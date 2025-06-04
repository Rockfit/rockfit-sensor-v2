import os
import json

# ================================
# Parámetros de Conexión MQTT
# ================================
MQTT_BROKER = "192.168.8.163"
MQTT_PORT = 1883
EVENT_TOPIC = "rockfit/events/timestamp"

# ================================
# Plantillas para tópicos según el tipo de dispositivo
# ================================
TAG_TOPIC_TEMPLATES = {
    "tap_topic": "devices/{name}/msa3xx/accelsensor/tap",
    "double_tap_topic": "devices/{name}/msa3xx/accelsensor/double_tap",
    "light_command_topic": "devices/{name}/light/circular_leds/command"
}

TILE_TOPIC_TEMPLATES = {
    "loadcell_topic": "devices/{name}/sensor/loadcell/state",
    "light_command_topic": "devices/{name}/light/leds/command"
}

def get_topic(template_dict, name, topic_key):
    template = template_dict.get(topic_key)
    if template:
        return template.format(name=name)
    return None

# ================================
# Constantes de Colores y Brillo
# ================================
DEFAULT_COLOR = {"r": 255, "g": 255, "b": 255}
DEFAULT_GREEN = {"r": 0, "g": 255, "b": 0}
DEFAULT_RED = {"r": 255, "g": 0, "b": 0}

COLOR_RED     = {"r": 255, "g": 0, "b": 0}
COLOR_GREEN   = {"r": 0, "g": 255, "b": 0}
COLOR_BLUE    = {"r": 0, "g": 0, "b": 255}
COLOR_YELLOW  = {"r": 255, "g": 255, "b": 0}
COLOR_MAGENTA = {"r": 255, "g": 0, "b": 255}
COLOR_CYAN    = {"r": 0, "g": 255, "b": 255}
COLOR_WHITE   = {"r": 255, "g": 255, "b": 255}

CELEBRATION_COLORS   = [COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_YELLOW, COLOR_MAGENTA, COLOR_CYAN]
CELEBRATION_INTERVAL = 0.5  # segundos
CELEBRATION_DURATION = 5    # segundos

DEFAULT_BRIGHTNESS = 255
LOW_BRIGHTNESS = int(0.2 * DEFAULT_BRIGHTNESS)

# ================================
# Funciones Utilitarias para Comandos de LED
# ================================
def get_led_off_command():
    return {"state": "OFF"}

def get_led_on_command(color=DEFAULT_COLOR, brightness=DEFAULT_BRIGHTNESS):
    return {"state": "ON", "brightness": brightness, "color": color}

def get_led_on_low_brightness_command(color=DEFAULT_COLOR):
    return get_led_on_command(color=color, brightness=LOW_BRIGHTNESS)

EFFECTS = {
    "pulse": {"state": "ON", "effect": "pulse"},
    "Fast Pulse": {"state": "ON", "effect": "Fast Pulse"},
    "Slow Pulse": {"state": "ON", "effect": "Slow Pulse"},
    "random": {"state": "ON", "effect": "random"},
    "My Slow Random Effect": {"state": "ON", "effect": "My Slow Random Effect"},
    "My Fast Random Effect": {"state": "ON", "effect": "My Fast Random Effect"},
    "strobe": {"state": "ON", "effect": "strobe"},
    "Strobe Effect With Custom Values": {"state": "ON", "effect": "Strobe Effect With Custom Values"},
    "flicker": {"state": "ON", "effect": "flicker"},
    "Flicker Effect With Custom Values": {"state": "ON", "effect": "Flicker Effect With Custom Values"}
}

def get_led_effect_command(effect_name):
    return EFFECTS.get(effect_name, {"state": "ON", "effect": effect_name})

