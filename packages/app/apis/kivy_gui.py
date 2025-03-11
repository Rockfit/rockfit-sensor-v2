import kivy
kivy.require('2.1.0')  # Se recomienda Kivy >= 2.1.0

import time
import datetime

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, Line
from kivy.core.window import Window
from kivy.clock import Clock

# Colores cíclicos para el "bullet" de cada jugador
PLAYER_COLORS = [
    (1, 0, 0, 1),   # rojo
    (0, 1, 0, 1),   # verde
    (0, 0, 1, 1),   # azul
    (1, 1, 0, 1)    # amarillo
]

# ===============================================================
# DropZoneBoxLayout: zona de drop para jugadores.
# ===============================================================
class DropZoneBoxLayout(BoxLayout):
    def __init__(self, is_quadrant=False, **kwargs):
        super().__init__(**kwargs)
        self.is_quadrant = is_quadrant
        with self.canvas.before:
            if self.is_quadrant:
                Color(0.2, 0.2, 0.2, 1)
            else:
                Color(0.1, 0.1, 0.1, 1)
            self.bg_rect = Rectangle()
        self.bind(pos=self._update_bg, size=self._update_bg)
        
    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

# ===============================================================
# DraggablePlayer: widget de jugador con dos filas:
# - La fila superior contiene el botón bullet y el nombre.
# - La fila inferior (oculta por defecto) mostrará los resultados
#   cuando se asigne a un circuito.
#
# Se gestiona manualmente el touch para:
#   • Si se toca el botón bullet, se cambia el color.
#   • Si se toca el nombre (sin arrastrar), se abre un pop-up de edición.
#   • Si se hace doble click (sin arrastrar), se devuelve al banquillo.
#   • Si se arrastra, se mueve al contenedor flotante para asegurar su visibilidad.
# ===============================================================
class DraggablePlayer(BoxLayout):
    def __init__(self, name, color_index=0, **kwargs):
        # Configuramos como vertical; altura total 80 (40 para cada fila)
        super().__init__(orientation='vertical', size_hint=(None, None), width=180, height=80, **kwargs)
        self.name = name
        self.color_index = color_index
        
        # Variables para gestionar el toque y el arrastre
        self._dragging = False
        self._drag_offset = (0, 0)
        self._original_parent = None
        self._original_index = None
        self._original_pos = (0, 0)
        self._touch_down_pos = (0, 0)
        self._popup_event = None
        self._last_touch_time = 0  # Para detectar doble click

        with self.canvas.before:
            Color(0.25, 0.25, 0.25, 1)
            self.bg_rect = Rectangle()
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # Fila superior: bullet y nombre
        self.top_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40, spacing=5, padding=5)
        self.bullet_btn = Button(size_hint=(None, 1), width=30, background_normal='',
                                 on_release=self._cycle_color)
        self._set_bullet_color(self.color_index)
        self.name_label = Label(text=self.name, color=(1,1,1,1), halign='left', valign='middle')
        self.name_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        # Vincular touch en el label para abrir el pop-up (consumiendo el evento)
        self.name_label.bind(on_touch_down=self._on_name_touch_down)
        self.top_row.add_widget(self.bullet_btn)
        self.top_row.add_widget(self.name_label)
        
        # Fila inferior: campo para resultados (oculto inicialmente: altura 0)
        self.bottom_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=0, padding=5)
        self.result_label = Label(text="", color=(1,1,1,1), halign='left', valign='middle')
        self.result_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        self.bottom_row.add_widget(self.result_label)
        
        # Agregar las dos filas al widget
        self.add_widget(self.top_row)
        self.add_widget(self.bottom_row)
    
    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        
    def _set_bullet_color(self, idx):
        self.color_index = idx % len(PLAYER_COLORS)
        self.bullet_btn.background_color = PLAYER_COLORS[self.color_index]
        
    def _cycle_color(self, *args):
        # Al pulsar el bullet se cambia el color.
        self._set_bullet_color(self.color_index + 1)
    
    # ---------------------------------------------------------------
    # Popup de edición: se abre al tocar el nombre.
    # ---------------------------------------------------------------
    def _on_name_touch_down(self, instance, touch):
        if instance.collide_point(*touch.pos) and touch.button == 'left':
            self._touch_down_pos = (touch.x, touch.y)
            # Programar el popup para que se abra tras 0.3 s si no se detecta movimiento
            self._popup_event = Clock.schedule_once(lambda dt: self.open_edit_popup(), 0.3)
            return True
        return False

    def open_edit_popup(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        title_lbl = Label(text="Editar datos del jugador", size_hint_y=None, height=30)
        name_lbl = Label(text="Nombre:", size_hint_y=None, height=20)
        name_input = TextInput(text=self.name, multiline=False)
        # Cuatro campos para resultados (inicialmente en blanco)
        results_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=140, spacing=5)
        for i in range(1, 5):
            lbl = Label(text=f"Resultados en circuito {i}:", size_hint_y=None, height=30)
            results_layout.add_widget(lbl)
        buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        btn_save = Button(text="Guardar")
        btn_cancel = Button(text="Cancelar")
        buttons.add_widget(btn_save)
        buttons.add_widget(btn_cancel)
        
        content.add_widget(title_lbl)
        content.add_widget(name_lbl)
        content.add_widget(name_input)
        content.add_widget(results_layout)
        content.add_widget(buttons)
        
        popup = Popup(title="Editar jugador", content=content, size_hint=(None, None), size=(400, 400))
        btn_save.bind(on_release=lambda inst: self._save_popup(name_input.text, popup))
        btn_cancel.bind(on_release=lambda inst: popup.dismiss())
        popup.open()
    
    def _save_popup(self, new_name, popup):
        self.name = new_name
        self.name_label.text = new_name
        popup.dismiss()
    
    # ---------------------------------------------------------------
    # Método para devolver el jugador al banquillo (por doble click).
    # ---------------------------------------------------------------
    def return_to_banquillo(self):
        app = App.get_running_app()
        if self.parent:
            self.parent.remove_widget(self)
        bench = app.banquillo_zone
        bench.add_widget(self)
        self.size_hint_x = None
        self.width = 180
        self.result_label.text = ""
        self.bottom_row.height = 0
        self.bottom_row.opacity = 0
        self.pos = (0, 0)
    
    # ---------------------------------------------------------------
    # Manejo manual de arrastre: on_touch_down, on_touch_move, on_touch_up.
    # ---------------------------------------------------------------
    def on_touch_down(self, touch):
        # Si el touch ocurre sobre el botón bullet, dejar que éste lo gestione.
        if self.bullet_btn.collide_point(*touch.pos) and touch.button == 'left':
            return super().on_touch_down(touch)
        # Si el touch ocurre sobre el nombre, se gestiona en _on_name_touch_down.
        if self.collide_point(*touch.pos) and touch.button == 'left':
            # Detectar doble click para devolver al banquillo
            current_time = time.time()
            if current_time - self._last_touch_time < 0.3:
                self.return_to_banquillo()
                self._last_touch_time = 0
                return True
            self._last_touch_time = current_time
            self._touch_down_pos = (touch.x, touch.y)
            # Si el touch no es sobre el name_label (o se cancela el popup), iniciar arrastre.
            if not self.name_label.collide_point(*touch.pos):
                if self._popup_event:
                    self._popup_event.cancel()
                    self._popup_event = None
                self._start_drag(touch)
                return True
        return super().on_touch_down(touch)
    
    def _start_drag(self, touch):
        self._dragging = True
        self._original_parent = self.parent
        self._original_index = self.parent.children.index(self)
        self._original_pos = self.pos
        self._drag_offset = (self.x - touch.x, self.y - touch.y)
        # Re-parentar al contenedor flotante para que quede por encima
        app = App.get_running_app()
        float_root = app.float_root
        if self.parent:
            self.parent.remove_widget(self)
        float_root.add_widget(self)
        self.x = touch.x + self._drag_offset[0]
        self.y = touch.y + self._drag_offset[1]
    
    def on_touch_move(self, touch):
        # Si se programó un popup y se detecta movimiento mayor que el umbral, cancelarlo e iniciar arrastre.
        if self._popup_event and not self._dragging:
            dx = touch.x - self._touch_down_pos[0]
            dy = touch.y - self._touch_down_pos[1]
            if dx*dx + dy*dy > 25:
                self._popup_event.cancel()
                self._popup_event = None
                self._start_drag(touch)
                return True
        if self._dragging and touch.button == 'left':
            self.x = touch.x + self._drag_offset[0]
            self.y = touch.y + self._drag_offset[1]
            return True
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        # Si se programó un popup y no se inició arrastre, abrir el popup.
        if self._popup_event and not self._dragging:
            self._popup_event.cancel()
            self._popup_event = None
            self.open_edit_popup()
            return True
        if self._dragging and touch.button == 'left':
            self._dragging = False
            app = App.get_running_app()
            dropped = False
            for dz in app.drop_zones:
                if dz.collide_point(touch.x, touch.y):
                    if self.parent is not dz:
                        if self.parent:
                            self.parent.remove_widget(self)
                    # Agregar en la dropzone y usar el orden de hijos para asignar color
                    order_idx = len(dz.children)
                    dz.add_widget(self, index=order_idx)
                    if dz.is_quadrant:
                        # En circuito: ocupar ancho completo y asignar color según orden
                        self.size_hint_x = 1
                        self._set_bullet_color(order_idx)
                        circuit_num = dz.circuit_number if hasattr(dz, 'circuit_number') else "?"
                        now = datetime.datetime.now().strftime("%H:%M:%S")
                        self.result_label.text = f"{now} - resultado en el circuito {circuit_num} sin generar"
                        self.bottom_row.height = 40
                        self.bottom_row.opacity = 1
                    else:
                        # En banquillo: ancho fijo y sin resultados
                        self.size_hint_x = None
                        self.width = 180
                        self.result_label.text = ""
                        self.bottom_row.height = 0
                        self.bottom_row.opacity = 0
                    self.pos = (0, 0)
                    dropped = True
                    break
            if not dropped:
                # Si no se soltó sobre ninguna zona, regresar al contenedor original.
                if self.parent:
                    self.parent.remove_widget(self)
                if self._original_parent:
                    self._original_parent.add_widget(self, index=self._original_index)
                    self.pos = self._original_pos
            return True
        return super().on_touch_up(touch)

