import flet as ft
import config
from ui.theme import Theme


class Sidebar(ft.Container):
    def __init__(self, neurona, on_parametros_cambiados, on_recalibrar, has_serial: bool):
        super().__init__(
            width=280,
            bgcolor=Theme.PANEL,
            padding=16,
            border_radius=16,
        )
        self.neurona = neurona
        self.on_parametros_cambiados = on_parametros_cambiados
        self.seccion_activa = None

        # --- Controles dinámicos para Pesos y Sesgo ---
        self.lbl_wluz = ft.Text(f"{self._get_param('peso_luz', config.PESO_LUZ):.1f}", size=12, weight=ft.FontWeight.BOLD, color=Theme.AMARILLO)
        self.slider_wluz = ft.Slider(
            min=0.0, max=10.0, divisions=100,
            value=self._get_param("peso_luz", config.PESO_LUZ),
            active_color=Theme.AMARILLO,
            on_change=self._actualizar_pesos
        )

        self.lbl_wson = ft.Text(f"{self._get_param('peso_sonido', config.PESO_SONIDO):.1f}", size=12, weight=ft.FontWeight.BOLD, color=Theme.AZUL)
        self.slider_wson = ft.Slider(
            min=0.0, max=10.0, divisions=100,
            value=self._get_param("peso_sonido", config.PESO_SONIDO),
            active_color=Theme.AZUL,
            on_change=self._actualizar_pesos
        )

        self.lbl_sesgo = ft.Text(f"{self._get_param('sesgo', config.SESGO):.1f}", size=12, weight=ft.FontWeight.BOLD, color=Theme.MORADO)
        self.slider_sesgo = ft.Slider(
            min=-10.0, max=0.0, divisions=100,
            value=self._get_param("sesgo", config.SESGO),
            active_color=Theme.MORADO,
            on_change=self._actualizar_pesos
        )

        # --- Controles dinámicos para Histéresis ---
        self.lbl_mon = ft.Text(f"{config.MUESTRAS_ON}", size=12, weight=ft.FontWeight.BOLD, color=Theme.ROJO)
        self.slider_mon = ft.Slider(
            min=1, max=10, divisions=9,
            value=config.MUESTRAS_ON,
            active_color=Theme.ROJO,
            on_change=self._actualizar_histeresis
        )

        self.lbl_moff = ft.Text(f"{config.MUESTRAS_OFF}", size=12, weight=ft.FontWeight.BOLD, color=Theme.VERDE)
        self.slider_moff = ft.Slider(
            min=1, max=10, divisions=9,
            value=config.MUESTRAS_OFF,
            active_color=Theme.VERDE,
            on_change=self._actualizar_histeresis
        )

        # --- Definición de las secciones desplegables ---
        self.paneles_detalle = {
            "pesos": ft.Container(
                visible=False,
                bgcolor=Theme.FONDO,
                padding=12,
                border_radius=12,
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Row([ft.Text("Peso Luz (W_luz)", size=11, color=Theme.TEXTO_SEC), self.lbl_wluz], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        self.slider_wluz,
                        ft.Row([ft.Text("Peso Sonido (W_son)", size=11, color=Theme.TEXTO_SEC), self.lbl_wson], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        self.slider_wson,
                        ft.Row([ft.Text("Sesgo (b)", size=11, color=Theme.TEXTO_SEC), self.lbl_sesgo], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        self.slider_sesgo,
                        ft.TextButton("Restaurar originales", icon=ft.Icons.RESTORE, on_click=self._restaurar_pesos)
                    ]
                )
            ),
            "histeresis": ft.Container(
                visible=False,
                bgcolor=Theme.FONDO,
                padding=12,
                border_radius=12,
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Row([ft.Text("Muestras ON (Alerta)", size=11, color=Theme.TEXTO_SEC), self.lbl_mon], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        self.slider_mon,
                        ft.Row([ft.Text("Muestras OFF (Normal)", size=11, color=Theme.TEXTO_SEC), self.lbl_moff], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        self.slider_moff,
                    ]
                )
            ),
            "modelo": ft.Container(
                visible=False,
                bgcolor=Theme.FONDO,
                padding=12,
                border_radius=12,
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text("z = x1·Wluz + x2·Wson + b", size=12, weight=ft.FontWeight.BOLD, color=Theme.AZUL),
                        ft.Text("• x1, x2: Entradas normalizadas [0, 1]", size=11, color=Theme.TEXTO_SEC),
                        ft.Text("• Umbral: Alerta activa si z ≥ 0", size=11, color=Theme.TEXTO_SEC),
                    ]
                )
            ),
            "hardware": ft.Container(
                visible=False,
                bgcolor=Theme.FONDO,
                padding=12,
                border_radius=12,
                content=ft.Column(
                    spacing=6,
                    controls=[
                        self._fila_pin("LDR (Luz)", f"GPIO {config.PIN_LDR}"),
                        self._fila_pin("Micrófono", f"GPIO {config.PIN_MICROFONO}"),
                        self._fila_pin("Pulsador", f"GPIO {config.PIN_BOTON}"),
                        self._fila_pin("LED Verde / Rojo", f"G{config.PIN_LED_VERDE} / G{config.PIN_LED_ROJO}"),
                        self._fila_pin("Buzzers", f"G{config.PIN_BUZZER_AGUDO} / G{config.PIN_BUZZER_GRAVE}"),
                        self._fila_pin("LCD I2C", f"G{config.PIN_SDA} / G{config.PIN_SCL}"),
                    ]
                )
            ),
        }

        # --- Ítems estilo lista limpia ---
        self.items_menu = {
            "pesos": self._crear_item_menu("pesos", "Ajustar Pesos y Sesgo", ft.Icons.TUNE, fijado=True),
            "histeresis": self._crear_item_menu("histeresis", "Filtro de Histéresis", ft.Icons.SPEED, fijado=True),
            "modelo": self._crear_item_menu("modelo", "Fórmula Matemática", ft.Icons.FUNCTIONS, fijado=False),
            "hardware": self._crear_item_menu("hardware", "Pines y Hardware ESP32", ft.Icons.MEMORY, fijado=False),
        }

        self.content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=6,
            controls=[
                ft.Container(
                    padding=ft.Padding(8, 4, 8, 8),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.PSYCHOLOGY, color=Theme.AZUL, size=22),
                                    ft.Text("Configuración", size=14, weight=ft.FontWeight.BOLD, color=Theme.TEXTO),
                                ]
                            ),
                            ft.Icon(ft.Icons.FILTER_LIST, size=18, color=Theme.TEXTO_SEC)
                        ]
                    )
                ),
                self.items_menu["pesos"],
                self.paneles_detalle["pesos"],
                self.items_menu["histeresis"],
                self.paneles_detalle["histeresis"],
                self.items_menu["modelo"],
                self.paneles_detalle["modelo"],
                self.items_menu["hardware"],
                self.paneles_detalle["hardware"],
                ft.Divider(color=Theme.BORDE, height=16),
                ft.Container(
                    border_radius=20,
                    padding=ft.Padding(14, 10, 14, 10),
                    ink=True,
                    on_click=on_recalibrar,
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.REFRESH, size=18, color=Theme.AZUL),
                            ft.Text("Recalibrar Neurona", size=13, color=Theme.TEXTO)
                        ]
                    )
                ),
                ft.Container(
                    border_radius=20,
                    padding=ft.Padding(14, 8, 14, 8),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.CIRCLE, size=10, color=Theme.VERDE if has_serial else Theme.AMARILLO),
                            ft.Text("Serial Listo" if has_serial else "Modo Simulación", size=12, color=Theme.TEXTO_SEC)
                        ]
                    )
                )
            ]
        )

    def _crear_item_menu(self, clave: str, titulo: str, icono, fijado: bool = False):
        return ft.Container(
            border_radius=22,
            padding=ft.Padding(14, 10, 14, 10),
            bgcolor="transparent",
            ink=True,
            on_click=lambda e: self._toggle_seccion(clave),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=10,
                        expand=True,
                        controls=[
                            ft.Icon(icono, size=17, color=Theme.TEXTO_SEC),
                            ft.Text(
                                titulo,
                                size=13,
                                color=Theme.TEXTO,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True
                            ),
                        ]
                    ),
                    ft.Icon(ft.Icons.PUSH_PIN_OUTLINED, size=15, color=Theme.TEXTO_SEC) if fijado else ft.Container()
                ]
            )
        )

    def _toggle_seccion(self, clave: str):
        self.seccion_activa = None if self.seccion_activa == clave else clave

        for k, item in self.items_menu.items():
            activo = (k == self.seccion_activa)
            item.bgcolor = Theme.PANEL_SEC if activo else "transparent"
            fila_izq = item.content.controls[0]
            fila_izq.controls[0].color = Theme.TEXTO if activo else Theme.TEXTO_SEC
            fila_izq.controls[1].weight = ft.FontWeight.BOLD if activo else ft.FontWeight.NORMAL
            self.paneles_detalle[k].visible = activo

        self.update()

    def _get_param(self, attr_neurona: str, fallback):
        return getattr(self.neurona, attr_neurona, fallback)

    def _actualizar_pesos(self, e):
        wl = round(self.slider_wluz.value, 1)
        ws = round(self.slider_wson.value, 1)
        b = round(self.slider_sesgo.value, 1)

        self.lbl_wluz.value = f"{wl:.1f}"
        self.lbl_wson.value = f"{ws:.1f}"
        self.lbl_sesgo.value = f"{b:.1f}"

        config.PESO_LUZ = wl
        config.PESO_SONIDO = ws
        config.SESGO = b
        if hasattr(self.neurona, "peso_luz"):
            self.neurona.peso_luz = wl
        if hasattr(self.neurona, "peso_sonido"):
            self.neurona.peso_sonido = ws
        if hasattr(self.neurona, "sesgo"):
            self.neurona.sesgo = b

        self.on_parametros_cambiados()

    def _restaurar_pesos(self, e):
        self.slider_wluz.value = 5.0
        self.slider_wson.value = 5.0
        self.slider_sesgo.value = -6.0
        self._actualizar_pesos(e)
        self.update()

    def _actualizar_histeresis(self, e):
        mon = int(self.slider_mon.value)
        moff = int(self.slider_moff.value)
        self.lbl_mon.value = str(mon)
        self.lbl_moff.value = str(moff)

        config.MUESTRAS_ON = mon
        config.MUESTRAS_OFF = moff
        if hasattr(self.neurona, "muestras_on"):
            self.neurona.muestras_on = mon
        if hasattr(self.neurona, "muestras_off"):
            self.neurona.muestras_off = moff

        self.on_parametros_cambiados()

    def _fila_pin(self, nombre: str, pin: str):
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(nombre, size=11, color=Theme.TEXTO_SEC),
                ft.Text(pin, size=11, weight=ft.FontWeight.BOLD, color=Theme.TEXTO),
            ]
        )