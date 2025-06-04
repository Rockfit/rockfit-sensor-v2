#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calibración rápida de tile4‑tile6 con lectura a la máxima velocidad posible.
– HX711 debe estar cableado a 80 Hz  (pin RATE a VCC).
– Filtrado mínimo: tara en 5 muestras, sin umbral de cambio excepto 1 count.
– LED azul proporcional, instante a instante.
"""

import json
import logging
import time
from collections import defaultdict

import paho.mqtt.client as mqtt

# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #
BROKER = "192.168.8.163"
PORT   = 1883
TILES  = ["tile4", "tile5", "tile6"]

# Tara en 5 muestras para reaccionar antes
N_TARE_SAMPLES = 5

# Conversión counts → brillo (ajusta a tu rango)
COUNTS_FULL_SCALE = 4000        # counts ≈ brillo 255
CHANGE_THRESHOLD  = 1           # 1 count: máximo detalle

# --------------------------------------------------------------------------- #
# Topics
# --------------------------------------------------------------------------- #
LOADCELL_T = "devices/{tile}/sensor/loadcell/state"
LED_CMD_T  = "devices/{tile}/light/leds/command"

def blue(brightness: int) -> dict:
    return {"state": "OFF"} if brightness <= 0 else {
        "state": "ON",
        "brightness": brightness,
        "color": {"r": 0, "g": 0, "b": 255},
    }

# --------------------------------------------------------------------------- #
# Estado
# --------------------------------------------------------------------------- #
tare         = {t: None for t in TILES}
samples_left = {t: N_TARE_SAMPLES for t in TILES}
last_delta   = defaultdict(lambda: None)

# --------------------------------------------------------------------------- #
# Logger
# --------------------------------------------------------------------------- #
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("calib_fast")

# --------------------------------------------------------------------------- #
# MQTT callbacks
# --------------------------------------------------------------------------- #
def on_connect(client, *_):
    log.info(f"Conectado a {BROKER}:{PORT}")
    for tile in TILES:
        client.subscribe(LOADCELL_T.format(tile=tile), qos=0)  # QoS 0 = mínima latencia
    log.info("Suscrito a loadcells de tile4‑6")

def on_message(client, userdata, msg):
    tile = msg.topic.split("/")[1]
    try:
        raw = int(msg.payload.decode())
    except ValueError:
        return

    # Tara exprés
    if samples_left[tile] > 0:
        tare[tile] = (tare[tile] or 0) + raw
        samples_left[tile] -= 1
        if samples_left[tile] == 0:
            tare[tile] //= N_TARE_SAMPLES
            log.info(f"{tile}: tara={tare[tile]}")
        return

    delta = raw - tare[tile]

    # LED & log en tiempo real
    if last_delta[tile] is None or abs(delta - last_delta[tile]) >= CHANGE_THRESHOLD:
        last_delta[tile] = delta
        brightness = 0 if delta <= 0 else min(int(delta * 255 / COUNTS_FULL_SCALE), 255)
        client.publish(LED_CMD_T.format(tile=tile), json.dumps(blue(brightness)), qos=0)
        log.info(f"{tile:5s} raw={raw:>8d}  Δ={delta:>8d}  br={brightness:3d}")

# --------------------------------------------------------------------------- #
def main():
    client = mqtt.Client()  # callback_api_version=5 si tu Paho es 2.x
    client.on_connect = on_connect
    client.on_message = on_message
    client.enable_logger(log)

    client.connect(BROKER, PORT, keepalive=30)  # keepalive bajo: detecta cortes antes
    client.loop_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
