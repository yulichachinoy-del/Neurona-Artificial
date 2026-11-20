import flet as ft
from ui.theme import Theme


class WelcomeView(ft.Container):
    def __init__(self, on_ir_monitoreo, on_ir_simulador):
        super().__init__(
            expand=True,
            alignment=ft.Alignment(0, 0),
            padding=30,
        )
        self.content = ft.Container(
            width=760,
            bgcolor=Theme.PANEL,
            padding=36,
            border_radius=20,
            border=ft.Border.all(1, Theme.BORDE),
            content=ft.Column(
                spacing=20,
                tight=True,
                controls=[
                    ft.Row(
                        spacing=14,
                        controls=[
                            ft.Container(
                                bgcolor=Theme.FONDO,
                                padding=14,
                                border_radius=14,
                                content=ft.Icon(ft.Icons.PSYCHOLOGY, color=Theme.AZUL, size=36),
                            ),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Neurona Artificial — ESP32", size=24, weight=ft.FontWeight.BOLD, color=Theme.TEXTO),
                                    ft.Text("Sistema Embebido de Percepción Sensorial", size=13, color=Theme.AZUL),
                                ],
                            ),
                        ],
                    ),
                    ft.Divider(color=Theme.BORDE),
                    ft.Text(
                        "Firmware en MicroPython que lee un sensor de luz y un micrófono, evalúa sus señales "
                        "con una neurona artificial y controla indicadores, una alarma y una pantalla LCD. "
                        "La versión actual funciona localmente: no requiere conexión Wi-Fi ni comunicación MQTT.",
                        size=15,
                        color=Theme.TEXTO,
                        height=1.5,
                    ),
                    ft.Row(
                        spacing=12,
                        controls=[
                            self._chip(ft.Icons.LIGHT_MODE, "Sensor de Luz (LDR)", Theme.AMARILLO),
                            self._chip(ft.Icons.MIC, "Micrófono Ambiental", Theme.AZUL),
                            self._chip(ft.Icons.USB, "Comunicación Serial Local", Theme.VERDE),
                        ],
                    ),
                    ft.Container(height=6),
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.FilledButton(
                                "Ver Monitoreo en Vivo",
                                icon=ft.Icons.DASHBOARD,
                                on_click=lambda e: on_ir_monitoreo(),
                            ),
                            ft.OutlinedButton(
                                "Abrir Simulador y LCD",
                                icon=ft.Icons.TUNE,
                                on_click=lambda e: on_ir_simulador(),
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _chip(self, icono, texto: str, color: str):
        return ft.Container(
            bgcolor=Theme.FONDO,
            padding=ft.Padding(12, 8, 12, 8),
            border_radius=10,
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(icono, size=16, color=color),
                    ft.Text(texto, size=12, color=Theme.TEXTO_SEC),
                ],
            ),
        )