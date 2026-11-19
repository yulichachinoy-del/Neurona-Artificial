import flet as ft
import config
from ui.theme import Theme

class Sidebar(ft.Container):
    def __init__(self, on_recalibrar, has_serial: bool):
        super().__init__(
            width=270,
            bgcolor=Theme.PANEL,
            padding=18,
            border_radius=16,
        )
        self.content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                # Cabecera Lateral
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.PSYCHOLOGY, color=Theme.AZUL, size=32),
                        ft.Column(
                            spacing=1,
                            controls=[
                                ft.Text("NEURONA ARTIFICIAL", size=14, weight=ft.FontWeight.BOLD, color=Theme.TEXTO),
                                ft.Text("Proyecto ESP32 MicroPython", size=11, color=Theme.TEXTO_SEC)
                            ]
                        )
                    ]
                ),
                ft.Divider(color=Theme.BORDE, height=1),

                # Tarjeta de Fórmula Matemática
                ft.Container(
                    bgcolor=Theme.FONDO,
                    padding=12,
                    border_radius=10,
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text("MODELO MATEMÁTICO", size=11, weight=ft.FontWeight.BOLD, color=Theme.AZUL),
                            ft.Text("z = x1·Wluz + x2·Wson + b", size=12, weight=ft.FontWeight.BOLD, color=Theme.TEXTO),
                            ft.Text("Alerta activa cuando z ≥ 0", size=11, color=Theme.TEXTO_SEC),
                        ]
                    )
                ),

                # Hiperparámetros
                ft.Text("HIPERPARÁMETROS", size=11, weight=ft.FontWeight.BOLD, color=Theme.TEXTO_SEC),
                self._crear_fila("Peso Luz (W_luz)", f"{config.PESO_LUZ:.1f}", Theme.AMARILLO),
                self._crear_fila("Peso Sonido (W_son)", f"{config.PESO_SONIDO:.1f}", Theme.AZUL),
                self._crear_fila("Sesgo (b)", f"{config.SESGO:.1f}", Theme.MORADO),
                self._crear_fila("Muestras ON (alerta)", f"{config.MUESTRAS_ON}", Theme.ROJO),
                self._crear_fila("Muestras OFF (normal)", f"{config.MUESTRAS_OFF}", Theme.VERDE),

                ft.Divider(color=Theme.BORDE, height=1),

                # Mapeo de Hardware
                ft.Text("HARDWARE & PINES", size=11, weight=ft.FontWeight.BOLD, color=Theme.TEXTO_SEC),
                self._crear_fila("LDR (Luz)", f"GPIO {config.PIN_LDR}"),
                self._crear_fila("Micrófono", f"GPIO {config.PIN_MICROFONO}"),
                self._crear_fila("Pulsador Calibrar", f"GPIO {config.PIN_BOTON}"),
                self._crear_fila("LED Verde (Sonido)", f"GPIO {config.PIN_LED_VERDE}"),
                self._crear_fila("LED Rojo (Luz/Alerta)", f"GPIO {config.PIN_LED_ROJO}"),
                self._crear_fila("Sirena (Buzzers)", f"G{config.PIN_BUZZER_AGUDO}/G{config.PIN_BUZZER_GRAVE}"),
                self._crear_fila("LCD I2C (SDA/SCL)", f"G{config.PIN_SDA}/G{config.PIN_SCL}"),

                ft.Divider(color=Theme.BORDE, height=1),

                # Botón de Recalibración
                ft.FilledButton(
                    "Pulsador Recalibrar",
                    icon=ft.Icons.REFRESH,
                    on_click=on_recalibrar
                ),

                # Estado de Comunicación
                ft.Container(
                    bgcolor=Theme.FONDO,
                    padding=10,
                    border_radius=8,
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.TERMINAL, size=16, color=Theme.VERDE if has_serial else Theme.TEXTO_SEC),
                            ft.Text(
                                "Modo: Simulación Activa" if not has_serial else "Serial: Disponible",
                                size=11,
                                color=Theme.TEXTO_SEC
                            )
                        ]
                    )
                )
            ]
        )

    def _crear_fila(self, nombre: str, valor: str, color: str = Theme.TEXTO):
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(nombre, size=12, color=Theme.TEXTO_SEC),
                ft.Container(
                    content=ft.Text(str(valor), size=12, weight=ft.FontWeight.BOLD, color=color),
                    bgcolor=Theme.PANEL_SEC,
                    padding=ft.Padding(8, 2, 8, 2),
                    border_radius=6
                )
            ]
        )