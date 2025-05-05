import paho.mqtt.client as mqtt
import json
import time
import logging
import datetime
import threading
import uuid

import config

# ======================
# Estados del circuito
# ======================
STATE_WAITING     = "waiting"
STATE_READY       = "ready"
STATE_IN_PROGRESS = "in_progress"
STATE_COMPLETED   = "completed"
STATE_TIMEOUT     = "timeout"
STATE_DISABLED    = "disabled"

# ======================
# Ciclo de colores para color_mode = variable
# ======================
COLOR_CYCLE = [
    {"r": 0, "g": 255, "b": 0},
    {"r": 0, "g": 0, "b": 255},
    {"r": 255, "g": 0, "b": 0},
    {"r": 255, "g": 255, "b": 0}
]

# ======================
# Parámetro para ignorar eventos repetidos en menos de X segundos (global)
# ======================
DUPLICATE_EVENT_WINDOW = 0.10

# ======================
# Marca de tiempo global por tipo de evento (para filtrar "golpes fantasmas")
# ======================
last_global_ts_for_event_type = {
    "tap": 0.0,
    "double_tap": 0.0
}

# ======================
# Listas globales
# ======================
circuits = []
completed_circuits = []
mqtt_client = None
mqtt_client_ready = False
desired_active_ids = set()


class CircuitBase:
    def __init__(self, circuit_config, client):
        self.client = client
        self.config = circuit_config
        self.id = circuit_config["id"]
        self.name = circuit_config.get("name", self.id)
        self.description = circuit_config.get("description", "")

        # Primero definir steps y sequence
        self.steps = sorted(circuit_config.get("steps", []), key=lambda x: x["order"])
        self.sequence = [step["device"] for step in self.steps]

        # Luego asignar control_device (por defecto, el device del primer paso)
        self.control_device = circuit_config.get("control_device", self.steps[0]["device"] if self.steps else None)

        self.color_initial = circuit_config.get("color_initial", {"r": 0, "g": 255, "b": 0})
        self.color_mode = circuit_config.get("color_mode", "variable")
        self.max_time = circuit_config.get("max_time", 0)
        self.completion_effect = circuit_config.get("completion_effect", "celebration")
        self.order_mode = circuit_config.get("order_mode", "strict")
        self.state_reposo = circuit_config.get("state_reposo", "only_active")
        self.surpassed_light = circuit_config.get("surpassed_light", 0)
        self.default_wait_brightness_strict = circuit_config.get("default_wait_brightness_strict", 50)
        self.default_wait_brightness_flexible = circuit_config.get("default_wait_brightness_flexible", 60)

        self.state = STATE_WAITING
        self.current_index = 0
        self.start_time = None
        self.timestamps = []
        self.user_color = self.color_initial.copy()

        self.topic_map = {}
        for device in set(self.sequence):
            dev_cfg = config.DEVICES_CONFIG.get(device, {})
            tap_topic = dev_cfg.get("tap_topic")
            double_tap_topic = dev_cfg.get("double_tap_topic")
            if tap_topic:
                self.topic_map[tap_topic] = (device, "tap")
            if double_tap_topic:
                self.topic_map[double_tap_topic] = (device, "double_tap")

        self.instance_id = str(uuid.uuid4())[:8]
        self.assigned_users = []
        self.total_time = 0

    def log_event(self, event, device):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.timestamps.append((event, device, ts))
        logging.info(f"[{self.name}] Evento '{event}' en {device} a las {ts}")

    def publish_command(self, device, cmd):
        dev_cfg = config.DEVICES_CONFIG.get(device, {})
        light_topic = dev_cfg.get("light_command_topic")
        if light_topic:
            logging.debug(f"[{self.name}] (debug) cmd to {light_topic}: {cmd}")
            self.client.publish(light_topic, json.dumps(cmd))
        else:
            logging.warning(f"[{self.name}] No se encontró light_command_topic para {device}.")

    def update_led(self, device, brightness):
        cmd = config.get_led_on_command(color=self.get_current_color(), brightness=brightness)
        cmd["effect"] = "none"
        self.publish_command(device, cmd)

    def update_led_effect(self, device, effect_name):
        cmd = config.get_led_effect_command(effect_name)
        if effect_name == "Fast Pulse":
            cmd["color"] = self.get_current_color()
            cmd["brightness"] = config.DEFAULT_BRIGHTNESS
        self.publish_command(device, cmd)

    def turn_off_led(self, device):
        cmd = config.get_led_off_command()
        self.publish_command(device, cmd)

    def get_current_color(self):
        if self.color_mode == "fixed":
            return self.color_initial
        return self.user_color

    def change_color(self):
        """Si el modo es 'variable', rota por COLOR_CYCLE."""
        if self.color_mode == "variable":
            try:
                idx = COLOR_CYCLE.index(self.user_color)
                self.user_color = COLOR_CYCLE[(idx + 1) % len(COLOR_CYCLE)]
            except ValueError:
                self.user_color = COLOR_CYCLE[0]
            logging.info(f"[{self.name}] COLOR -> {self.user_color}")
            if self.state == STATE_WAITING:
                self.update_all_leds()
            elif self.state == STATE_IN_PROGRESS:
                self.update_led(self.control_device, config.DEFAULT_BRIGHTNESS)

    def _get_default_wait_brightness(self):
        return int(self.default_wait_brightness_strict / 100 * config.DEFAULT_BRIGHTNESS)

    def get_wait_brightness(self):
        if self.state == STATE_IN_PROGRESS and self.surpassed_light:
            return int(self.surpassed_light / 100 * config.DEFAULT_BRIGHTNESS)
        return self._get_default_wait_brightness()

    def update_all_leds(self):
        if self.state == STATE_WAITING:
            # Modo "reposo"
            if self.state_reposo == "all_active":
                for dev in self.sequence:
                    if dev == self.control_device:
                        self.update_led_effect(dev, "Fast Pulse")
                    else:
                        self.update_led(dev, self.get_wait_brightness())
            else:  # "only_active"
                for dev in self.sequence:
                    if dev == self.control_device:
                        self.update_led_effect(dev, "Fast Pulse")
                    else:
                        self.turn_off_led(dev)
        else:
            # En ejecución
            for idx, dev in enumerate(self.sequence):
                if idx < self.current_index:
                    if self.surpassed_light:
                        brillo = int(self.surpassed_light / 100 * config.DEFAULT_BRIGHTNESS)
                    else:
                        brillo = self.get_wait_brightness()
                    self.update_led(dev, brillo)
                elif idx > self.current_index:
                    self.update_led(dev, self.get_wait_brightness())
            # Quien está en current_index se enciende fuerte
            if self.state == STATE_IN_PROGRESS and self.current_index < len(self.sequence):
                dev = self.sequence[self.current_index]
                evt = self.steps[self.current_index]["event"]
                if evt == "double_tap":
                    self.update_led_effect(dev, "Fast Pulse")
                else:
                    self.update_led(dev, config.DEFAULT_BRIGHTNESS)

    def reset_and_activate_ready(self):
        """Devuelve el circuito a waiting, reiluminándolo como tal."""
        self.state = STATE_WAITING
        self.current_index = 0
        self.timestamps.clear()
        self.start_time = None
        for d in self.sequence:
            self.turn_off_led(d)
        self.user_color = self.color_initial.copy()
        if self.steps:
            next_evt = self.steps[0]["event"]
        else:
            next_evt = "tap"
        self.update_led_effect(self.control_device, "Fast Pulse")
        logging.info(f"[{self.name}] RESET -> OFF en {len(self.sequence)} disp, "
                     f"FastPulse en '{self.control_device}', color {self.get_current_color()}, "
                     f"esperando '{next_evt}'")

    def start_circuit(self):
        """Pasa a in_progress, enciende leds y avanza current_index a 1 (primer step consumido)."""
        self.turn_off_led(self.control_device)
        self.start_time = time.time()
        self.state = STATE_IN_PROGRESS
        self.current_index = 1
        self.update_all_leds()

        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        nxt_dev = self.sequence[self.current_index] if self.current_index < len(self.sequence) else None
        nxt_evt = self.steps[self.current_index]["event"] if self.current_index < len(self.steps) else None
        logging.info(
            f"[{self.name}] START @ {ts} -> ctrl '{self.control_device}' OFF, "
            f"paso {self.current_index}/{len(self.sequence)} con '{nxt_dev}' ({nxt_evt}), t=0s"
        )

    def advance_step(self):
        """Llamado cuando se detecta el evento correcto en el step actual."""
        dev_act = self.sequence[self.current_index]
        old_index = self.current_index
        self.log_event("advance", dev_act)

        self.current_index += 1
        self.update_all_leds()

        if self.current_index >= len(self.sequence):
            self.complete_circuit()
        else:
            nxt_dev = self.sequence[self.current_index]
            nxt_evt = self.steps[self.current_index]["event"]
            elapsed = time.time() - self.start_time if self.start_time else 0
            logging.info(
                f"[{self.name}] STEP -> {old_index}->{self.current_index}/{len(self.sequence)} "
                f"({dev_act} ok). Próximo: '{nxt_dev}' ({nxt_evt}). Tiempo: {elapsed:.2f}s"
            )

    def skip_step(self):
        """
        Permite saltar el paso actual, comportándose igual que si el dispositivo
        hubiera activado el paso correctamente.
        Ahora se permite también en estado waiting (inicial).
        """
        # Si el circuito está en waiting y aún no ha iniciado (current_index == 0),
        # se simula el inicio del circuito:
        if self.state == STATE_WAITING and self.current_index == 0:
            self.log_event("skip_step", self.control_device)
            self.start_circuit()
            return

        if self.state not in [STATE_WAITING, STATE_IN_PROGRESS] or self.current_index >= len(self.sequence):
            logging.info(f"[{self.name}] skip_step llamado en un estado no válido (state={self.state}, current_index={self.current_index}).")
            return

        dev_act = self.sequence[self.current_index]
        self.log_event("skip_step", dev_act)
        self.current_index += 1
        self.update_all_leds()

        if self.current_index >= len(self.sequence):
            self.complete_circuit()
        else:
            nxt_dev = self.sequence[self.current_index]
            nxt_evt = self.steps[self.current_index]["event"]
            elapsed = time.time() - self.start_time if self.start_time else 0
            logging.info(
                f"[{self.name}] STEP (skip) -> {self.current_index}/{len(self.sequence)} "
                f"(saltado: {dev_act}). Próximo: '{nxt_dev}' ({nxt_evt}). Tiempo: {elapsed:.2f}s"
            )

    def complete_circuit(self):
        """Marca el circuito como completado y lanza la celebración si corresponde."""
        self.state = STATE_COMPLETED
        elapsed = time.time() - self.start_time if self.start_time else 0
        self.total_time = elapsed

        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        snapshot = {
            "instance_id": self.instance_id,
            "name": self.name,
            "assigned_users": self.assigned_users[:],
            "total_time": elapsed,
            "timestamps": self.timestamps[:],
            "steps": self.steps,
            "final_color": self.get_current_color()
        }
        completed_circuits.append(snapshot)

        logging.info(f"[{self.name}] DONE @ {ts} -> {elapsed:.2f}s. Ejecutando celebración.")

        def finalize():
            self.remove_from_circuits()
            create_new_instance_if_still_active(self.id)

        if self.completion_effect == "celebration":
            threading.Thread(target=self.run_celebration, daemon=True).start()
            threading.Timer(3.0, finalize).start()
        else:
            finalize()

    def remove_from_circuits(self):
        global circuits
        try:
            circuits.remove(self)
            logging.info(f"[{self.name}] Eliminado de circuits tras completarse.")
        except ValueError:
            logging.warning(f"[{self.name}] No se encontró en circuits al intentar eliminarlo.")

    def timeout_check(self):
        """Si max_time>0, verifica si excedió el tiempo."""
        if self.max_time > 0 and self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed >= self.max_time:
                self.state = STATE_TIMEOUT
                logging.info(f"[{self.name}] TIMEOUT tras {elapsed:.2f} s.")

                def finalize_timeout():
                    self.remove_from_circuits()
                    create_new_instance_if_still_active(self.id)

                threading.Thread(target=self.run_failure, daemon=True).start()
                threading.Timer(3.0, finalize_timeout).start()

    def handle_event(self, client_topic, msg_payload):
        """Recibe un evento ya filtrado por topic_map."""
        if client_topic not in self.topic_map:
            return False

        device, event_type = self.topic_map[client_topic]
        self.log_event(event_type, device)

        if self.state in [STATE_COMPLETED, STATE_TIMEOUT, STATE_DISABLED]:
            return False

        if device == self.control_device:
            if self.state in [STATE_WAITING, STATE_READY]:
                if not self.steps:
                    return False
                exp_evt = self.steps[0]["event"]
                if exp_evt == "double_tap":
                    if event_type == "tap":
                        if self.color_mode == "variable":
                            self.change_color()
                        else:
                            logging.info(f"[{self.name}] Tap en ctrl ignorado; se requiere double_tap.")
                        return True
                    elif event_type == "double_tap":
                        self.start_circuit()
                        return True
                else:
                    if event_type == "tap":
                        self.start_circuit()
                        return True
                    elif event_type == "double_tap":
                        self.reset_and_activate_ready()
                        return True
            elif self.state == STATE_IN_PROGRESS:
                if self.current_index < len(self.sequence) and self.sequence[self.current_index] == self.control_device:
                    exp_evt = self.steps[self.current_index]["event"]
                    if event_type == exp_evt:
                        self.advance_step()
                        return True
                    else:
                        logging.info(f"[{self.name}] Evento incorrecto en ctrl; se esperaba {exp_evt}.")
                        return False
            return False
        else:
            if self.state == STATE_IN_PROGRESS and self.current_index < len(self.sequence):
                if device == self.sequence[self.current_index]:
                    exp_evt = self.steps[self.current_index]["event"]
                    if event_type == exp_evt:
                        self.advance_step()
                        return True
                    else:
                        logging.info(f"[{self.name}] Evento incorrecto en {device}: se esperaba {exp_evt}.")
                        return False
            return False

    def run_celebration(self):
        start_time = time.time()
        while time.time() - start_time < 3.0:
            for color in config.CELEBRATION_COLORS:
                cmd = {
                    "state": "ON",
                    "brightness": config.DEFAULT_BRIGHTNESS,
                    "color": color,
                    "effect": "none"
                }
                for dev in self.sequence:
                    self.publish_command(dev, cmd)
                time.sleep(config.CELEBRATION_INTERVAL)
                if time.time() - start_time >= 3.0:
                    break

    def run_failure(self):
        start_time = time.time()
        while time.time() - start_time < 3.0:
            cmd_on = {
                "state": "ON",
                "brightness": config.DEFAULT_BRIGHTNESS,
                "color": config.COLOR_RED,
                "effect": "none"
            }
            for dev in self.sequence:
                self.publish_command(dev, cmd_on)
            time.sleep(0.5)
            cmd_off = config.get_led_off_command()
            for dev in self.sequence:
                self.publish_command(dev, cmd_off)
            time.sleep(0.5)

    def deactivate(self):
        """Desactiva manualmente este circuito (apaga LEDs, marca state=DISABLED)."""
        self.state = STATE_DISABLED
        for dev in self.sequence:
            self.turn_off_led(dev)
        logging.info(f"[{self.name}] Desactivado manualmente (state=DISABLED).")

    def restart(self):
        """Reinicia manualmente el circuito, volviendo a waiting."""
        self.reset_and_activate_ready()
        logging.info(f"[{self.name}] Reiniciado manualmente (state=WAITING).")


