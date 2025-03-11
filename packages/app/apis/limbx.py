# limbx.py
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.label import Label
import threading

import logic  # Nuestro módulo de lógica
import config_base

# Variable global para controlar la intensidad (brightness)
global_brightness = 100  # Valor por defecto

# Funciones globales para controles de luces

def turn_on_all():
    for circuit in logic.circuits:
        for device in circuit.sequence:
            circuit.update_led(device, global_brightness)

def turn_off_all():
    for circuit in logic.circuits:
        for device in circuit.sequence:
            circuit.turn_off_led(device)

def activate_fast_pulse_global():
    for circuit in logic.circuits:
        for device in circuit.sequence:
            circuit.update_led_effect(device, "Fast Pulse")

def deactivate_fast_pulse_global():
    for circuit in logic.circuits:
        for device in circuit.sequence:
            circuit.turn_off_led(device)

def apply_color_to_all(color, brightness_value):
    # Convierte la selección de color (valores entre 0 y 1) a valores entre 0 y 255
    new_color = {"r": int(color[0]*255), "g": int(color[1]*255), "b": int(color[2]*255)}
    for circuit in logic.circuits:
        circuit.user_color = new_color
        # Actualiza todos los LED del circuito usando el brillo seleccionado
        for device in circuit.sequence:
            circuit.update_led(device, brightness_value)

# Funciones para simular eventos en Circuito 2 (ejemplo: tag3 y tag4)
def get_circuit_by_name(name):
    for c in logic.circuits:
        if c.name == name:
            return c
    return None

def simulate_tap(circuit_name, device):
    circuit = get_circuit_by_name(circuit_name)
    if circuit:
        circuit.tap(device)

def simulate_double_tap(circuit_name, device):
    circuit = get_circuit_by_name(circuit_name)
    if circuit:
        circuit.double_tap(device)

class ControlPanel(BoxLayout):
    def __init__(self, **kwargs):
        super(ControlPanel, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 10
        self.padding = 10

        # Título
        self.add_widget(Label(text="Rockfit Control Panel", font_size="24sp", size_hint=(1,0.1)))

        # Panel de control global
        global_controls = GridLayout(cols=2, spacing=10, size_hint=(1,0.3))
        btn_on = Button(text="Encender Todas")
        btn_on.bind(on_press=lambda x: turn_on_all())
        btn_off = Button(text="Apagar Todas")
        btn_off.bind(on_press=lambda x: turn_off_all())
        btn_fast_on = Button(text="Activar Fast Pulse Global")
        btn_fast_on.bind(on_press=lambda x: activate_fast_pulse_global())
        btn_fast_off = Button(text="Desactivar Fast Pulse Global")
        btn_fast_off.bind(on_press=lambda x: deactivate_fast_pulse_global())
        global_controls.add_widget(btn_on)
        global_controls.add_widget(btn_off)
        global_controls.add_widget(btn_fast_on)
        global_controls.add_widget(btn_fast_off)
        self.add_widget(global_controls)

        # Selector de Color y control de Intensidad
        self.color_picker = ColorPicker(size_hint=(1, 0.5))
        self.add_widget(self.color_picker)
        brightness_layout = BoxLayout(orientation="horizontal", size_hint=(1,0.1))
        brightness_layout.add_widget(Label(text="Intensidad:"))
        self.brightness_slider = Slider(min=0, max=255, value=global_brightness)
        self.brightness_slider.bind(value=self.on_brightness_change)
        brightness_layout.add_widget(self.brightness_slider)
        self.add_widget(brightness_layout)
        btn_apply_color = Button(text="Aplicar color a todos", size_hint=(1,0.1))
        btn_apply_color.bind(on_press=lambda x: apply_color_to_all(self.color_picker.color, self.brightness_slider.value))
        self.add_widget(btn_apply_color)

        # Panel para reiniciar circuitos individualmente
        circuit_controls = GridLayout(cols=3, spacing=10, size_hint=(1,0.2))
        for circuit in logic.circuits:
            btn_reset = Button(text=f"Reset {circuit.name}")
            btn_reset.bind(on_press=lambda x, c=circuit: c.reset())
            circuit_controls.add_widget(btn_reset)
        self.add_widget(circuit_controls)

        # Panel para simular eventos en Circuito 2 (tag3 y tag4)
        sim_controls = GridLayout(cols=2, spacing=10, size_hint=(1,0.2))
        sim_controls.add_widget(Button(text="Simular TAP tag3 (C2)", on_press=lambda x: simulate_tap("Circuito 2", "tag3")))
        sim_controls.add_widget(Button(text="Simular DOUBLE TAP tag3 (C2)", on_press=lambda x: simulate_double_tap("Circuito 2", "tag3")))
        sim_controls.add_widget(Button(text="Simular TAP tag4 (C2)", on_press=lambda x: simulate_tap("Circuito 2", "tag4")))
        sim_controls.add_widget(Button(text="Simular DOUBLE TAP tag4 (C2)", on_press=lambda x: simulate_double_tap("Circuito 2", "tag4")))
        self.add_widget(sim_controls)

    def on_brightness_change(self, instance, value):
        global global_brightness
        global_brightness = value

class LimbxApp(App):
    def build(self):
        return ControlPanel()

    def on_start(self):
        threading.Thread(target=logic.main, daemon=True).start()

if __name__ == '__main__':
    LimbxApp().run()
