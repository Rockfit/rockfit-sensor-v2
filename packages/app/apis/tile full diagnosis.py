#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse, json, os, time
from collections import defaultdict, deque
from datetime import datetime, timezone as tz
from statistics import mean
from pathlib import Path

# ─────────────── Carpeta de salida fija ───────────────
BASE_DIR = Path(r"C:\Users\javib\rockfit-sensor-v2\rockfit-sensor-v2-main\packages\app\apis")
BASE_DIR.mkdir(parents=True, exist_ok=True)

CSV_MQTT = BASE_DIR / "mqtt.csv"
CSV_PING = BASE_DIR / "ping.csv"
CSV_SYS  = BASE_DIR / "sys.csv"

for fp, hdr in ((CSV_MQTT, ["ts","tile","value"]),
                (CSV_PING, ["ts_cmd","ts_ack","lat_ms","tile"]),
                (CSV_SYS , ["ts","cpu","ram"])):
    if not fp.exists():
        fp.write_text(",".join(hdr)+"\n", encoding="utf-8")

# ─────────────── CLI ───────────────
P = argparse.ArgumentParser(description="Diagnóstico baldosas")
P.add_argument("--broker", default="localhost")
P.add_argument("--port",   type=int, default=1883)
P.add_argument("--tiles",  nargs="*", default=[f"tile{i}" for i in range(1,19)])
P.add_argument("--watch",  nargs="*", default=None)
P.add_argument("--interval", type=int, default=5)
P.add_argument("--ping-every", type=int, default=20)
P.add_argument("--duration", type=int, default=0)
args = P.parse_args()

BROKER, PORT   = args.broker, args.port
TILES          = list(dict.fromkeys(args.tiles))
DISPLAY_TILES  = list(dict.fromkeys(args.watch or TILES))
INTERVAL       = args.interval
PING_INT       = args.ping_every
STOP_AT        = time.time()+args.duration if args.duration>0 else None

# ─────────────── Buffers ───────────────
recent_ts       = deque(maxlen=20000)
per_tile_vals   = defaultdict(list)
latencies_ms    = defaultdict(list)
outstanding_ping= {}
cpu_hist, ram_hist = [], []

# ─────────────── MQTT ───────────────
import paho.mqtt.client as mqtt
def on_connect(c,*_):
    for t in TILES:
        c.subscribe(f"devices/{t}/sensor/loadcell/state",1)
        c.subscribe(f"devices/{t}/light/leds/state",1)
    print(f"Conectado a {BROKER}:{PORT} – {len(TILES)} tiles")
    print("Latencias mostradas:", ", ".join(DISPLAY_TILES))

def on_message(c,_,msg):
    now=time.time()
    parts=msg.topic.split("/")
    tile =parts[1]
    if parts[-2:] == ["loadcell","state"]:
        try: val=int(msg.payload)
        except ValueError: return
        recent_ts.append(now); per_tile_vals[tile].append(val)
        CSV_MQTT.open("a").write(
            f"{datetime.fromtimestamp(now,tz.utc).isoformat()},{tile},{val}\n")
    elif parts[-2:] == ["leds","state"] and tile in outstanding_ping:
        ts_cmd=outstanding_ping.pop(tile)
        lat=(now-ts_cmd)*1000
        latencies_ms[tile].append(lat)
        CSV_PING.open("a").write(
            f"{datetime.fromtimestamp(ts_cmd,tz.utc).isoformat()},"
            f"{datetime.fromtimestamp(now,tz.utc).isoformat()},"
            f"{lat:.1f},{tile}\n")

# ─────────────── Hilos auxiliares ───────────────
import threading, psutil
STOP=threading.Event()

def ping_loop(client:mqtt.Client):
    payload={"state":"ON","brightness":5,"color":{"r":255,"g":255,"b":255}}
    next_ping={t:time.time()+i for i,t in enumerate(TILES)}
    while not STOP.is_set():
        now=time.time()
        for t in TILES:
            if now>=next_ping[t]:
                client.publish(f"devices/{t}/light/leds/command",
                               json.dumps(payload),1)
                outstanding_ping[t]=now
                next_ping[t]=now+PING_INT
        time.sleep(0.2)

def sys_loop():
    while not STOP.is_set():
        cpu=psutil.cpu_percent(interval=None)
        ram=psutil.virtual_memory().percent
        CSV_SYS.open("a").write(
            f"{datetime.now(tz.utc).isoformat()},{cpu:.1f},{ram:.1f}\n")
        cpu_hist.append(cpu); ram_hist.append(ram)
        time.sleep(INTERVAL)

def console_loop():
    while not STOP.is_set():
        now=time.time()
        msgs=sum(1 for ts in recent_ts if ts>=now-INTERVAL)
        tiles_active=sum(1 for v in per_tile_vals.values() if v)
        cpu=cpu_hist[-1] if cpu_hist else 0
        ram=ram_hist[-1] if ram_hist else 0
        lats=" ".join(f"{t}:{latencies_ms[t][-1]:.0f}"
                      if latencies_ms[t] else f"{t}:--"
                      for t in DISPLAY_TILES)
        os.system("cls" if os.name=="nt" else "clear")
        print(f"{datetime.now().strftime('%H:%M:%S')}  "
              f"{msgs/INTERVAL:.1f} msg/s | tiles={tiles_active} | "
              f"CPU={cpu:.1f}% RAM={ram:.1f}%")
        print("Última latencia ms:", lats)
        if STOP_AT and now>=STOP_AT: STOP.set()
        time.sleep(INTERVAL)

# ─────────────── Lanzamiento ───────────────
client=mqtt.Client(); client.on_connect=on_connect; client.on_message=on_message
while True:
    try: client.connect(BROKER,PORT,60); break
    except ConnectionRefusedError: print("Esperando broker…"); time.sleep(2)
client.loop_start()

threading.Thread(target=ping_loop, args=(client,), daemon=True).start()
threading.Thread(target=sys_loop,               daemon=True).start()
threading.Thread(target=console_loop,           daemon=True).start()

try:
    while not STOP.is_set(): time.sleep(1)
except KeyboardInterrupt:
    STOP.set()
client.loop_stop(); client.disconnect()

# ─────────────── Informe final ───────────────
report = BASE_DIR / f"diagnostics_report_{datetime.now().strftime('%Y%m%d-%H%M')}.txt"
with report.open("w") as R:
    dur=time.time()-(STOP_AT-args.duration if STOP_AT else 0)
    total=len(recent_ts)
    R.write(f"== INFORME Tiles {datetime.now(tz.utc)} UTC ==\n")
    R.write(f"Duración {dur:.0f}s  | Mensajes {total} "
            f"({total/max(dur,1):.2f} msg/s)\n\n")
    R.write("Tile  msgs  lat_ms(avg)  val_min  val_max  val_media\n")
    for t in TILES:
        vals=per_tile_vals[t]; lats=latencies_ms[t]
        if vals:
            R.write(f"{t:4} {len(vals):5d}  "
                    f"{(mean(lats) if lats else 0):10.1f}  "
                    f"{min(vals):8d} {max(vals):8d} {mean(vals):10.1f}\n")
        else:
            R.write(f"{t:4}    0       --        --       --        --\n")
    if cpu_hist:
        R.write(f"\nCPU medio {mean(cpu_hist):.1f}%  pico {max(cpu_hist):.1f}%\n")
        R.write(f"RAM media {mean(ram_hist):.1f}%  pico {max(ram_hist):.1f}%\n")

print(f"\n[✓] Archivos guardados en:\n   {BASE_DIR}")