class StrictCircuit(CircuitBase):
    def _get_default_wait_brightness(self):
        return int(self.default_wait_brightness_strict / 100 * config.DEFAULT_BRIGHTNESS)


class FlexibleCircuit(CircuitBase):
    def _get_default_wait_brightness(self):
        return int(self.default_wait_brightness_flexible / 100 * config.DEFAULT_BRIGHTNESS)

    def get_wait_brightness(self):
        if self.state == STATE_IN_PROGRESS and self.surpassed_light == 0:
            return 0
        return super().get_wait_brightness()


class CompetitionCircuit(CircuitBase):
    def _get_default_wait_brightness(self):
        return int(self.default_wait_brightness_strict / 100 * config.DEFAULT_BRIGHTNESS)

    def start_circuit(self):
        logging.info(f"[{self.name}] Modo competition no implementado aún.")
        raise NotImplementedError("La lógica para Competition aún no está desarrollada.")


def on_connect(client, userdata, flags, rc):
    logging.info(f"Conectado al broker {config.MQTT_BROKER}:{config.MQTT_PORT} con código {rc}")
    topics = set()
    for dev in config.DEVICES_CONFIG.values():
        for key in ["tap_topic", "double_tap_topic"]:
            t = dev.get(key)
            if t:
                topics.add(t)
    for t in topics:
        client.subscribe(t)
    logging.info(f"Suscrito a {len(topics)} tópicos: {', '.join(sorted(topics))}")


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="replace")
    logging.info(f"Mensaje recibido: {msg.topic} - {payload}")

    event_type = None
    if "/tap" in msg.topic:
        event_type = "tap"
    elif "/double_tap" in msg.topic:
        event_type = "double_tap"

    if event_type in ("tap", "double_tap"):
        now_ts = time.time()
        global last_global_ts_for_event_type
        last_ts = last_global_ts_for_event_type[event_type]
        if (now_ts - last_ts) < DUPLICATE_EVENT_WINDOW:
            ignored_time = datetime.datetime.fromtimestamp(now_ts).strftime("%H:%M:%S.%f")[:-3]
            logging.info(f"Ignorando globalmente '{event_type}' repetido en menos de {DUPLICATE_EVENT_WINDOW}s. (Timestamp: {ignored_time})")
            return
        last_global_ts_for_event_type[event_type] = now_ts

    for c in circuits:
        c.handle_event(msg.topic, payload)
    for c in circuits:
        if c.state == STATE_IN_PROGRESS:
            c.timeout_check()


