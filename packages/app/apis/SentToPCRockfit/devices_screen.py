from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.label import Label
import logic_devices

class DevicesScreen(Screen):
    def __init__(self, **kwargs):
        super(DevicesScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        layout.add_widget(Label(text="Pantalla de Dispositivos", font_size="24sp", size_hint=(1, 0.1)))
        
        global_controls = GridLayout(cols=2, spacing=10, size_hint=(1, 0.3))
        btn_on = Button(text="Encender Todas")
        btn_on.bind(on_release=lambda x: logic_devices.turn_on_all())
        btn_off = Button(text="Apagar Todas")
        btn_off.bind(on_release=lambda x: logic_devices.turn_off_all())
        btn_fp_on = Button(text="Activar Fast Pulse Global")
        btn_fp_on.bind(on_release=lambda x: logic_devices.activate_fast_pulse_global())
        btn_fp_off = Button(text="Desactivar Fast Pulse Global")
        btn_fp_off.bind(on_release=lambda x: logic_devices.deactivate_fast_pulse_global())
        global_controls.add_widget(btn_on)
        global_controls.add_widget(btn_off)
        global_controls.add_widget(btn_fp_on)
        global_controls.add_widget(btn_fp_off)
        layout.add_widget(global_controls)
        
        self.color_picker = ColorPicker(size_hint=(1, 0.5))
        layout.add_widget(self.color_picker)
        
        brightness_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        brightness_layout.add_widget(Label(text="Intensidad:"))
        self.brightness_slider = Slider(min=0, max=255, value=100)
        brightness_layout.add_widget(self.brightness_slider)
        layout.add_widget(brightness_layout)
        
        btn_apply_color = Button(text="Aplicar color a TODOS", size_hint=(1, 0.1))
        btn_apply_color.bind(on_release=lambda x: logic_devices.apply_color_to_all(self.color_picker.color, self.brightness_slider.value))
        layout.add_widget(btn_apply_color)
        
        self.add_widget(layout)
