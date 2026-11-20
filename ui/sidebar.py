import flet as ft
import serial.tools.list_ports
from ui.theme import Theme


class Sidebar(ft.Container):
    def __init__(
        self,
        on_navegar,
        on_conectar_serial,
        on_refrescar_puertos,
        on_recalibrar_circuito=None,
    ):
        self.on_navegar = on_navegar
        self.on_conectar_serial = on_conectar_serial
        self.on_refrescar_puertos = on_refrescar_puertos
        self.on_recalibrar_circuito = on_recalibrar_circuito
        self.vista_activa = "inicio"

        # --- Botones de Navegación ---
        self.btn_inicio = self._crear_item_nav("inicio", ft.Icons.HOME_ROUNDED, "Inicio", activo=True)
        self.btn_monitoreo = self._crear_item_nav("monitoreo", ft.Icons.DASHBOARD_ROUNDED, "Monitoreo en Vivo")
        self.btn_simulador = self._crear_item_nav("simulador", ft.Icons.DEVELOPER_BOARD_ROUNDED, "Simulador y LCD")
        self.btn_historial = self._crear_item_nav("historial", ft.Icons.HISTORY_ROUNDED, "Historial de Alertas")

        self.botones_nav = {
            "inicio": self.btn_inicio,
            "monitoreo": self.btn_monitoreo,
            "simulador": self.btn_simulador,
            "historial": self.btn_historial,
        }

        # --- Controles de Conexión Serial (USB) ---
        self.dropdown_puertos = ft.Dropdown(
            hint_text="Puerto COM",
            text_size=13,
            height=44,
            expand=True,
            border=ft.OutlineInputBorder(
                border_radius=8,
                side=ft.BorderSide(color=Theme.BORDE),
            ),
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            options=[],
        )

        self.btn_refrescar = ft.IconButton(
            icon=ft.Icons.REFRESH_ROUNDED,
            icon_color=Theme.TEXTO_SEC,
            icon_size=20,
            tooltip="Actualizar puertos COM",
            on_click=self._handle_refrescar_click,
        )

        self.texto_btn_conectar = ft.Text(
            "Conectar",
            size=14,
            weight=ft.FontWeight.W_600,
            color="#0F172A",
        )

        self.btn_conectar = ft.Button(
            content=self.texto_btn_conectar,
            height=42,
            width=float("inf"),
            bgcolor=Theme.AZUL,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=21),
            ),
            on_click=self._handle_conectar_click,
        )

        self.btn_recalibrar = ft.OutlinedButton(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.TUNE_ROUNDED, size=16, color=Theme.TEXTO),
                    ft.Text("Recalibrar Circuito", size=12, color=Theme.TEXTO),
                ],
            ),
            height=38,
            width=float("inf"),
            on_click=self.on_recalibrar_circuito,
        )

        self.indicador_punto = ft.Container(
            width=10,
            height=10,
            border_radius=5,
            bgcolor=Theme.TEXTO_SEC,
        )

        self.texto_estado = ft.Text(
            "Desconectado",
            size=12,
            color=Theme.TEXTO_SEC,
            expand=True,
        )

        # Detectar puertos inmediatamente al construir la barra lateral
        self.actualizar_puertos()

        super().__init__(
            width=260,
            bgcolor=Theme.PANEL,
            border=ft.Border.all(1, Theme.BORDE),
            border_radius=16,
            padding=20,
            content=ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    # Parte superior: Logo y Navegación
                    ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                spacing=10,
                                controls=[
                                    ft.Icon(ft.Icons.PSYCHOLOGY_ROUNDED, color=Theme.AZUL, size=28),
                                    ft.Text(
                                        "Neurona ESP32",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=Theme.TEXTO,
                                    ),
                                ],
                            ),
                            ft.Container(height=16),
                            self.btn_inicio,
                            self.btn_monitoreo,
                            self.btn_simulador,
                            self.btn_historial,
                        ],
                    ),
                    # Parte inferior: Conexión USB
                    ft.Column(
                        spacing=10,
                        controls=[
                            ft.Divider(color=Theme.BORDE, height=1),
                            ft.Text(
                                "CONEXIÓN CIRCUITO (USB)",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=Theme.TEXTO_SEC,
                            ),
                            ft.Row(
                                spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[self.dropdown_puertos, self.btn_refrescar],
                            ),
                            self.btn_conectar,
                            self.btn_recalibrar,
                            ft.Row(
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[self.indicador_punto, self.texto_estado],
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _crear_item_nav(self, vista_id: str, icono, texto: str, activo: bool = False):
        color_texto = Theme.TEXTO if activo else Theme.TEXTO_SEC
        return ft.Container(
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(icono, size=20, color=color_texto),
                    ft.Text(texto, size=14, weight=ft.FontWeight.W_500, color=color_texto),
                ],
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            border_radius=24,
            bgcolor=Theme.PANEL_SEC if activo else ft.Colors.TRANSPARENT,
            ink=True,
            on_click=lambda e: self.seleccionar(vista_id),
        )

    def seleccionar(self, vista_id: str):
        self.vista_activa = vista_id
        for vid, btn in self.botones_nav.items():
            activo = vid == vista_id
            btn.bgcolor = Theme.PANEL_SEC if activo else ft.Colors.TRANSPARENT
            color_texto = Theme.TEXTO if activo else Theme.TEXTO_SEC
            btn.content.controls[0].color = color_texto
            btn.content.controls[1].color = color_texto
            try:
                btn.update()
            except Exception:
                pass
        if callable(self.on_navegar):
            self.on_navegar(vista_id)

    def actualizar_puertos(self, puertos=None):
        lista_limpia = []
        if puertos:
            for p in puertos:
                # Extraer "COM6" incluso si viene en formato "COM6 - CP210x..."
                nombre = str(p).split(" - ")[0].split(" ")[0].strip()
                if nombre:
                    lista_limpia.append(nombre)

        # Si el serial_manager devolvió vacío, leer directamente los puertos de Windows
        if not lista_limpia:
            lista_limpia = [p.device for p in serial.tools.list_ports.comports()]

        self.dropdown_puertos.options = [
            ft.dropdown.Option(key=p, text=p) for p in lista_limpia
        ]

        if lista_limpia:
            if "COM6" in lista_limpia:
                self.dropdown_puertos.value = "COM6"
            elif self.dropdown_puertos.value not in lista_limpia:
                self.dropdown_puertos.value = lista_limpia[0]
        else:
            self.dropdown_puertos.value = None

        try:
            self.dropdown_puertos.update()
        except Exception:
            pass

    def _handle_refrescar_click(self, e):
        self.actualizar_puertos()
        if callable(self.on_refrescar_puertos):
            self.on_refrescar_puertos(e)

    def _handle_conectar_click(self, e):
        puerto = self.dropdown_puertos.value
        if not puerto:
            self.texto_estado.value = "Selecciona un puerto"
            self.texto_estado.color = Theme.ROJO
            try:
                self.texto_estado.update()
            except Exception:
                pass
            return

        if callable(self.on_conectar_serial):
            self.on_conectar_serial(puerto)

    def actualizar_estado_serial(self, conectado: bool, mensaje: str = ""):
        if conectado:
            self.texto_btn_conectar.value = "Desconectar"
            self.texto_btn_conectar.color = "#450A0A"
            self.btn_conectar.bgcolor = Theme.ROJO
            self.indicador_punto.bgcolor = Theme.VERDE
            self.texto_estado.value = mensaje if mensaje else "Conectado"
            self.texto_estado.color = Theme.VERDE
        else:
            self.texto_btn_conectar.value = "Conectar"
            self.texto_btn_conectar.color = "#0F172A"
            self.btn_conectar.bgcolor = Theme.AZUL
            self.indicador_punto.bgcolor = Theme.TEXTO_SEC
            self.texto_estado.value = mensaje if mensaje else "Desconectado"
            self.texto_estado.color = Theme.TEXTO_SEC

        try:
            self.btn_conectar.update()
            self.indicador_punto.update()
            self.texto_estado.update()
        except Exception:
            pass