# ================================
# Definición de Dispositivos
# ================================
DEVICES = [
    {"name": "r1", "type": "tag"},
    {"name": "r2", "type": "tag"},#muro negro
    {"name": "r3", "type": "tag"},
    {"name": "r4", "type": "tag"},#cubo abajo dcha2- nija-koala
    {"name": "r5", "type": "tag"},
    {"name": "r6", "type": "tag"},#cubo marron
    {"name": "r7", "type": "tag"},#viga peg boards
    {"name": "r8", "type": "tag"},#viga koalas
    {"name": "r9", "type": "tag"},
    {"name": "r10", "type": "tag"},
    {"name": "r11", "type": "tag"}, #Rampa negra
    {"name": "r12", "type": "tag"}, #nuevo por instalar
    {"name": "r13", "type": "tag"}, #pod acero
    {"name": "v1", "type": "tag"},
    {"name": "tag1", "type": "tag"},#inicio puerta
    {"name": "tag2", "type": "tag"},#inicio pared entrada
    {"name": "tag3", "type": "tag"},
    {"name": "tag4", "type": "tag"},
    {"name": "tag5", "type": "tag"},
    {"name": "tag6", "type": "tag"},
    {"name": "cube1", "type": "tag"},#techo cubo platanos- actualizar
    {"name": "cube2", "type": "tag"},
    {"name": "cube3", "type": "tag"},#cubo abajo dcha1- monkey-koala- actualizar
    {"name": "cube4", "type": "tag"},
    {"name": "koala1", "type": "tag"},#monkey top
    {"name": "koala2", "type": "tag"},
    {"name": "t1", "type": "tile", "threshold": 0.0},
    {"name": "t2", "type": "tile", "threshold": 0.0},
    {"name": "t3", "type": "tile", "threshold": 0.0},
    {"name": "t4", "type": "tile", "threshold": 0.0},
]

DEVICES_CONFIG = {}
for device in DEVICES:
    name = device["name"]
    device_type = device["type"]
    config_entry = device.copy()
    if device_type == "tag":
        config_entry["tap_topic"] = get_topic(TAG_TOPIC_TEMPLATES, name, "tap_topic")
        config_entry["double_tap_topic"] = get_topic(TAG_TOPIC_TEMPLATES, name, "double_tap_topic")
        config_entry["light_command_topic"] = get_topic(TAG_TOPIC_TEMPLATES, name, "light_command_topic")
    elif device_type == "tile":
        config_entry["loadcell_topic"] = get_topic(TILE_TOPIC_TEMPLATES, name, "loadcell_topic")
        config_entry["light_command_topic"] = get_topic(TILE_TOPIC_TEMPLATES, name, "light_command_topic")
    DEVICES_CONFIG[name] = config_entry

# ================================
# LISTA DE USUARIOS
# ================================
USER_LIST = ["U1", "U2", "U3", "U4", "U5", "U6", "U7", "U8"]
    
