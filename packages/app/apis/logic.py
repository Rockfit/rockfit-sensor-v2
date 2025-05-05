"""
logic.py
---------
Este script implementa la lógica en vivo para tres circuitos (cada uno basado en un game_sequence definido en config_params).
Utiliza los métodos de config_base para generar los comandos de LED, incluidos los efectos internos.
Características:
  - Cada circuito se crea a partir de un número (1, 2 o 3) y tiene asignado un color de usuario.
  - Se obtiene la secuencia de dispositivos mediante get_game_sequence(game_number) de config_params.
  - Mientras el circuito no esté iniciado (estado WAITING o READY), el botón inicial muestra el efecto "Fast Pulse".
    Si ya está en READY, un TAP adicional en el botón inicial reasigna el color aplicando la secuencia:
      OFF → encendido sólido con el nuevo color → efecto "Fast Pulse".
  - Con un DOUBLE TAP en el botón inicial se inicia (o se reinicia) el circuito; al iniciarse, el botón inicial se apaga.
  - Durante el avance, el dispositivo esperado se enciende al 100% y los demás al 20%.
  - Tras completar la secuencia, se reinicia automáticamente y el circuito queda en estado READY, mostrando fast pulse en el botón inicial.
  
Los mensajes MQTT disparan la lógica de cada circuito.
"""

import paho.mqtt.client as mqtt
import json
import time
import logging
import datetime
import threading

import config_base
import config_params

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

STATE_WAITING     = "waiting"
STATE_READY       = "ready"
STATE_IN_PROGRESS = "in_progress"
STATE_COMPLETED   = "completed"

