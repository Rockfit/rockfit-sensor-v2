#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tiles_diagnostics.py  –  Monitor ligero de lecturas de loadcells

• Escucha ÚNICAMENTE el tópico:
      devices/{tile}/sensor/loadcell/state
• Cada N segundos (por defecto 10) muestra:
      Nº mensajes      | Nº baldosas activas | pico msgs/s | CPU% | RAM%
• Guarda en logs/events.csv:
      timestamp ISO-8601 (UTC),  tile,  valor entero
• Reconexión automática al broker (--wait activado por defecto).

Instalación rápida:
    pip install paho-mqtt psutil        # psutil solo para CPU/RAM

Ejemplo:
    python tiles_diagnostics.py --broker 192.168.8.163 \
                                --tiles tile1 tile2 tile3 tile4 tile5 tile6
"""
from __future__ import annotations

import argparse, csv, sys, time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

# psutil es opcional: solo se usa para leer CPU/RAM.
try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    HAVE_PSUTIL = False

# ───────────────────────── Argumentos CLI ──────────────────────────
parser = argparse.ArgumentParser(description="Monitor ligero de loadcells")
parser.add_argument("--broker",   default="localhost")
parser.add_argument("--port",     type=int, default=1883)
parser.add_argument("--tiles",    nargs="*",
                    default=[f"tile{i}" for i in range(1, 19)],
                    help="Lista de baldosas a monitorizar (por defecto las 18)")
parser.add_argument("--interval", type=int, default=10,
                    help="Segundos entre resúmenes")
parser.add_argument("--wait",     action="store_true", default=True,
                    help="Reintentar hasta que el broker esté disponible")
args = parser.parse_args()

BROKER, PORT = args.broker, args.port
TILES        = set(args.tiles)
INTERVAL     = args.interval

# ─────────────────────── CSV de eventos ────────────────────────────
OUTDIR = Path("logs"); OUTDIR.mkdir(exist_ok=True)
EVENTS_CSV = OUTDIR / "events.csv"
if not EVENTS_CSV.exists():
    with EVENTS_CSV.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["ts_iso", "tile", "value"])

# Buffers in-memory para métricas
timestamps: deque[float] = deque(maxlen=5000)       # times de los últimos 5k eventos
counts: defaultdict[str, int] = defaultdict(int)    # total recibido por tile

# ─────────────────────── Callbacks MQTT ────────────────────────────
def on_connect(client, *_):
    for t in TILES:
        client.subscribe(f"devices/{t}/sensor/loadcell/state", qos=1)
    print(f"[*] Conectado a {BROKER}:{PORT} – escuchando {len(TILES)} tiles")

def on_message(client, userdata, msg):
    ts   = time.time()
    tile = msg.topic.split("/")[1]
    try:
        value = int(msg.payload)
    except ValueError:
        return                       # ignora payloads no numéricos
    timestamps.append(ts)
    counts[tile] += 1

    with EVENTS_CSV.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.now(timezone.utc).isoformat(),
            tile,
            value
        ])

# ───────────────────────── Métricas en pantalla ────────────────────
def print_metrics():
    now = time.time(); start = now - INTERVAL
    msgs  = sum(1 for t in timestamps if t >= start)
    peak  = max((sum(1 for t in timestamps if int(t) == sec)
                 for sec in range(int(start), int(now)+1)), default=0)
    active = sum(1 for c in counts.values() if c)
    cpu = psutil.cpu_percent() if HAVE_PSUTIL else 0.0
    ram = psutil.virtual_memory().percent if HAVE_PSUTIL else 0.0

    print(f"{datetime.now(timezone.utc).isoformat()}  "
          f"{msgs:4d} msgs/{INTERVAL}s | tiles={active:2d} "
          f"| pico={peak}/s | CPU={cpu:4.1f}% RAM={ram:4.1f}%")

# ───────────────────────── Cliente MQTT ────────────────────────────
client = mqtt.Client()               # Compatible con Paho 1.x y 2.x
client.on_connect = on_connect
client.on_message = on_message

# ─────────────────────── Conexión con reintento ────────────────────
while True:
    try:
        client.connect(BROKER, PORT, keepalive=60)
        break
    except ConnectionRefusedError:
        if not args.wait:
            sys.exit("Broker inaccesible: arranca tu plataforma o usa --wait")
        print("Broker no disponible, reintentando en 2 s…")
        time.sleep(2)

client.loop_start()
next_tick = time.time() + INTERVAL
try:
    while True:
        time.sleep(0.2)
        if time.time() >= next_tick:
            print_metrics()
            next_tick += INTERVAL
except KeyboardInterrupt:
    print("\n[Monitor detenido por el usuario]")
finally:
    client.loop_stop()
    client.disconnect()
