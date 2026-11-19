import flet as ft
import flet_charts as fch
from ui.theme import Theme

class TrendChartSection(ft.Container):
    def __init__(self, max_puntos: int = 20):
        super().__init__(
            height=280,
            bgcolor=Theme.PANEL,
            padding=16,
            border_radius=14,
        )
        self.max_puntos = max_puntos
        self.hist_luz = [25.0] * max_puntos
        self.hist_sonido = [20.0] * max_puntos
        self.hist_z_norm = [30.0] * max_puntos

        self.serie_luz = self._crear_serie(Theme.AMARILLO, self.hist_luz)
        self.serie_sonido = self._crear_serie(Theme.AZUL, self.hist_sonido)
        self.serie_z = self._crear_serie(Theme.MORADO, self.hist_z_norm)

        grafica = fch.LineChart(
            expand=True,
            min_x=0,
            max_x=max_puntos - 1,
            min_y=0,
            max_y=100,
            interactive=True,
            data_series=[self.serie_luz, self.serie_sonido, self.serie_z]
        )

        self.content = ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("TENDENCIA TEMPORAL DE ENTRADAS Y ACTIVACIÓN", size=13, weight=ft.FontWeight.BOLD, color=Theme.TEXTO),
                                ft.Text("Evolución en tiempo real de Luz, Sonido y Activación Neuronal (Umbral en 60%)", size=11, color=Theme.TEXTO_SEC)
                            ]
                        ),
                        ft.Row(
                            spacing=12,
                            controls=[
                                self._crear_leyenda(Theme.AMARILLO, "Luz (x1 %)"),
                                self._crear_leyenda(Theme.AZUL, "Sonido (x2 %)"),
                                self._crear_leyenda(Theme.MORADO, "Activación Z"),
                            ]
                        )
                    ]
                ),
                ft.Container(expand=True, content=grafica)
            ]
        )

    def _crear_serie(self, color: str, datos: list):
        return fch.LineChartData(
            color=color,
            stroke_width=3,
            curved=True,
            points=[fch.LineChartDataPoint(i, val) for i, val in enumerate(datos)]
        )

    def _crear_leyenda(self, color: str, texto: str):
        return ft.Row([
            ft.Container(width=10, height=10, bgcolor=color, border_radius=5),
            ft.Text(texto, size=11, color=Theme.TEXTO_SEC)
        ])

    def agregar_punto(self, luz_pct: float, sonido_pct: float, z_norm: float):
        self.hist_luz.pop(0)
        self.hist_luz.append(luz_pct)

        self.hist_sonido.pop(0)
        self.hist_sonido.append(sonido_pct)

        self.hist_z_norm.pop(0)
        self.hist_z_norm.append(z_norm)

        self.serie_luz.points = [fch.LineChartDataPoint(i, val) for i, val in enumerate(self.hist_luz)]
        self.serie_sonido.points = [fch.LineChartDataPoint(i, val) for i, val in enumerate(self.hist_sonido)]
        self.serie_z.points = [fch.LineChartDataPoint(i, val) for i, val in enumerate(self.hist_z_norm)]