def init_mqtt_client():
    global mqtt_client, mqtt_client_ready
    if mqtt_client is None:
        mqtt_client = mqtt.Client()
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
        mqtt_client.loop_start()
        mqtt_client_ready = True
    else:
        logging.info("Cliente MQTT ya existente; no se crea uno nuevo.")


def create_new_instance_if_still_active(circuit_id):
    """Si un circuito finaliza pero ese ID sigue siendo deseado, se crea una nueva instancia en WAITING."""
    if circuit_id not in desired_active_ids:
        return
    for inst in circuits:
        if inst.id == circuit_id and inst.state in [STATE_WAITING, STATE_IN_PROGRESS]:
            return
    from config import CIRCUITS
    conf = next((c for c in CIRCUITS if c["id"] == circuit_id), None)
    if not conf:
        return
    order_mode = conf.get("order_mode", "strict")
    if order_mode == "strict":
        inst = StrictCircuit(conf, mqtt_client)
    elif order_mode == "flexible":
        inst = FlexibleCircuit(conf, mqtt_client)
    elif order_mode == "competition":
        inst = CompetitionCircuit(conf, mqtt_client)
    else:
        inst = StrictCircuit(conf, mqtt_client)
    circuits.append(inst)
    logging.info(f"[{inst.name}] Se crea nueva instancia WAITING (ID={inst.instance_id}) por reactivación inmediata tras completarse.")
    inst.user_color = inst.color_initial.copy()
    inst.update_all_leds()