# ===============================================================
# QuadrantsLayout: GridLayout 2x2 con líneas divisorias.
# ===============================================================
class QuadrantsLayout(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rows = 2
        self.cols = 2
        self.spacing = 0
        with self.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.bg_rect = Rectangle()
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.bind(pos=self._draw_lines, size=self._draw_lines)
        
    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        
    def _draw_lines(self, *args):
        self.canvas.after.clear()
        with self.canvas.after:
            Color(1, 1, 1, 0.2)
            # Línea vertical:
            x_line = self.x + self.width / 2
            Line(points=[x_line, self.y, x_line, self.top], width=1)
            # Línea horizontal:
            y_line = self.y + self.height / 2
            Line(points=[self.x, y_line, self.right, y_line], width=1)

# ===============================================================
# RockFitApp: aplicación principal.
# ===============================================================
class RockFitApp(App):
    def build(self):
        Window.maximize()
        # Contenedor flotante raíz para re-parentar jugadores durante el arrastre.
        self.float_root = FloatLayout()
        main_box = BoxLayout(orientation='vertical', size_hint=(1, 1))
        self.float_root.add_widget(main_box)
        
        # Sección superior: banquillo + botón "Iniciar todos"
        top_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=120)
        with top_layout.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.top_bg_rect = Rectangle()
        top_layout.bind(pos=self._update_top_bg, size=self._update_top_bg)
        
        banquillo_scroll = ScrollView(size_hint=(1, None), size=(Window.width, 60),
                                       do_scroll_x=True, do_scroll_y=False)
        self.banquillo_zone = DropZoneBoxLayout(orientation='horizontal', is_quadrant=False, spacing=10, size_hint=(None, 1))
        self.banquillo_zone.bind(minimum_width=self.banquillo_zone.setter('width'))
        banquillo_scroll.add_widget(self.banquillo_zone)
        
        iniciar_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=50)
        iniciar_btn = Button(text="Iniciar todos", size_hint=(None, 1), width=180,
                             font_size=18, background_color=(0.4, 0.2, 0.2, 1), color=(1, 1, 1, 1))
        iniciar_layout.add_widget(BoxLayout(size_hint=(0.5, 1)))
        iniciar_layout.add_widget(iniciar_btn)
        iniciar_layout.add_widget(BoxLayout(size_hint=(0.5, 1)))
        
        top_layout.add_widget(banquillo_scroll)
        top_layout.add_widget(iniciar_layout)
        main_box.add_widget(top_layout)
        
        # Cuadrantes 2x2:
        quads = QuadrantsLayout(size_hint=(1, 1))
        main_box.add_widget(quads)
        
        # Crear 4 cuadrantes; a cada uno se le asigna un número de circuito.
        c1_container, c1_zone = self._create_quadrant("Circuito #1", "Recorrido #1", 1)
        c2_container, c2_zone = self._create_quadrant("Circuito #2", "Recorrido #2", 2)
        c3_container, c3_zone = self._create_quadrant("Circuito #3", "Recorrido #3", 3)
        c4_container, c4_zone = self._create_quadrant("Circuito #4", "Recorrido #4", 4)
        
        quads.add_widget(c1_container)
        quads.add_widget(c2_container)
        quads.add_widget(c3_container)
        quads.add_widget(c4_container)
        
        # Registrar las dropzones:
        self.drop_zones = []
        self.drop_zones.append(self.banquillo_zone)
        self.drop_zones.extend([c1_zone, c2_zone, c3_zone, c4_zone])
        
        # Agregar jugadores de prueba al banquillo:
        jugadores = [
            "Jugador1", "CapitánSupremo", "JugadoraLargaDeNombre",
            "ElConquistador", "PowerPlayer999", "JugadorX",
            "TestTestTestName", "JugadorDePrueba", "Jugador9",
            "PlayerWithLongName", "Jugador11", "Jugador12"
        ]
        for nombre in jugadores:
            dp = DraggablePlayer(name=nombre)
            # En el banquillo, usar ancho fijo:
            dp.size_hint_x = None
            dp.width = 180
            self.banquillo_zone.add_widget(dp)
        
        return self.float_root
    
    def _update_top_bg(self, instance, _):
        self.top_bg_rect.pos = instance.pos
        self.top_bg_rect.size = instance.size
    
    def _create_quadrant(self, title, desc, circuit_number):
        """
        Retorna (container, players_zone):
         - container: BoxLayout vertical con título, descripción, botón "Iniciar Circuito" y zona de drop.
         - players_zone: DropZoneBoxLayout vertical con atributo circuit_number.
        """
        container = BoxLayout(orientation='vertical', padding=10, spacing=5)
        with container.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            rect = Rectangle()
        container.bind(pos=lambda *a: self._update_rect(container, rect),
                       size=lambda *a: self._update_rect(container, rect))
        
        lbl_title = Label(text=title, font_size=20, color=(1, 1, 1, 1),
                          size_hint=(1, None), height=30,
                          halign='center', valign='middle')
        lbl_title.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        
        lbl_desc = Label(text=desc, font_size=14, color=(1, 1, 1, 1),
                         size_hint=(1, None), height=20,
                         halign='center', valign='middle')
        lbl_desc.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        
        btn_iniciar = Button(text="Iniciar Circuito",
                             size_hint=(1, None), height=40,
                             background_color=(0.3, 0.4, 0.7, 1),
                             color=(1, 1, 1, 1), font_size=16)
        
        players_zone = DropZoneBoxLayout(orientation='vertical', is_quadrant=True, spacing=5, padding=5)
        players_zone.circuit_number = circuit_number
        
        container.add_widget(lbl_title)
        container.add_widget(lbl_desc)
        container.add_widget(btn_iniciar)
        container.add_widget(players_zone)
        
        return container, players_zone
    
    def _update_rect(self, layout, rect):
        rect.pos = layout.pos
        rect.size = layout.size

if __name__ == '__main__':
    RockFitApp().run()

