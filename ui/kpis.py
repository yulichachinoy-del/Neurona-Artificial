import flet as ft
import config
from ui.theme import Theme

class KPISection(ft.Row):
    def __init__(self):
        super().__init__(spacing=14)

        # Referencias internas
        self.txt_luz_val = ft.Text("30%", size=26, weight=ft.FontWeight.BOLD, color=Theme.TEXTO)
        self.txt_luz_sub = ft.Text("x1 = 0.30 · LED Rojo", size=12, color=Theme.TEXTO_SEC)
        self.bar_luz = ft.ProgressBar(value=0.30, color=Theme.AMARILLO, bgcolor=Theme.PANEL_SEC, height=6)

        self.txt_son_val = ft.Text("25%", size=26, weight=ft.FontWeight.BOLD, color=Theme.TEXTO)
        self.txt_son_sub = ft.Text("x2 = 0.25 · LED Verde", size=12, color=Theme.TEXTO_SEC)
        self.bar_son = ft.ProgressBar(value=0.25, color=Theme.AZUL, bgcolor=Theme.PANEL_SEC, height=6)

        self.txt_z_val = ft.Text("-3.25", size=26, weight=ft.FontWeight.BOLD, color=Theme.TEXTO)
        self.txt_z_sub = ft.Text("Umbral z ≥ 0 · Inactivo", size=12, color=Theme.TEXTO_SEC)
        self.bar_z = ft.ProgressBar(value=0.275, color=Theme.MORADO, bgcolor=Theme.PANEL_SEC, height=6)

        self.txt_alerta_val = ft.Text("NORMAL", size=24, weight=ft.FontWeight.BOLD, color=Theme.VERDE)
        self.txt_alerta_sub = ft.Text("Sirena: Apagada", size=12, color=Theme.TEXTO_SEC)
        self.icon_alerta = ft.Icon(ft.Icons.CHECK_CIRCLE, color=Theme.VERDE, size=32)

        self.controls = [
            self._crear_tarjeta("NIVEL DE LUZ (x1)", self.txt_luz_val, self.txt_luz_sub, ft.Icons.LIGHT_MODE, Theme.AMARILLO, self.bar_luz),
            self._crear_tarjeta("NIVEL DE SONIDO (x2)", self.txt_son_val, self.txt_son_sub, ft.Icons.MIC, Theme.AZUL, self.bar_son),
            self._crear_tarjeta("ACTIVACIÓN (Z)", self.txt_z_val, self.txt_z_sub, ft.Icons.PSYCHOLOGY, Theme.MORADO, self.bar_z),
            self._crear_tarjeta("ESTADO SISTEMA", self.txt_alerta_val, self.txt_alerta_sub, ft.Icons.CHECK_CIRCLE, Theme.VERDE, icono_ref=self.icon_alerta),
        ]

    def _crear_tarjeta(self, titulo, txt_val, txt_sub, icono, color_icono, barra=None, icono_ref=None):
        icono_widget = icono_ref if icono_ref else ft.Icon(icono, color=color_icono, size=32)
        contenido = ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(titulo, size=11, weight=ft.FontWeight.BOLD, color=Theme.TEXTO_SEC),
                        icono_widget
                    ]
                ),
                txt_val,
                txt_sub
            ]
        )
        if barra:
            contenido.controls.append(barra)

        return ft.Container(
            expand=True,
            bgcolor=Theme.PANEL,
            padding=16,
            border_radius=14,
            content=contenido
        )

    def actualizar(self, x1: float, x2: float, z: float, z_norm: float, alerta: bool, cont_on: int, cont_off: int):
        self.txt_luz_val.value = f"{int(x1 * 100)}%"
        self.txt_luz_sub.value = f"x1 = {x1:.2f} · LED Rojo ({int(x1 * 100)}%)"
        self.bar_luz.value = x1

        self.txt_son_val.value = f"{int(x2 * 100)}%"
        self.txt_son_sub.value = f"x2 = {x2:.2f} · LED Verde ({int(x2 * 100)}%)"
        self.bar_son.value = x2

        self.txt_z_val.value = f"{z:+.2f}"
        if z >= 0:
            self.txt_z_sub.value = f"Supera Umbral (z ≥ 0) · Muestras ON: {cont_on}/{config.MUESTRAS_ON}"
            self.txt_z_val.color = Theme.ROJO if alerta else Theme.AMARILLO
        else:
            self.txt_z_sub.value = f"Bajo Umbral (z < 0) · Muestras OFF: {cont_off}/{config.MUESTRAS_OFF}"
            self.txt_z_val.color = Theme.TEXTO

        self.bar_z.value = z_norm / 100.0

        if alerta:
            self.txt_alerta_val.value = "¡ALERTA!"
            self.txt_alerta_val.color = Theme.ROJO
            self.txt_alerta_sub.value = "Sirena: ACTIVA (Doble tono)"
            self.icon_alerta.name = ft.Icons.WARNING_AMBER_ROUNDED
            self.icon_alerta.color = Theme.ROJO
        else:
            self.txt_alerta_val.value = "NORMAL"
            self.txt_alerta_val.color = Theme.VERDE
            self.txt_alerta_sub.value = "Sirena: Silenciada"
            self.icon_alerta.name = ft.Icons.CHECK_CIRCLE
            self.icon_alerta.color = Theme.VERDE