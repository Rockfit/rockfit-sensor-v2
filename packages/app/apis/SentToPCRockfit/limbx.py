from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock
import threading
import logging

import logic
import logic_devices
import config

active_circuits = ["circuito_2"]
logic_thread = None

def update_active_circuits(new_active):
    global active_circuits, logic_thread
    active_circuits = new_active
    logging.info(f"Reiniciando sistema con active_circuits: {active_circuits}")

    # Si se desea limpiar las instancias previas:
    # logic.circuits.clear()

    def reconfigure():
        logic.main(active_circuits)

    new_thread = threading.Thread(target=reconfigure, daemon=True)
    new_thread.start()
    logic_thread = new_thread

class LimbxApp(App):
    def build(self):
        self.sm = ScreenManager()
        from config_screen import ConfigScreen
        from devices_screen import DevicesScreen
        from game_screen import GameScreen

        self.config_screen = ConfigScreen(name="config")
        self.devices_screen = DevicesScreen(name="devices")
        self.game_screen = GameScreen(name="game")

        self.sm.add_widget(self.config_screen)
        self.sm.add_widget(self.devices_screen)
        self.sm.add_widget(self.game_screen)

        root = BoxLayout(orientation="vertical")
        nav_bar = BoxLayout(size_hint=(1, 0.1))

        btn_config = Button(text="Config")
        btn_config.bind(on_release=lambda x: setattr(self.sm, 'current', 'config'))
        btn_devices = Button(text="Devices")
        btn_devices.bind(on_release=lambda x: setattr(self.sm, 'current', 'devices'))
        btn_game = Button(text="Game")
        btn_game.bind(on_release=lambda x: setattr(self.sm, 'current', 'game'))

        nav_bar.add_widget(btn_config)
        nav_bar.add_widget(btn_devices)
        nav_bar.add_widget(btn_game)

        root.add_widget(nav_bar)
        root.add_widget(self.sm)

        # Actualizamos la vista de GameScreen usando update_cards() (no update_active_label)
        Clock.schedule_interval(lambda dt: self.game_screen.update_cards(dt), 1)
        return root

    def on_start(self):
        def init_logic():
            logic.main(active_circuits)  # Arranca la lógica con los circuitos por defecto
            logic_devices.init_devices_client()

        init_thread = threading.Thread(target=init_logic, daemon=True)
        init_thread.start()

        # Forzamos el nivel de log a INFO para ocultar mensajes DEBUG
        logging.getLogger().setLevel(logging.INFO)

if __name__ == '__main__':
    LimbxApp().run()
