import flet as ft
from ui.theme import Theme


class ControlsAndHardwareSection(ft.Row):
    def __init__(self, on_valores_cambiados, on_toggle_auto):
        super().__init__(spacing=14)
        self.on_valores_cambiados = on_valores_cambiados

        self.lbl_luz_pct = ft.Text("30%", size=12, color=Theme.TEXTO)
        self.slider_luz = ft.Slider(
            min=0.0, max=1.0, value=0.30, divisions=100,
            active_color=Theme.AMARILLO, inactive_color=Theme.PANEL_SEC,
            on_change=self._handle_slider
        )

        self.lbl_son_pct = ft.Text("25%", size=12, color=Theme.TEXTO)
        self.slider_sonido = ft.Slider(
            min=0.0, max=1.0, value=0.25, divisions=100,
            active_color=Theme.AZUL, inactive_color=Theme.PANEL_SEC,
            on_change=self._handle_slider
        )

        self.switch_auto = ft.Switch(
            label="Generador Dinámico",
            value=False,
            active_color=Theme.AZUL,
            on_change=on_toggle_auto
        )

        panel_controles = ft.Container(
            expand=1, bgcolor=Theme.PANEL, padding=20, border_radius=14,
            content=ft.Column(spacing=10, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text("SIMULADOR DE SENSORES (x1 y x2)", size=12, weight=ft.FontWeight.BOLD, color=Theme.TEXTO_SEC),
                    self.switch_auto
                ]),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text("Luz LDR (x1):", size=12, color=Theme.AMARILLO, weight=ft.FontWeight.BOLD),
                    self.lbl_luz_pct
                ]),
                self.slider_luz,
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text("Micrófono (x2):", size=12, color=Theme.AZUL, weight=ft.FontWeight.BOLD),
                    self.lbl_son_pct
                ]),
                self.slider_sonido,
                ft.Row(spacing=8, controls=[
                    ft.OutlinedButton("Oscuridad", on_click=lambda e: self.fijar_escenario(0.10, 0.15)),
                    ft.OutlinedButton("Ambiente Normal", on_click=lambda e: self.fijar_escenario(0.40, 0.30)),
                    ft.OutlinedButton("Disparar Alerta", on_click=lambda e: self.fijar_escenario(0.85, 0.80)),
                ])
            ])
        )

        self.txt_lcd_l1 = ft.Text("Luz:30% Son:25%", size=18, font_family="Consolas", color="#22C55E", weight=ft.FontWeight.BOLD)
        self.txt_lcd_l2 = ft.Text("Z:-3.2 NORMAL   ", size=18, font_family="Consolas", color="#22C55E", weight=ft.FontWeight.BOLD)

        self.led_verde = ft.Container(width=22, height=22, border_radius=11, bgcolor="#14532D", border=ft.Border.all(2, Theme.VERDE))
        self.led_rojo = ft.Container(width=22, height=22, border_radius=11, bgcolor="#7F1D1D", border=ft.Border.all(2, Theme.ROJO))
        self.sirena_texto = ft.Text("SILENCIADA", size=12, weight=ft.FontWeight.BOLD, color=Theme.TEXTO_SEC)

        panel_hardware = ft.Container(
            expand=1, bgcolor=Theme.PANEL, padding=20, border_radius=14,
            content=ft.Column(spacing=14, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text("PANTALLA LCD 1602 & ACTUADORES", size=12, weight=ft.FontWeight.BOLD, color=Theme.TEXTO_SEC),
                    ft.Icon(ft.Icons.MEMORY, size=18, color=Theme.AZUL)
                ]),
                ft.Container(
                    bgcolor="#0A1E14", padding=ft.Padding(20, 16, 20, 16), border_radius=8,
                    border=ft.Border.all(2, "#1B4D33"),
                    content=ft.Column(spacing=6, controls=[self.txt_lcd_l1, self.txt_lcd_l2])
                ),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_AROUND, controls=[
                    ft.Row(spacing=8, controls=[self.led_verde, ft.Text("LED Verde", size=12, color=Theme.TEXTO_SEC)]),
                    ft.Row(spacing=8, controls=[self.led_rojo, ft.Text("LED Rojo", size=12, color=Theme.TEXTO_SEC)]),
                    ft.Row(spacing=8, controls=[ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE, size=18, color=Theme.TEXTO_SEC), self.sirena_texto]),
                ])
            ])
        )

        self.controls = [panel_controles, panel_hardware]

    def _handle_slider(self, e):
        self.lbl_luz_pct.value = f"{self.slider_luz.value * 100:.0f}%"
        self.lbl_son_pct.value = f"{self.slider_sonido.value * 100:.0f}%"
        self.on_valores_cambiados(self.slider_luz.value, self.slider_sonido.value)

    def fijar_escenario(self, luz: float, sonido: float):
        self.sincronizar_sliders(luz, sonido)
        self.on_valores_cambiados(luz, sonido)

    def sincronizar_sliders(self, luz: float, sonido: float):
        self.slider_luz.value = luz
        self.slider_sonido.value = sonido
        self.lbl_luz_pct.value = f"{luz * 100:.0f}%"
        self.lbl_son_pct.value = f"{sonido * 100:.0f}%"

    def set_modo_auto(self, activo: bool):
        self.slider_luz.disabled = activo
        self.slider_sonido.disabled = activo

    def actualizar_hardware(self, x1: float, x2: float, z: float, alerta: bool):
        if alerta:
            self.led_rojo.bgcolor = Theme.ROJO
            self.sirena_texto.value = "¡SONANDO!"
            self.sirena_texto.color = Theme.ROJO
        else:
            brillo_rojo = int(x1 * x1 * 255)
            self.led_rojo.bgcolor = f"#{brillo_rojo:02x}0000" if brillo_rojo > 20 else "#400000"
            self.sirena_texto.value = "SILENCIADA"
            self.sirena_texto.color = Theme.TEXTO_SEC

        brillo_verde = int(x2 * 255)
        self.led_verde.bgcolor = f"#00{brillo_verde:02x}00" if brillo_verde > 20 else "#003300"

        self.txt_lcd_l1.value = f"Luz:{int(x1 * 100):02d}% Son:{int(x2 * 99):02d}%"
        if alerta:
            self.txt_lcd_l2.value = f"Z:{z:+.1f} ALERTA! "
            self.txt_lcd_l2.color = Theme.ROJO
        else:
            self.txt_lcd_l2.value = f"Z:{z:+.1f} NORMAL  "
            self.txt_lcd_l2.color = "#22C55E"