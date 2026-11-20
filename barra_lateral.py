import flet as ft

import config
from tema import (
    FONDO, PANEL, PANEL_SEC, BORDE, TEXTO, TEXTO_SEC,
    AZUL, VERDE, AMARILLO, ROJO, MORADO,
)


def crear_fila_parametro(nombre, valor, color=TEXTO):
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Text(nombre, size=12, color=TEXTO_SEC),
            ft.Container(
                content=ft.Text(str(valor), size=12, weight=ft.FontWeight.BOLD, color=color),
                bgcolor=PANEL_SEC,
                padding=ft.Padding(8, 2, 8, 2),
                border_radius=6,
            ),
        ],
    )


def crear_barra_lateral(on_recalibrar, serial_disponible=False):
    """Devuelve el contenedor de la barra lateral.

    on_recalibrar: función que se ejecuta al pulsar el botón (recibe el evento).
    serial_disponible: True si pyserial está instalado.
    """
    return ft.Container(
        width=270,
        bgcolor=PANEL,
        padding=18,
        border_radius=16,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                # Cabecera
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.PSYCHOLOGY, color=AZUL, size=32),
                        ft.Column(
                            spacing=1,
                            controls=[
                                ft.Text("NEURONA ARTIFICIAL", size=14, weight=ft.FontWeight.BOLD, color=TEXTO),
                                ft.Text("Proyecto ESP32 MicroPython", size=11, color=TEXTO_SEC),
                            ],
                        ),
                    ],
                ),
                ft.Divider(color=BORDE, height=1),

                # Modelo matemático
                ft.Container(
                    bgcolor=FONDO,
                    padding=12,
                    border_radius=10,
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text("MODELO MATEMÁTICO", size=11, weight=ft.FontWeight.BOLD, color=AZUL),
                            ft.Text("z = x1·Wluz + x2·Wson + b", size=12, weight=ft.FontWeight.BOLD, color=TEXTO),
                            ft.Text("Alerta activa cuando z ≥ 0", size=11, color=TEXTO_SEC),
                        ],
                    ),
                ),

                # Hiperparámetros (vienen de config.py)
                ft.Text("HIPERPARÁMETROS", size=11, weight=ft.FontWeight.BOLD, color=TEXTO_SEC),
                crear_fila_parametro("Peso Luz (W_luz)", f"{config.PESO_LUZ:.1f}", AMARILLO),
                crear_fila_parametro("Peso Sonido (W_son)", f"{config.PESO_SONIDO:.1f}", AZUL),
                crear_fila_parametro("Sesgo (b)", f"{config.SESGO:.1f}", MORADO),
                crear_fila_parametro("Muestras ON (alerta)", f"{config.MUESTRAS_ON}", ROJO),
                crear_fila_parametro("Muestras OFF (normal)", f"{config.MUESTRAS_OFF}", VERDE),

                ft.Divider(color=BORDE, height=1),

                # Mapeo de hardware (también viene de config.py)
                ft.Text("HARDWARE & PINES", size=11, weight=ft.FontWeight.BOLD, color=TEXTO_SEC),
                crear_fila_parametro("LDR (Luz)", f"GPIO {config.PIN_LDR}"),
                crear_fila_parametro("Micrófono", f"GPIO {config.PIN_MICROFONO}"),
                crear_fila_parametro("Pulsador Calibrar", f"GPIO {config.PIN_BOTON}"),
                crear_fila_parametro("LED Verde (Sonido)", f"GPIO {config.PIN_LED_VERDE}"),
                crear_fila_parametro("LED Rojo (Luz/Alerta)", f"GPIO {config.PIN_LED_ROJO}"),
                crear_fila_parametro("Sirena (Buzzers)", f"G{config.PIN_BUZZER_AGUDO}/G{config.PIN_BUZZER_GRAVE}"),
                crear_fila_parametro("LCD I2C (SDA/SCL)", f"G{config.PIN_SDA}/G{config.PIN_SCL}"),

                ft.Divider(color=BORDE, height=1),

                # Botón de recalibración
                ft.FilledButton(
                    "Pulsador Recalibrar",
                    icon=ft.Icons.REFRESH,
                    on_click=on_recalibrar,
                ),

                # Estado de comunicación
                ft.Container(
                    bgcolor=FONDO,
                    padding=10,
                    border_radius=8,
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.TERMINAL, size=16, color=VERDE if serial_disponible else TEXTO_SEC),
                            ft.Text(
                                "Serial: Disponible" if serial_disponible else "Modo: Simulación Activa",
                                size=11,
                                color=TEXTO_SEC,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )