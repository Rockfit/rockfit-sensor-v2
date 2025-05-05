"""
config_base.py
---------------
Este archivo contiene elementos inmutables, plantillas de tópicos, constantes de colores, niveles de brillo y funciones genéricas
para generar comandos de LED y para resetear dispositivos. Estas definiciones no se esperan cambiar en caliente.
"""

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
    """
    Devuelve el tópico para un dispositivo dado utilizando la plantilla correspondiente.
    """
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

# Batería de colores (útil para efectos, indicaciones, etc.)
COLOR_RED     = {"r": 255, "g": 0, "b": 0}
COLOR_GREEN   = {"r": 0, "g": 255, "b": 0}
COLOR_BLUE    = {"r": 0, "g": 0, "b": 255}
COLOR_YELLOW  = {"r": 255, "g": 255, "b": 0}
COLOR_MAGENTA = {"r": 255, "g": 0, "b": 255}
COLOR_CYAN    = {"r": 0, "g": 255, "b": 255}
COLOR_WHITE   = {"r": 255, "g": 255, "b": 255}

# Modo "Celebración" (anteriormente disco)
CELEBRATION_COLORS   = [COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_YELLOW, COLOR_MAGENTA, COLOR_CYAN]
CELEBRATION_INTERVAL = 0.5  # Intervalo en segundos para cambio de color
CELEBRATION_DURATION = 5    # Duración total en segundos del modo celebración

# Niveles de brillo
DEFAULT_BRIGHTNESS = 255
LOW_BRIGHTNESS = int(0.2 * DEFAULT_BRIGHTNESS)  # Aproximadamente 20%

# ================================
# Funciones Utilitarias para Comandos de LED
# ================================
def get_led_off_command():
    """Genera el comando para apagar el LED."""
    return {"state": "OFF"}

def get_led_on_command(color=DEFAULT_COLOR, brightness=DEFAULT_BRIGHTNESS):
    """Genera el comando para encender el LED con el color y brillo especificados."""
    return {"state": "ON", "brightness": brightness, "color": color}

def get_led_on_low_brightness_command(color=DEFAULT_COLOR):
    """Genera el comando para encender el LED con baja intensidad (aprox. 20%)."""
    return get_led_on_command(color=color, brightness=LOW_BRIGHTNESS)

# ================================
# Definición de Efectos Disponibles en el Dispositivo
# ================================
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
    """
    Retorna el comando para activar un efecto de LED dado su nombre.
    Si el efecto no se encuentra en EFFECTS, retorna un comando básico usando el nombre.
    Ejemplo:
       get_led_effect_command("Fast Pulse") -> {"state": "ON", "effect": "Fast Pulse"}
    """
    return EFFECTS.get(effect_name, {"state": "ON", "effect": effect_name})