class Circuit:
    def __init__(self, name, game_number, user_color, client):
        self.name = name
        self.client = client
        self.sequence = config_params.get_game_sequence(game_number)
        self.user_color = user_color
        self.state = STATE_WAITING
        self.current_index = 0
        self.timestamps = []
        self.topic_map = {}
        for device in set(self.sequence):
            dev_cfg = config_params.DEVICES_CONFIG.get(device, {})
            tap_topic = dev_cfg.get("tap_topic")
            double_tap_topic = dev_cfg.get("double_tap_topic")
            if tap_topic:
                self.topic_map[tap_topic] = (device, "tap")
            if double_tap_topic:
                self.topic_map[double_tap_topic] = (device, "double_tap")
    
    def log_event(self, event, device):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.timestamps.append((event, device, ts))
        logging.info(f"[{self.name}] Evento '{event}' en {device} a las {ts}")
    
    def publish_command(self, device, cmd):
        dev_cfg = config_params.DEVICES_CONFIG.get(device, {})
        light_topic = dev_cfg.get("light_command_topic")
        if light_topic:
            self.client.publish(light_topic, json.dumps(cmd))
            logging.info(f"[{self.name}] Publicado en {light_topic}: {cmd}")
        else:
            logging.warning(f"[{self.name}] No se encontró light_command_topic para {device}.")
    
    def update_led(self, device, brightness):
        cmd = config_base.get_led_on_command(color=self.user_color, brightness=brightness)
        self.publish_command(device, cmd)
    
    def update_led_effect(self, device, effect_name):
        cmd = config_base.get_led_effect_command(effect_name)
        self.publish_command(device, cmd)
    
    def turn_off_led(self, device):
        cmd = config_base.get_led_off_command()
        self.publish_command(device, cmd)
    
    def update_all_leds(self):
        for idx, device in enumerate(self.sequence):
            if self.state == STATE_IN_PROGRESS:
                if idx == 0:
                    brillo = 0
                elif idx == self.current_index:
                    brillo = 100
                else:
                    brillo = 20
            else:
                brillo = 20
            self.update_led(device, brillo)
    
    def reset(self):
        logging.info(f"[{self.name}] --- RESET del circuito ---")
        self.state = STATE_WAITING
        self.current_index = 0
        self.timestamps = []
        for device in self.sequence:
            self.turn_off_led(device)
        logging.info(f"[{self.name}] Circuito reiniciado.\n")
    
    def reset_and_activate_ready(self):
        self.reset()
        self.state = STATE_READY
        self.update_led_effect(self.sequence[0], "Fast Pulse")
        logging.info(f"[{self.name}] Circuito listo, botón inicial en Fast Pulse.")
    
    def get_next_color(self, current):
        colors = [
            config_base.COLOR_RED,
            config_base.COLOR_BLUE,
            config_base.COLOR_GREEN,
            config_base.COLOR_YELLOW,
            config_base.COLOR_MAGENTA,
            config_base.COLOR_CYAN
        ]
        try:
            idx = colors.index(current)
            return colors[(idx + 1) % len(colors)]
        except ValueError:
            return colors[0]
    
    def tap(self, device):
        logging.info(f"[{self.name}] TAP en {device}")
        self.log_event("tap", device)
        if self.current_index == 0 and device == self.sequence[0]:
            if self.state in [STATE_WAITING, STATE_READY]:
                if self.state == STATE_WAITING:
                    self.state = STATE_READY
                    logging.info(f"[{self.name}] Usuario asignado (color {self.user_color}).")
                else:
                    self.user_color = self.get_next_color(self.user_color)
                    logging.info(f"[{self.name}] Usuario reasignado, nuevo color: {self.user_color}.")
                self.turn_off_led(device)
                self.update_led(device, 100)
                threading.Timer(0.01, lambda: self.update_led_effect(device, "Fast Pulse")).start()
                logging.info(f"[{self.name}] Espera DOUBLE TAP para iniciar.")
            else:
                logging.info(f"[{self.name}] TAP en {device} ignorado en estado {self.state}.")
        else:
            if self.state == STATE_IN_PROGRESS:
                expected_device = self.sequence[self.current_index]
                if device == expected_device:
                    self.log_event("advance", device)
                    self.current_index += 1
                    self.update_all_leds()
                    if self.current_index >= len(self.sequence):
                        self.state = STATE_COMPLETED
                        logging.info(f"[{self.name}] Secuencia COMPLETADA.")
                        threading.Timer(0.5, self.reset_and_activate_ready).start()
                else:
                    logging.info(f"[{self.name}] TAP en {device} pero no es el pulsador esperado ({expected_device}).")
            else:
                logging.info(f"[{self.name}] TAP en {device} ignorado en estado {self.state}.")
    
    def double_tap(self, device):
        logging.info(f"[{self.name}] DOUBLE TAP en {device}")
        self.log_event("double_tap", device)
        if device == self.sequence[0]:
            self.turn_off_led(device)
            if self.state in [STATE_WAITING, STATE_READY]:
                self.state = STATE_IN_PROGRESS
                self.current_index = 1
                logging.info(f"[{self.name}] Circuito INICIADO.")
                self.update_all_leds()
            elif self.state in [STATE_IN_PROGRESS, STATE_COMPLETED]:
                self.reset_and_activate_ready()
        else:
            logging.info(f"[{self.name}] DOUBLE TAP en {device} ignorado (solo el botón inicial controla el circuito).")
    
    def handle_event(self, topic, payload):
        if topic in self.topic_map:
            device, event_type = self.topic_map[topic]
            if event_type == "tap":
                self.tap(device)
            elif event_type == "double_tap":
                self.double_tap(device)
            return True
        return False

# Lista global de circuitos
circuits = []

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"Conectado al broker {config_params.MQTT_BROKER}:{config_params.MQTT_PORT}")
        topics = set()
        for circuit in circuits:
            topics.update(circuit.topic_map.keys())
        for topic in topics:
            client.subscribe(topic)
            logging.info(f"Suscrito a: {topic}")
    else:
        logging.error(f"Error al conectar, rc={rc}")

def on_message(client, userdata, msg):
    payload_str = msg.payload.decode("utf-8", errors="replace")
    logging.info(f"Mensaje recibido: {msg.topic} - {payload_str}")
    for circuit in circuits:
        if circuit.handle_event(msg.topic, payload_str):
            break

def main():
    global circuits
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    circuit1 = Circuit("Circuito 1", 1, config_base.COLOR_RED, client)
    circuit2 = Circuit("Circuito 2", 2, config_base.COLOR_BLUE, client)
    circuit3 = Circuit("Circuito 3", 3, config_base.COLOR_GREEN, client)
    circuits = [circuit1, circuit2, circuit3]
    
    client.connect(config_params.MQTT_BROKER, config_params.MQTT_PORT, 60)
    client.loop_start()
    time.sleep(1)
    
    logging.info("Sistema listo para recibir eventos de dispositivos.")
    
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        logging.info("Interrupción recibida. Finalizando...")
        client.disconnect()

if __name__ == "__main__":
    main()