# ================================
# Definición de Circuitos (todos los circuitos definidos en JSON)
# ================================
'''
CIRCUITS = [
    {
        "id": "circuito_1",
        "name": "Circuito 1",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "tag1",
        "color_initial": {"r": 255, "g": 0, "b": 255},
        "color_mode": "variable",
        "max_time": 60,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 25,
        "default_wait_brightness_strict": 50,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "tag1",   "event": "double_tap", "bonus": False},
            {"order": 2, "device": "koala1", "event": "tap",        "bonus": False},
            {"order": 3, "device": "tag1",   "event": "double_tap", "bonus": False}
        ]
    },
    {
        "id": "circuito_2",
        "name": "Circuito 2",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "r8",
        "color_initial": {"r": 0, "g": 255, "b": 255},
        "color_mode": "variable",
        "max_time": 60,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 25,
        "default_wait_brightness_strict": 50,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "r8", "event": "double_tap", "bonus": False},
            {"order": 2, "device": "r7",   "event": "double_tap",        "bonus": False},
            {"order": 3, "device": "r8", "event": "tap",   "bonus": False},
            { "order": 4, "device": "r7", "event": "tap",         "bonus": False }
        ]
    },
    {
        "id": "circuito_3",
        "name": "Circuito 3",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "koala2",
        "color_initial": {"r": 0, "g": 0, "b": 255},
        "color_mode": "variable",
        "max_time": 60,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 25,
        "default_wait_brightness_strict": 50,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "koala2", "event": "double_tap", "bonus": False},
            {"order": 2, "device": "r3",     "event": "tap",        "bonus": False},
            {"order": 3, "device": "koala2", "event": "double_tap", "bonus": False}
        ]
    },
    {
        "id": "circuito_4",
        "name": "Circuito 4",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "r8",
        "color_initial": {"r": 255, "g": 0, "b": 0},
        "color_mode": "variable",
        "max_time": 60,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 25,
        "default_wait_brightness_strict": 50,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "r8",    "event": "double_tap", "bonus": False},
            {"order": 2, "device": "r8", "event": "tap",        "bonus": False},
            {"order": 3, "device": "r8",    "event": "tap", "bonus": False},
            {"order": 4, "device": "r8", "event": "double_tap",        "bonus": False}
        ]
    },
    {
        "id": "balis_1",
        "name": "balis_1",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "tag1",
        "color_initial": {"r": 255, "g": 0, "b": 255},
        "color_mode": "variable",
        "max_time": 60,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 20,
        "default_wait_brightness_strict": 30,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "tag1",   "event": "double_tap", "bonus": False},
            {"order": 2, "device": "tag4", "event": "tap",        "bonus": False},
            {"order": 3, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 4, "device": "tag1",   "event": "double_tap", "bonus": False},
            {"order": 5, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 6, "device": "tag4",   "event": "double_tap", "bonus": False},
            {"order": 7, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 8, "device": "tag1",   "event": "double_tap", "bonus": False},
            {"order": 9, "device": "tag4",   "event": "tap", "bonus": False},
            {"order": 10, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 11, "device": "tag1",   "event": "double_tap", "bonus": False}
        ]
    },
    {
        "id": "balis_2",
        "name": "balis_2",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "tag4",
        "color_initial": {"r": 255, "g": 0, "b": 255},
        "color_mode": "variable",
        "max_time": 60,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 0,
        "default_wait_brightness_strict": 20,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "tag4",   "event": "double_tap", "bonus": False},
            {"order": 3, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 4, "device": "tag4",   "event": "tap", "bonus": False},
            {"order": 5, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 6, "device": "tag4",   "event": "tap", "bonus": False},
            {"order": 7, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 8, "device": "tag4",   "event": "tap", "bonus": False},
            {"order": 9, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 10, "device": "tag4",   "event": "tap", "bonus": False},
            {"order": 11, "device": "tag3",   "event": "tap", "bonus": False}
        ]
    },
    {
        "id": "rockfit_1",
        "name": "rockfit_1",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "r4",
        "color_initial": {"r": 255, "g": 0, "b": 255},
        "color_mode": "variable",
        "max_time": 999,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 0,
        "default_wait_brightness_strict": 20,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "r4",   "event": "double_tap", "bonus": False},
            {"order": 2, "device": "r1",   "event": "tap", "bonus": False},
            {"order": 3, "device": "r5",   "event": "tap", "bonus": False},
            {"order": 4, "device": "r4",   "event": "tap", "bonus": False},
            {"order": 5, "device": "cube3",   "event": "tap", "bonus": False},
            {"order": 6, "device": "cube4",   "event": "tap", "bonus": False},
            {"order": 7, "device": "r4",   "event": "tap", "bonus": False}
        ]
    },
    {
        "id": "rockfit_2",
        "name": "rockfit_2",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "tag2",
        "color_initial": {"r": 0, "g": 0, "b": 255},
        "color_mode": "variable",
        "max_time": 999,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 0,
        "default_wait_brightness_strict": 20,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "tag2",   "event": "double_tap", "bonus": False},
            {"order": 2, "device": "tag1",   "event": "tap", "bonus": False},
            {"order": 3, "device": "tag2",   "event": "tap", "bonus": False},
            {"order": 4, "device": "tag1",   "event": "tap", "bonus": False},
            {"order": 5, "device": "koala1",   "event": "tap", "bonus": False},
            {"order": 6, "device": "tag1",   "event": "tap", "bonus": False},
            {"order": 7, "device": "tag2",   "event": "tap", "bonus": False}
        ]
    },
    {
        "id": "rockfit_3",
        "name": "rockfit_3",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "r6",
        "color_initial": {"r": 255, "g": 0, "b": 0},
        "color_mode": "variable",
        "max_time": 999,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 0,
        "default_wait_brightness_strict": 20,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "r6",   "event": "double_tap", "bonus": False},
            {"order": 2, "device": "koala2",   "event": "tap", "bonus": False},
            {"order": 3, "device": "r6",   "event": "tap", "bonus": False}
        ]
    },
    {
        "id": "rockfit_mix",
        "name": "rockfit_mix",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "tag2",
        "color_initial": {"r": 255, "g": 0, "b": 0},
        "color_mode": "variable",
        "max_time": 999,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 0,
        "default_wait_brightness_strict": 20,
        "default_wait_brightness_flexible": 60,
 "steps": [
            {"order": 1, "device": "tag2",   "event": "double_tap", "bonus": False},
            {"order": 2, "device": "r6",   "event": "tap", "bonus": False},
            {"order": 3, "device": "koala2",   "event": "tap", "bonus": False},
            {"order": 4, "device": "r1",   "event": "tap", "bonus": False},
            {"order": 5, "device": "r5",   "event": "tap", "bonus": False},
        ]
    }
]
'''
CIRCUITS = [
    {
        "id": "circuito_1",
        "name": "Circuito 1",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "r7",
        "color_initial": {"r": 255, "g": 0, "b": 255},
        "color_mode": "variable",
        "max_time": 60,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 25,
        "default_wait_brightness_strict": 50,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "r7",   "event": "double_tap", "bonus": False},
            {"order": 2, "device": "r7", "event": "tap",        "bonus": False},
            {"order": 3, "device": "r7",   "event": "double_tap", "bonus": False}
        ]
    },
    {
        "id": "circuito_2",
        "name": "Circuito 2",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "r8",
        "color_initial": {"r": 0, "g": 255, "b": 255},
        "color_mode": "variable",
        "max_time": 60,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 25,
        "default_wait_brightness_strict": 50,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "r8", "event": "double_tap", "bonus": False},
            {"order": 2, "device": "r7",   "event": "double_tap",        "bonus": False},
            {"order": 3, "device": "r8", "event": "tap",   "bonus": False},
            { "order": 4, "device": "r7", "event": "tap",         "bonus": False }
        ]
    },
    {
        "id": "circuito_3",
        "name": "Circuito 3",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "koala2",
        "color_initial": {"r": 0, "g": 0, "b": 255},
        "color_mode": "variable",
        "max_time": 60,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 25,
        "default_wait_brightness_strict": 50,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "koala2", "event": "double_tap", "bonus": False},
            {"order": 2, "device": "r3",     "event": "tap",        "bonus": False},
            {"order": 3, "device": "koala2", "event": "double_tap", "bonus": False}
        ]
    },
    {
        "id": "circuito_4",
        "name": "Circuito 4",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "r8",
        "color_initial": {"r": 255, "g": 0, "b": 0},
        "color_mode": "variable",
        "max_time": 60,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 25,
        "default_wait_brightness_strict": 50,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "r8",    "event": "double_tap", "bonus": False},
            {"order": 2, "device": "r8", "event": "tap",        "bonus": False},
            {"order": 3, "device": "r8",    "event": "tap", "bonus": False},
            {"order": 4, "device": "r8", "event": "double_tap",        "bonus": False}
        ]
    },
    {
        "id": "balis_1",
        "name": "balis_1",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "tag1",
        "color_initial": {"r": 255, "g": 0, "b": 255},
        "color_mode": "variable",
        "max_time": 60,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 20,
        "default_wait_brightness_strict": 30,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "tag1",   "event": "double_tap", "bonus": False},
            {"order": 2, "device": "tag4", "event": "tap",        "bonus": False},
            {"order": 3, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 4, "device": "tag1",   "event": "double_tap", "bonus": False},
            {"order": 5, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 6, "device": "tag4",   "event": "double_tap", "bonus": False},
            {"order": 7, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 8, "device": "tag1",   "event": "double_tap", "bonus": False},
            {"order": 9, "device": "tag4",   "event": "tap", "bonus": False},
            {"order": 10, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 11, "device": "tag1",   "event": "double_tap", "bonus": False}
        ]
    },
    {
        "id": "balis_2",
        "name": "balis_2",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "tag4",
        "color_initial": {"r": 255, "g": 0, "b": 255},
        "color_mode": "variable",
        "max_time": 60,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 0,
        "default_wait_brightness_strict": 20,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "tag4",   "event": "double_tap", "bonus": False},
            {"order": 3, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 4, "device": "tag4",   "event": "tap", "bonus": False},
            {"order": 5, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 6, "device": "tag4",   "event": "tap", "bonus": False},
            {"order": 7, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 8, "device": "tag4",   "event": "tap", "bonus": False},
            {"order": 9, "device": "tag3",   "event": "tap", "bonus": False},
            {"order": 10, "device": "tag4",   "event": "tap", "bonus": False},
            {"order": 11, "device": "tag3",   "event": "tap", "bonus": False}
        ]
    },
    {
        "id": "rockfit_1",
        "name": "rockfit_1",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "cube3",
        "color_initial": {"r": 255, "g": 0, "b": 255},
        "color_mode": "variable",
        "max_time": 999,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 0,
        "default_wait_brightness_strict": 20,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "cube3",   "event": "double_tap", "bonus": False},
            {"order": 2, "device": "cube4",   "event": "tap", "bonus": False},
            {"order": 3, "device": "r5",   "event": "tap", "bonus": False},
            {"order": 4, "device": "r1",   "event": "tap", "bonus": False},
            {"order": 5, "device": "r4",   "event": "tap", "bonus": False},
        ]
    },
    {
        "id": "rockfit_2",
        "name": "rockfit_2",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "tag1",
        "color_initial": {"r": 0, "g": 0, "b": 255},
        "color_mode": "variable",
        "max_time": 999,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 0,
        "default_wait_brightness_strict": 20,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "tag1",   "event": "double_tap", "bonus": False},
            {"order": 2, "device": "koala1",   "event": "tap", "bonus": False},
            {"order": 3, "device": "r6",   "event": "tap", "bonus": False},
            {"order": 4, "device": "tag1",   "event": "tap", "bonus": False}
        ]
    },
    {
        "id": "rockfit_3",
        "name": "rockfit_3",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "tag2",
        "color_initial": {"r": 255, "g": 0, "b": 0},
        "color_mode": "variable",
        "max_time": 999,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 0,
        "default_wait_brightness_strict": 20,
        "default_wait_brightness_flexible": 60,
        "steps": [
            {"order": 1, "device": "tag2",   "event": "double_tap", "bonus": False},
            {"order": 2, "device": "r3",   "event": "tap", "bonus": False},
            {"order": 3, "device": "koala2",   "event": "tap", "bonus": False},
            {"order": 4, "device": "r3",   "event": "tap", "bonus": False},
            {"order": 4, "device": "koala2",   "event": "tap", "bonus": False}
        ]
    },
    {
        "id": "rockfit_mix",
        "name": "rockfit_mix",
        "description": "Circuito en modo strict con color variable. Control device: r4 (se activa con double_tap).",
        "control_device": "tag2",
        "color_initial": {"r": 255, "g": 0, "b": 0},
        "color_mode": "variable",
        "max_time": 999,
        "completion_effect": "celebration",
        "order_mode": "strict",
        "state_reposo": "all_active",
        "surpassed_light": 0,
        "default_wait_brightness_strict": 20,
        "default_wait_brightness_flexible": 60,
 "steps": [
            {"order": 1, "device": "tag2",   "event": "double_tap", "bonus": False},
            {"order": 2, "device": "r6",   "event": "tap", "bonus": False},
            {"order": 3, "device": "koala2",   "event": "tap", "bonus": False},
            {"order": 4, "device": "r1",   "event": "tap", "bonus": False},
            {"order": 5, "device": "r5",   "event": "tap", "bonus": False},
        ]
    }
]