def main(active_circuits_param=None):
    global circuits, desired_active_ids
    init_mqtt_client()

    if active_circuits_param is None:
        active_circuits_param = []

    desired_active_ids = set(active_circuits_param)

    new_list = []
    for c in circuits:
        if c.id in desired_active_ids and c.state in [STATE_WAITING, STATE_IN_PROGRESS]:
            new_list.append(c)
    circuits[:] = new_list

    from config import CIRCUITS
    waiting_ids = {c.id for c in circuits if c.state in [STATE_WAITING, STATE_IN_PROGRESS]}
    for conf in CIRCUITS:
        cid = conf["id"]
        if cid in desired_active_ids and cid not in waiting_ids:
            order_mode = conf.get("order_mode", "strict")
            if order_mode == "strict":
                cinst = StrictCircuit(conf, mqtt_client)
            elif order_mode == "flexible":
                cinst = FlexibleCircuit(conf, mqtt_client)
            elif order_mode == "competition":
                cinst = CompetitionCircuit(conf, mqtt_client)
            else:
                cinst = StrictCircuit(conf, mqtt_client)
            circuits.append(cinst)
            e = cinst.steps[0]["event"] if cinst.steps else "tap"
            logging.info(f"[{cinst.name}] RESET -> OFF en {len(cinst.sequence)} disp, FastPulse en '{cinst.control_device}', "
                         f"color {cinst.get_current_color()}, esperando '{e}'")

    logging.info("Resumen de circuitos activos:")
    for c in circuits:
        start_evt = c.steps[0]["event"] if c.steps else "tap?"
        logging.info(f" - {c.name} (ID={c.instance_id}): ctrl={c.control_device}, color={c.get_current_color()}, "
                     f"modo={c.order_mode}, evento_inicio={start_evt}")

    logging.info("Sistema listo para recibir eventos de dispositivos.")
    for c in circuits:
        c.user_color = c.color_initial.copy()
        c.update_all_leds()


if __name__ == '__main__':
    main(["circuito_2"])
    while True:
        time.sleep(0.5)
