import paho.mqtt.client as mqtt
import json
import logging
import config

# Quitamos logging.basicConfig(...) aquí

devices_client = None

def init_devices_client():
    global devices_client
    devices_client = mqtt.Client()
    devices_client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
    devices_client.loop_start()
    logging.info("Devices MQTT client initialized and loop started.")

def publish_device_command(device, cmd):
    dev_cfg = config.DEVICES_CONFIG.get(device, {})
    light_topic = dev_cfg.get("light_command_topic")
    if light_topic:
        logging.debug(f"[Devices] (debug) to {light_topic}: {cmd}")
        devices_client.publish(light_topic, json.dumps(cmd))
    else:
        logging.warning(f"[Devices] No light_command_topic found for {device}.")

def turn_on_device(device, brightness=100, color=config.DEFAULT_COLOR):
    cmd = config.get_led_on_command(color=color, brightness=brightness)
    publish_device_command(device, cmd)

def turn_off_device(device):
    cmd = config.get_led_off_command()
    publish_device_command(device, cmd)

def update_device_effect(device, effect_name):
    cmd = config.get_led_effect_command(effect_name)
    if effect_name == "Fast Pulse":
        cmd["color"] = config.DEFAULT_COLOR
        cmd["brightness"] = 100
    publish_device_command(device, cmd)

def turn_on_all():
    for device in config.DEVICES_CONFIG.keys():
        turn_on_device(device)
    logging.info("Turn on command sent to ALL devices.")

def turn_off_all():
    for device in config.DEVICES_CONFIG.keys():
        turn_off_device(device)
    logging.info("Turn off command sent to ALL devices.")

def activate_fast_pulse_global():
    for device in config.DEVICES_CONFIG.keys():
        update_device_effect(device, "Fast Pulse")
    logging.info("Fast Pulse activated on ALL devices.")

def deactivate_fast_pulse_global():
    for device in config.DEVICES_CONFIG.keys():
        turn_off_device(device)
    logging.info("Fast Pulse deactivated on ALL devices.")

def apply_color_to_all(color, brightness_value):
    new_color = {"r": int(color[0]*255), "g": int(color[1]*255), "b": int(color[2]*255)}
    for device in config.DEVICES_CONFIG.keys():
        turn_on_device(device, brightness=brightness_value, color=new_color)
    logging.info(f"New color applied to ALL devices: {new_color}")
