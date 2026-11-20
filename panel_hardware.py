import flet as ft

import config
from tema import PANEL, TEXTO_SEC, AZUL, VERDE, ROJO


def _ajustar(linea):
    """Rellena con espacios y corta a 16 caracteres, igual que Lcd.py."""
    return (linea + " " * 16)[:16]


class PanelHardware:
    def __init__(self):
        # Pantalla LCD
        self.txt_lcd_l1 = ft.Text("", size=16, font_family="Consolas", color=VERDE, weight=ft.FontWeight.BOLD)
        self.txt_lcd_l2 = ft.Text("", size=16, font_family="Consolas", color=VERDE, weight=ft.FontWeight.BOLD)

        # LEDs e indicador de sirena
        self.led_verde = self._crear_led(VERDE)
        self.led_rojo = self._crear_led(ROJO)
        self.txt_sirena = ft.Text("SILENCIADA", size=12, weight=ft.FontWeight.BOLD, color=TEXTO_SEC)

        self.control = ft.Container(
            expand=1,
            bgcolor=PANEL,
            padding=16,
            border_radius=14,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("PANTALLA LCD 1602 & ACTUADORES", size=12,
                                    weight=ft.FontWeight.BOLD, color=TEXTO_SEC),
                            ft.Icon(ft.Icons.MEMORY, size=18, color=AZUL),
                        ],
                    ),
                    # Pantalla LCD retro
                    ft.Container(
                        bgcolor="#0A1E14",
                        padding=ft.Padding(16, 12, 16, 12),
                        border_radius=8,
                        border=ft.Border.all(2, "#1B4D33"),
                        content=ft.Column(spacing=4, controls=[self.txt_lcd_l1, self.txt_lcd_l2]),
                    ),
                    # Indicadores de actuadores
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        controls=[
                            self._fila_led(self.led_verde, f"LED Verde (G{config.PIN_LED_VERDE})"),
                            self._fila_led(self.led_rojo, f"LED Rojo (G{config.PIN_LED_ROJO})"),
                            ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE, size=18, color=TEXTO_SEC),
                                    self.txt_sirena,
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        )

        # Estado inicial (mismos valores de partida que la guía)
        self.actualizar(0.30, 0.25, -3.25, False)

    @staticmethod
    def _crear_led(color_borde):
        return ft.Container(
            width=20,
            height=20,
            border_radius=10,
            bgcolor="#000000",
            border=ft.Border.all(2, color_borde),
        )

    @staticmethod
    def _fila_led(led, etiqueta):
        return ft.Row(spacing=6, controls=[led, ft.Text(etiqueta, size=11, color=TEXTO_SEC)])

    def actualizar(self, x1, x2, z, alerta):
        # LCD: mismos textos que actuators.py
        self.txt_lcd_l1.value = _ajustar("Luz:%d%% Son:%d%%" % (int(x1 * 100), int(x2 * 99)))
        if alerta:
            self.txt_lcd_l2.value = _ajustar("Z:%.1f ALERTA!" % z)
            self.txt_lcd_l2.color = ROJO
        else:
            self.txt_lcd_l2.value = _ajustar("Z:%.1f NORMAL" % z)
            self.txt_lcd_l2.color = VERDE

        # LED verde: brilla con el sonido (x2)
        brillo_verde = int(x2 * 255)
        self.led_verde.bgcolor = f"#00{brillo_verde:02x}00" if brillo_verde > 20 else "#003300"

        # LED rojo: fijo si hay alerta, si no proporcional a x1*x1 (como en actuators.py)
        if alerta:
            self.led_rojo.bgcolor = ROJO
            self.txt_sirena.value = "¡SONANDO!"
            self.txt_sirena.color = ROJO
        else:
            brillo_rojo = int(x1 * x1 * 255)
            self.led_rojo.bgcolor = f"#{brillo_rojo:02x}0000" if brillo_rojo > 20 else "#400000"
            self.txt_sirena.value = "SILENCIADA"
            self.txt_sirena.color = TEXTO_SEC