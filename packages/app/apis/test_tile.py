import paho.mqtt.client as mqtt
import json
import threading
import time

# ——————————————
# Configuración
# ——————————————
BROKER = "192.168.8.163"
PORT = 1883
TILE_NAME = "tile16"

LOADCELL_TOPIC     = f"devices/{TILE_NAME}/sensor/loadcell/state"
LED_COMMAND_TOPIC  = f"devices/{TILE_NAME}/light/leds/command"

# Umbral mínimo de variación para imprimir (ajustable)
THRESHOLD = 500

# Almacena el último valor publicado
last_value = None


def on_connect(client, userdata, flags, rc):
    print(f"Conectado al broker {BROKER}:{PORT} (rc={rc})")
    client.subscribe(LOADCELL_TOPIC)
    print(f"Suscrito a {LOADCELL_TOPIC}")

    # Al iniciar, encender LED en rojo durante 3 s y luego apagar
    red_cmd = {"state": "ON",  "brightness": 255, "color": {"r":255,"g":0,"b":0}}
    off_cmd = {"state": "OFF"}

    client.publish(LED_COMMAND_TOPIC, json.dumps(red_cmd))
    threading.Timer(3.0, lambda: client.publish(LED_COMMAND_TOPIC, json.dumps(off_cmd))).start()


def on_message(client, userdata, msg):
    global last_value
    try:
        value = int(msg.payload.decode())
    except ValueError:
        return

    # Solo mostrar si la diferencia con el último valor supera el umbral
    if last_value is None or abs(value - last_value) >= THRESHOLD:
        print(f"[{msg.topic}] {value}")
        last_value = value
    # de lo contrario, se ignora


def main():
    client = mqtt.Client()  # Para silenciar el DeprecationWarning, podrías usar mqtt.Client(callback_api_version=2)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    main()
