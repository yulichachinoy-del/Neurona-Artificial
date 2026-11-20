import flet as ft

import config
from tema import PANEL, PANEL_SEC, TEXTO, TEXTO_SEC, AZUL, VERDE, AMARILLO, ROJO, MORADO


def normalizar_z(z):
    """Mapea z de [-6, 4] a [0, 100]. El umbral z = 0 queda en 60 %."""
    return max(0.0, min(100.0, (z + 6.0) * 10.0))


class TarjetasKPI:
    def __init__(self):
        # Luz
        self.txt_luz_val = ft.Text("30%", size=26, weight=ft.FontWeight.BOLD, color=TEXTO)
        self.txt_luz_sub = ft.Text("x1 = 0.30 · LED Rojo", size=12, color=TEXTO_SEC)
        self.bar_luz = ft.ProgressBar(value=0.30, color=AMARILLO, bgcolor=PANEL_SEC, height=6)

        # Sonido
        self.txt_sonido_val = ft.Text("25%", size=26, weight=ft.FontWeight.BOLD, color=TEXTO)
        self.txt_sonido_sub = ft.Text("x2 = 0.25 · LED Verde", size=12, color=TEXTO_SEC)
        self.bar_sonido = ft.ProgressBar(value=0.25, color=AZUL, bgcolor=PANEL_SEC, height=6)

        # Activación Z
        self.txt_z_val = ft.Text("-3.25", size=26, weight=ft.FontWeight.BOLD, color=TEXTO)
        self.txt_z_sub = ft.Text("Umbral z ≥ 0 · Inactivo", size=12, color=TEXTO_SEC)
        self.bar_z = ft.ProgressBar(value=0.275, color=MORADO, bgcolor=PANEL_SEC, height=6)

        # Estado del sistema
        self.txt_alerta_val = ft.Text("NORMAL", size=24, weight=ft.FontWeight.BOLD, color=VERDE)
        self.txt_alerta_sub = ft.Text("Sirena: Apagada", size=12, color=TEXTO_SEC)
        self.icono_alerta = ft.Icon(ft.Icons.CHECK_CIRCLE, color=VERDE, size=32)

        self.control = ft.Row(
            spacing=14,
            controls=[
                self._tarjeta("NIVEL DE LUZ (x1)", self.txt_luz_val, self.txt_luz_sub,
                              ft.Icon(ft.Icons.LIGHT_MODE, color=AMARILLO, size=32), self.bar_luz),
                self._tarjeta("NIVEL DE SONIDO (x2)", self.txt_sonido_val, self.txt_sonido_sub,
                              ft.Icon(ft.Icons.MIC, color=AZUL, size=32), self.bar_sonido),
                self._tarjeta("ACTIVACIÓN (Z)", self.txt_z_val, self.txt_z_sub,
                              ft.Icon(ft.Icons.PSYCHOLOGY, color=MORADO, size=32), self.bar_z),
                self._tarjeta("ESTADO SISTEMA", self.txt_alerta_val, self.txt_alerta_sub,
                              self.icono_alerta),
            ],
        )

    @staticmethod
    def _tarjeta(titulo, txt_val, txt_sub, icono, barra=None):
        contenido = ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(titulo, size=11, weight=ft.FontWeight.BOLD, color=TEXTO_SEC),
                        icono,
                    ],
                ),
                txt_val,
                txt_sub,
            ],
        )
        if barra:
            contenido.controls.append(barra)

        return ft.Container(
            expand=True,
            bgcolor=PANEL,
            padding=16,
            border_radius=14,
            content=contenido,
        )

    def actualizar(self, x1, x2, z, alerta, contador_on, contador_off):
        # Luz
        self.txt_luz_val.value = f"{int(x1 * 100)}%"
        self.txt_luz_sub.value = f"x1 = {x1:.2f} · LED Rojo ({int(x1 * 100)}%)"
        self.bar_luz.value = x1

        # Sonido
        self.txt_sonido_val.value = f"{int(x2 * 100)}%"
        self.txt_sonido_sub.value = f"x2 = {x2:.2f} · LED Verde ({int(x2 * 100)}%)"
        self.bar_sonido.value = x2

        # Activación Z
        self.txt_z_val.value = f"{z:+.2f}"
        if z >= 0:
            self.txt_z_sub.value = f"Supera Umbral (z ≥ 0) · Muestras ON: {contador_on}/{config.MUESTRAS_ON}"
            self.txt_z_val.color = ROJO if alerta else AMARILLO
        else:
            self.txt_z_sub.value = f"Bajo Umbral (z < 0) · Muestras OFF: {contador_off}/{config.MUESTRAS_OFF}"
            self.txt_z_val.color = TEXTO
        self.bar_z.value = normalizar_z(z) / 100.0

        # Estado del sistema
        if alerta:
            self.txt_alerta_val.value = "¡ALERTA!"
            self.txt_alerta_val.color = ROJO
            self.txt_alerta_sub.value = "Sirena: ACTIVA (Doble tono)"
            self.icono_alerta.name = ft.Icons.WARNING_AMBER_ROUNDED
            self.icono_alerta.color = ROJO
        else:
            self.txt_alerta_val.value = "NORMAL"
            self.txt_alerta_val.color = VERDE
            self.txt_alerta_sub.value = "Sirena: Silenciada"
            self.icono_alerta.name = ft.Icons.CHECK_CIRCLE
            self.icono_alerta.color = VERDE