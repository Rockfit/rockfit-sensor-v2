from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView

import config

class ConfigScreen(Screen):
    def __init__(self, **kwargs):
        super(ConfigScreen, self).__init__(**kwargs)
        
        # Variables auxiliares para la pestaña Usuarios (y circuitos)
        self.user_textinputs = []
        self.user_list_layout = None
        self.selected_circuits = set()

        # Layout principal
        main_layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Panel de pestañas
        self.tab_panel = TabbedPanel(do_default_tab=False)

        # =======================
        #   PESTAÑA: CIRCUITOS
        # =======================
        self.circuits_tab = TabbedPanelItem(text="Circuitos")
        self.circuits_tab.content = self.build_circuits_config_layout()
        self.tab_panel.add_widget(self.circuits_tab)

        # =======================
        #   PESTAÑA: USUARIOS
        # =======================
        self.users_tab = TabbedPanelItem(text="Usuarios")
        self.users_tab.content = self.build_users_config_layout()
        self.tab_panel.add_widget(self.users_tab)

        # Añadimos el TabbedPanel al layout principal
        main_layout.add_widget(self.tab_panel)

        # Pestaña por defecto: Circuitos
        self.tab_panel.default_tab = self.circuits_tab

        # Añadimos el layout principal a la pantalla
        self.add_widget(main_layout)

    def on_pre_enter(self, *args):
        """
        Cada vez que entramos a esta pantalla (ConfigScreen), repoblamos la lista
        de usuarios por si 'GameScreen' o cualquier otra parte los cambió.
        """
        if self.users_tab and self.user_list_layout:
            self.populate_user_fields()

    # -------------------------------------------------------------------------
    # PESTAÑA: CIRCUITOS
    # -------------------------------------------------------------------------
    def build_circuits_config_layout(self):
        """
        Crea un layout con un ScrollView para los circuitos, y los botones de control.
        """
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        
        layout.add_widget(Label(text="Configuración de Circuitos", font_size="24sp", size_hint=(1, 0.1)))

        # Scroll para la lista de circuitos
        scroll_circuits = ScrollView(size_hint=(1, 0.5))
        
        # GridLayout scrolleable
        self.circuit_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.circuit_grid.bind(minimum_height=self.circuit_grid.setter('height'))

        for circuit in config.CIRCUITS:
            btn = Button(
                text=f"{circuit['id']}: {circuit['name']}",
                size_hint_y=None,
                height=40,
                background_color=[1,1,1,1]
            )
            btn.bind(on_release=self.toggle_circuit)
            self.circuit_grid.add_widget(btn)

        scroll_circuits.add_widget(self.circuit_grid)
        layout.add_widget(scroll_circuits)

        btn_iniciar = Button(text="INICIAR", size_hint=(1, 0.1))
        btn_iniciar.bind(on_release=self.iniciar_config)
        layout.add_widget(btn_iniciar)

        action_box = BoxLayout(orientation="horizontal", spacing=10, size_hint=(1, 0.1))
        btn_reiniciar = Button(text="Reiniciar Todos")
        btn_desactivar = Button(text="Desactivar Todos")
        btn_reiniciar.bind(on_release=self.reiniciar_todos)
        btn_desactivar.bind(on_release=self.desactivar_todos)
        action_box.add_widget(btn_reiniciar)
        action_box.add_widget(btn_desactivar)
        layout.add_widget(action_box)

        return layout

    def toggle_circuit(self, instance):
        circuit_id = instance.text.split(":")[0].strip()
        if instance.background_color == [1, 1, 1, 1]:
            instance.background_color = [0, 1, 0, 1]  # verde seleccionado
            self.selected_circuits.add(circuit_id)
        else:
            instance.background_color = [1, 1, 1, 1]
            self.selected_circuits.discard(circuit_id)

    def iniciar_config(self, instance):
        from limbx import update_active_circuits
        update_active_circuits(list(self.selected_circuits))

    def reiniciar_todos(self, instance):
        from logic import circuits
        for circuit in circuits:
            if circuit.state not in ["waiting", "disabled"]:
                circuit.restart()
        print("Se han reiniciado todos los circuitos activos.")

    def desactivar_todos(self, instance):
        from logic import circuits
        for circuit in circuits:
            if circuit.state != "disabled":
                circuit.deactivate()
        print("Se han desactivado todos los circuitos activos.")

    # -------------------------------------------------------------------------
    # PESTAÑA: USUARIOS
    # -------------------------------------------------------------------------
    def build_users_config_layout(self):
        container = BoxLayout(orientation='vertical', spacing=10, padding=10)
        container.add_widget(Label(text="Configuración de Usuarios", font_size="24sp", size_hint=(1, 0.1)))

        self.user_list_layout = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, None))
        self.user_list_layout.bind(minimum_height=self.user_list_layout.setter('height'))

        scroll_users = ScrollView(size_hint=(1, 0.7))
        scroll_users.add_widget(self.user_list_layout)
        container.add_widget(scroll_users)

        self.populate_user_fields()

        btn_box = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.1))
        btn_add = Button(text="Añadir usuario")
        btn_add.bind(on_release=self.add_user_entry)

        btn_save = Button(text="Guardar")
        btn_save.bind(on_release=self.save_users)

        btn_box.add_widget(btn_add)
        btn_box.add_widget(btn_save)
        container.add_widget(btn_box)

        return container

    def populate_user_fields(self):
        if not self.user_list_layout:
            return
        self.user_textinputs.clear()
        self.user_list_layout.clear_widgets()

        for user in config.USER_LIST:
            row = self.build_user_row(user)
            self.user_list_layout.add_widget(row)

    def build_user_row(self, user_name):
        row_layout = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=None, height=40)
        txt = TextInput(text=user_name, multiline=False)
        row_layout.add_widget(txt)
        self.user_textinputs.append(txt)
        return row_layout

    def add_user_entry(self, instance):
        row = self.build_user_row("")
        self.user_list_layout.add_widget(row)

    def save_users(self, instance):
        new_users = []
        for txt in self.user_textinputs:
            name = txt.text.strip()
            if name:
                new_users.append(name)
        config.USER_LIST = new_users
        print("Lista de usuarios actualizada:", config.USER_LIST)
