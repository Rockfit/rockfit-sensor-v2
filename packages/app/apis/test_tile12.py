#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Control de 18 baldosas (ESP32 + HX711) vía MQTT
Arranque:
  1) RGB secuencial
  2) 5 s en rojo tenue, salvo {1,3,8,14,18} en verde brillante
  3) Blanco muy tenue durante 20 s
  4) Apagado
La detección de carga permanece igual.
"""

import json
import logging
import threading
import time
from collections import defaultdict

import paho.mqtt.client as mqtt

# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #
BROKER = "192.168.8.163"
PORT   = 1883
TILES  = [f"tile{i}" for i in range(1, 19)]     # tile1 … tile18

THRESHOLDS = defaultdict(lambda: 500)
STEP_DELAY = 0.20

SPECIAL_GREEN = {"tile1", "tile3", "tile8", "tile14", "tile18"}

# --------------------------------------------------------------------------- #
# Paleta
# --------------------------------------------------------------------------- #
RED       = {"state": "ON", "brightness": 255, "color": {"r": 255, "g":   0, "b":   0}}
YELLOW    = {"state": "ON", "brightness": 255, "color": {"r": 255, "g": 255, "b":   0}}
GREEN     = {"state": "ON", "brightness": 255, "color": {"r":   0, "g": 255, "b":   0}}
OFF       = {"state": "OFF"}

RED_DIM   = {"state": "ON", "brightness": 128, "color": {"r": 255, "g": 0, "b": 0}}
WHITE_DIM = {"state": "ON", "brightness": 32,  "color": {"r": 255, "g": 255, "b": 255}}

# --------------------------------------------------------------------------- #
# Estado
# --------------------------------------------------------------------------- #
state        = {t: "idle" for t in TILES}
tare         = {t: None   for t in TILES}
last_value   = {t: None   for t in TILES}
samples_left = {t: 10     for t in TILES}
loaded_tiles = set()

# --------------------------------------------------------------------------- #
# Logger
# --------------------------------------------------------------------------- #
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("tiles")

# --------------------------------------------------------------------------- #
# Utilidades MQTT
# --------------------------------------------------------------------------- #
def mqtt_pub(client: mqtt.Client, tile: str, payload: dict):
    client.publish(f"devices/{tile}/light/leds/command",
                   json.dumps(payload), qos=1)

def sequential_show(client: mqtt.Client, payload: dict, delay: float):
    for tile in TILES:
        mqtt_pub(client, tile, payload)
        time.sleep(delay)

def all_show(client: mqtt.Client, payload: dict):
    for tile in TILES:
        mqtt_pub(client, tile, payload)

def red_green_mix(client: mqtt.Client):
    """Todas rojo tenue salvo las SPECIAL_GREEN en verde brillante."""
    for tile in TILES:
        mqtt_pub(client, tile, GREEN if tile in SPECIAL_GREEN else RED_DIM)

# --------------------------------------------------------------------------- #
# Callbacks MQTT
# --------------------------------------------------------------------------- #
def on_connect(client, userdata, flags, rc, *_):
    if rc:
        log.error(f"Error de conexión (rc={rc})"); return
    log.info(f"Conectado a {BROKER}:{PORT}")

    for tile in TILES:
        client.subscribe(f"devices/{tile}/sensor/loadcell/state", qos=1)
    log.info("Suscrito a todos los loadcells")

    threading.Thread(target=startup_animation,
                     args=(client,), daemon=True).start()

def on_message(client, userdata, msg):
    tile = msg.topic.split("/")[1]
    try:
        raw = int(msg.payload.decode())
    except ValueError:
        return

    # Tara automática
    if samples_left[tile] > 0:
        tare[tile] = (tare[tile] or 0) + raw
        samples_left[tile] -= 1
        if samples_left[tile] == 0:
            tare[tile] //= 10
            state[tile] = "armed"
            log.info(f"{tile}  Tara={tare[tile]}")
        return

    delta = raw - tare[tile]

    if abs(delta) >= THRESHOLDS[tile] and state[tile] == "armed":
        loaded_tiles.add(tile)
        state[tile] = "loaded"
        mqtt_pub(client, tile, GREEN)
        log.info(f"{tile}  **LOAD**  delta={delta}")
        if len(loaded_tiles) == len(TILES):
            log.info("Todas las baldosas cargadas → parpadeo final")
            blink_all(client, GREEN, 0.25, 3)
            all_show(client, OFF)
            threading.Timer(0.5, client.disconnect).start()

# --------------------------------------------------------------------------- #
# Animaciones
# --------------------------------------------------------------------------- #
def startup_animation(client: mqtt.Client):
    """RGB secuencial → 5 s rojo/verde → 20 s blanco tenue → apagado"""
    log.info(">> Animación de arranque")

    # Fase 1 – RGB secuencial
    for payload in (RED, YELLOW, GREEN):
        sequential_show(client, payload, STEP_DELAY)

    # Fase 2 – rojo tenue + verdes especiales (5 s)
    red_green_mix(client)
    time.sleep(5)

    # Fase 3 – blanco tenue (20 s)
    all_show(client, WHITE_DIM)
    time.sleep(20)

    # Fase 4 – apagado
    all_show(client, OFF)
    log.info(">> Animación completada; sistema ARMADO")

def blink_all(client: mqtt.Client, payload_on: dict, delay: float, times: int):
    for _ in range(times):
        all_show(client, payload_on); time.sleep(delay)
        all_show(client, OFF);       time.sleep(delay)

# --------------------------------------------------------------------------- #
def main():
    client = mqtt.Client()           # añade callback_api_version=5 si tu Paho 2.x lo requiere
    client.on_connect = on_connect
    client.on_message = on_message
    client.enable_logger(log)

    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
