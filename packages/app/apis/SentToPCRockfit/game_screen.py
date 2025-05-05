from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.properties import ListProperty
import time
import logging

import logic
import config

# --- Constantes de color para los fondos de cada sección ---
ACTIVE_BG_COLOR = [0, 0, 0, 1]        # Fondo para circuitos activos
COMPLETED_BG_COLOR = [0.10, 0.10, 0, 1]         # Fondo circuitos completados

# --- Widget personalizado para fondo coloreado ---
class ColoredBoxLayout(BoxLayout):
    bg_color = ListProperty([1, 1, 1, 1])
    
    def __init__(self, **kwargs):
        self.bg_color = kwargs.pop('bg_color', [1, 1, 1, 1])
        super(ColoredBoxLayout, self).__init__(**kwargs)
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect, bg_color=self.update_rect_color)
        
    def update_rect(self, instance, value):
        self.rect.pos = self.pos
        self.rect.size = self.size
        
    def update_rect_color(self, instance, value):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.scroll = ScrollView(size_hint=(1, 1))
        # Main layout containing the cards
        self.main_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        self.main_layout.bind(minimum_height=self.main_layout.setter('height'))

        self.scroll.add_widget(self.main_layout)
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

        Clock.schedule_interval(self.update_cards, 1)

    def normalize_color(self, color_dict):
        return [
            color_dict['r'] / 255.0,
            color_dict['g'] / 255.0,
            color_dict['b'] / 255.0,
            1
        ]

    def add_border(self, widget, color):
        with widget.canvas.before:
            Color(*self.normalize_color(color))
            widget._border_line = Line(rectangle=(widget.x, widget.y, widget.width, widget.height), width=1)
        widget.bind(pos=self.update_border, size=self.update_border)

    def update_border(self, instance, value):
        instance._border_line.rectangle = (instance.x, instance.y, instance.width, instance.height)

    def update_cards(self, dt):
        self.main_layout.clear_widgets()

        # --- Circuitos Activos ---
        active_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        active_layout.bind(minimum_height=active_layout.setter('height'))
        active_layout.add_widget(Label(text="Circuitos Activos", font_size="18sp", size_hint_y=None, height=30))
        for circuit in logic.circuits:
            if circuit.state in ["waiting", "in_progress", "timeout"]:
                card = self.create_active_card(circuit)
                active_layout.add_widget(card)
        # Envolvemos active_layout en un ColoredBoxLayout con el fondo para activos
        active_container = ColoredBoxLayout(orientation='vertical', spacing=5, size_hint_y=None, bg_color=ACTIVE_BG_COLOR)
        active_container.add_widget(active_layout)
        active_container.bind(minimum_height=active_container.setter('height'))

        # --- Circuitos Completados ---
        completed_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        completed_layout.bind(minimum_height=completed_layout.setter('height'))
        completed_layout.add_widget(Label(text="Circuitos Completados", font_size="18sp", size_hint_y=None, height=30))
        for result in logic.completed_circuits:
            card = self.create_completed_card(result)
            completed_layout.add_widget(card)
        # Envolvemos completed_layout en un ColoredBoxLayout con fondo para completados
        completed_container = ColoredBoxLayout(orientation='vertical', spacing=5, size_hint_y=None, bg_color=COMPLETED_BG_COLOR)
        completed_container.add_widget(completed_layout)
        completed_container.bind(minimum_height=completed_container.setter('height'))

        self.main_layout.add_widget(active_container)
        self.main_layout.add_widget(completed_container)

    def create_active_card(self, circuit):
        card = BoxLayout(orientation='vertical', padding=1, spacing=1, size_hint_y=None)
        card.height = 120

        circuit_color = circuit.get_current_color() if hasattr(circuit, "get_current_color") else circuit.color_initial

        info_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
        total_steps = len(circuit.sequence)
        current_index = circuit.current_index
        prog_text = f"{current_index}/{total_steps}"

        if circuit.state == "completed" and hasattr(circuit, "total_time"):
            time_text = f"{circuit.total_time:.2f}s"
        elif circuit.start_time:
            elapsed = time.time() - circuit.start_time
            time_text = f"{elapsed:.2f}s"
        else:
            time_text = "0s"

        col1 = BoxLayout(orientation='vertical', size_hint_x=0.33)
        col1.add_widget(Label(text=f"Progreso: {prog_text}", font_size="14sp", halign="center", valign="middle"))
        col1.add_widget(Label(text=f"Tiempo: {time_text}", font_size="14sp", halign="center", valign="middle"))

        next_step_str = ""
        if circuit.state in ["waiting", "in_progress"]:
            if current_index < total_steps:
                dev = circuit.sequence[current_index]
                evt = circuit.steps[current_index]["event"]
                next_step_str = f" - {dev}({evt})"

        title_text = f"{circuit.name}: {circuit.state}{next_step_str}"
        col2 = BoxLayout(orientation='vertical', size_hint_x=0.34)
        col2.add_widget(Label(text=title_text, font_size="16sp", halign="center", valign="middle"))

        assigned = circuit.assigned_users[0] if circuit.assigned_users else "Sin asignar"
        spinner_values = list(config.USER_LIST) + ["Nuevo"]
        spinner_assigned = Spinner(text=assigned, values=spinner_values, size_hint=(1, None), height=40)

        def on_select_user(spinner, new_selection):
            if new_selection == "Nuevo":
                spinner_assigned.text = assigned
                self.show_new_user_popup(circuit=circuit, result=None)
            else:
                circuit.assigned_users = [new_selection] if new_selection != "Sin asignar" else []
                self.update_cards(0)

        spinner_assigned.bind(text=on_select_user)
        col3 = BoxLayout(orientation='vertical', size_hint_x=0.33)
        col3.add_widget(spinner_assigned)

        info_row.add_widget(col1)
        info_row.add_widget(col2)
        info_row.add_widget(col3)
        card.add_widget(info_row)

        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
        skip_text = f"Saltar Paso: {current_index}/{total_steps}"
        btn_skip = Button(text=skip_text)
        btn_finish = Button(text="Finalizar")
        btn_more = Button(text="Más Info")

        normalized_color = self.normalize_color(circuit_color)
        btn_skip.background_color = normalized_color
        btn_finish.background_color = normalized_color
        btn_more.background_color = normalized_color

        def on_skip(_instance):
            circuit.skip_step()
            self.update_cards(0)
        btn_skip.bind(on_release=on_skip)
        btn_finish.bind(on_release=lambda instance: self.finish_circuit(circuit))
        btn_more.bind(on_release=lambda instance: self.show_more_info(circuit))

        btn_row.add_widget(btn_skip)
        btn_row.add_widget(btn_finish)
        btn_row.add_widget(btn_more)
        card.add_widget(btn_row)

        self.add_border(card, circuit_color)
        return card

    def create_completed_card(self, result):
        card = BoxLayout(orientation='vertical', padding=5, spacing=5, size_hint_y=None)
        card.height = 110

        color = result.get("final_color", {"r": 255, "g": 255, "b": 255})
        title_text = f"{result['name']}: COMPLETED"
        info_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)

        time_val = f"{result['total_time']:.2f}s"
        col1 = BoxLayout(orientation='vertical', size_hint_x=0.33)
        col1.add_widget(Label(text=f"Tiempo: {time_val}", font_size="14sp", halign="center", valign="middle"))

        col2 = BoxLayout(orientation='vertical', size_hint_x=0.34)
        col2.add_widget(Label(text=title_text, font_size="16sp", halign="center", valign="middle"))

        assigned = result["assigned_users"][0] if result["assigned_users"] else "Sin asignar"
        spinner_values = list(config.USER_LIST) + ["Nuevo"]
        spinner_assigned = Spinner(text=assigned, values=spinner_values, size_hint=(1, None), height=40)

        def on_select_user_completed(spinner, new_selection):
            if new_selection == "Nuevo":
                spinner_assigned.text = assigned
                self.show_new_user_popup(circuit=None, result=result)
            else:
                if new_selection == "Sin asignar":
                    result["assigned_users"] = []
                else:
                    result["assigned_users"] = [new_selection]
                self.update_cards(0)

        spinner_assigned.bind(text=on_select_user_completed)
        col3 = BoxLayout(orientation='vertical', size_hint_x=0.33)
        col3.add_widget(spinner_assigned)

        info_row.add_widget(col1)
        info_row.add_widget(col2)
        info_row.add_widget(col3)
        card.add_widget(info_row)

        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
        btn_more = Button(text="Más Info")
        btn_more.background_color = self.normalize_color(color)
        btn_more.bind(on_release=lambda instance: self.show_more_info_result(result))
        btn_row.add_widget(btn_more)
        card.add_widget(btn_row)

        self.add_border(card, color)
        return card

    def skip_step(self, circuit):
        try:
            circuit.skip_step()
            self.update_cards(0)
        except Exception as e:
            logging.error(f"Error al saltar paso en {circuit.name}: {e}")

    def finish_circuit(self, circuit):
        try:
            circuit.complete_circuit()
        except Exception as e:
            logging.error(f"Error al finalizar circuito {circuit.name}: {e}")

    def show_more_info(self, circuit):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        details = f"Circuito: {circuit.name}\n"
        details += f"Estado: {circuit.state}\n"
        details += f"Progreso: {circuit.current_index}/{len(circuit.sequence)}\n"
        if circuit.start_time:
            elapsed = time.time() - circuit.start_time
            details += f"Tiempo transcurrido: {elapsed:.2f}s\n"
        if hasattr(circuit, 'total_time') and circuit.total_time:
            details += f"Tiempo total: {circuit.total_time:.2f}s\n"
        assigned = ", ".join(circuit.assigned_users) if circuit.assigned_users else "Sin asignar"
        details += f"Asignado a: {assigned}\n"
        details += "Eventos:\n"
        for ev in circuit.timestamps:
            details += f"  {ev[2]} - {ev[0]} en {ev[1]}\n"
        content.add_widget(Label(text=details))
        btn_close = Button(text="Cerrar", size_hint_y=None, height=40)
        content.add_widget(btn_close)
        popup = Popup(title="Detalles del Circuito", content=content, size_hint=(0.8, 0.8))
        btn_close.bind(on_release=popup.dismiss)
        popup.open()

    def show_more_info_result(self, result):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        details = f"Circuito: {result['name']}\n"
        details += f"Tiempo total: {result['total_time']:.2f}s\n"
        assigned = ", ".join(result["assigned_users"]) if result["assigned_users"] else "Sin asignar"
        details += f"Asignado a: {assigned}\n"
        details += "Eventos:\n"
        for ev in result["timestamps"]:
            details += f"  {ev[2]} - {ev[0]} en {ev[1]}\n"
        content.add_widget(Label(text=details))
        btn_close = Button(text="Cerrar", size_hint_y=None, height=40)
        content.add_widget(btn_close)
        popup = Popup(title="Detalles del Circuito Completado", content=content, size_hint=(0.8, 0.8))
        btn_close.bind(on_release=popup.dismiss)
        popup.open()

    def show_new_user_popup(self, circuit=None, result=None):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        new_user_input = TextInput(hint_text="Ingresa nuevo usuario", multiline=False, size_hint=(1, None), height=40)
        layout.add_widget(new_user_input)
        button_box = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)
        btn_ok = Button(text="OK")
        btn_cancel = Button(text="Cancelar")
        button_box.add_widget(btn_ok)
        button_box.add_widget(btn_cancel)
        layout.add_widget(button_box)
        popup_new_user = Popup(title="Nuevo Usuario", content=layout, size_hint=(0.8, 0.4))
        def on_ok(_instance):
            new_user = new_user_input.text.strip()
            if new_user and (new_user not in config.USER_LIST):
                config.USER_LIST.append(new_user)
            if new_user:
                if circuit:
                    circuit.assigned_users = [new_user]
                elif result is not None:
                    result["assigned_users"] = [new_user]
            popup_new_user.dismiss()
            self.update_cards(0)
        def on_cancel(_instance):
            popup_new_user.dismiss()
        btn_ok.bind(on_release=on_ok)
        btn_cancel.bind(on_release=on_cancel)
        popup_new_user.open()
