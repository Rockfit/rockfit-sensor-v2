#config_params.py

"""Este archivo contiene los parámetros específicos del entorno y del juego.
Aquí se definen la conexión MQTT, los dispositivos y las secuencias de juego.
Se podrá modificar en caliente (por ejemplo, a través de una GUI) sin alterar la base.
"""

from config_base import TAG_TOPIC_TEMPLATES, TILE_TOPIC_TEMPLATES, get_topic

# ================================
# Parámetros de Conexión MQTT
# ================================
MQTT_BROKER = "192.168.8.163"
MQTT_PORT = 1883
EVENT_TOPIC = "rockfit/events/timestamp"

# ================================
# Definición de Dispositivos
# Cada dispositivo se define con:
# - name: nombre único.
# - type: "tag" o "tile".
# Se pueden incluir otros parámetros específicos (por ejemplo, threshold en el caso de tiles).
# ================================
DEVICES = [
    {"name": "tag1", "type": "tag"},
    {"name": "tag2", "type": "tag"},
    {"name": "tag3", "type": "tag"},
    {"name": "tag4", "type": "tag"},
    {"name": "tag5", "type": "tag"},
    {"name": "tag6", "type": "tag"},
    {"name": "cube1", "type": "tag"},
    {"name": "cube2", "type": "tag"},
    {"name": "cube3", "type": "tag"},
    {"name": "cube4", "type": "tag"},
    {"name": "koala1", "type": "tag"},
    {"name": "koala2", "type": "tag"},
    {"name": "r2", "type": "tag"},
    # Ejemplo de dispositivo tipo tile:
    # {"name": "tile1", "type": "tile", "threshold": 0.0},
]

# A partir de la lista de dispositivos, se genera una configuración completa usando las plantillas
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
# Definición de Secuencias de Juego
# Se pueden definir múltiples secuencias y seleccionar una mediante un "game number".
# ================================
GAME_SEQUENCES = {
    1: ["tag1", "koala1", "tag1"],
    2: ["tag2", "tag2"],
    3: ["cube3", "cube4", "cube1"]
}

# Parámetro actual para seleccionar la secuencia de juego.
# Este valor se podrá cambiar (incluso en caliente) para seleccionar otra secuencia.
CURRENT_GAME = 1
CURRENT_LOGIC = 1

def get_game_sequence(game_number=None):
    """
    Devuelve la secuencia de juego para el número especificado.
    Si no se indica, se utiliza CURRENT_GAME.
    """
    if game_number is None:
        game_number = CURRENT_GAME
    return GAME_SEQUENCES.get(game_number, [])
