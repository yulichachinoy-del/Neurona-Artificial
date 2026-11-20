import flet as ft
import flet_charts as fch

from tema import PANEL, TEXTO, TEXTO_SEC, AZUL, AMARILLO, MORADO
from tarjetas_kpi import normalizar_z

MAX_PUNTOS = 20  # Muestras visibles en la gráfica


def _crear_serie(color, datos):
    return fch.LineChartData(
        color=color,
        stroke_width=3,
        curved=True,
        points=[fch.LineChartDataPoint(i, valor) for i, valor in enumerate(datos)],
    )


def _leyenda(color, texto):
    return ft.Row([
        ft.Container(width=10, height=10, bgcolor=color, border_radius=5),
        ft.Text(texto, size=11, color=TEXTO_SEC),
    ])


def _registrar(historial, valor):
    """Descarta la muestra más vieja y agrega la nueva al final."""
    historial.pop(0)
    historial.append(valor)


class GraficaTendencia:
    def __init__(self):
        # Historiales en porcentaje (0 a 100), con valores iniciales de partida
        self.hist_luz = [25.0] * MAX_PUNTOS
        self.hist_sonido = [20.0] * MAX_PUNTOS
        self.hist_z = [30.0] * MAX_PUNTOS

        self.serie_luz = _crear_serie(AMARILLO, self.hist_luz)
        self.serie_sonido = _crear_serie(AZUL, self.hist_sonido)
        self.serie_z = _crear_serie(MORADO, self.hist_z)

        self.grafica = fch.LineChart(
            expand=True,
            min_x=0,
            max_x=MAX_PUNTOS - 1,
            min_y=0,
            max_y=100,
            interactive=True,
            data_series=[self.serie_luz, self.serie_sonido, self.serie_z],
        )

        self.control = ft.Container(
            height=280,
            bgcolor=PANEL,
            padding=16,
            border_radius=14,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("TENDENCIA TEMPORAL DE ENTRADAS Y ACTIVACIÓN", size=13,
                                            weight=ft.FontWeight.BOLD, color=TEXTO),
                                    ft.Text("Evolución en tiempo real de Luz, Sonido y Activación Neuronal (Umbral en 60%)",
                                            size=11, color=TEXTO_SEC),
                                ],
                            ),
                            ft.Row(
                                spacing=12,
                                controls=[
                                    _leyenda(AMARILLO, "Luz (x1 %)"),
                                    _leyenda(AZUL, "Sonido (x2 %)"),
                                    _leyenda(MORADO, "Activación Z"),
                                ],
                            ),
                        ],
                    ),
                    ft.Container(expand=True, content=self.grafica),
                ],
            ),
        )

    def actualizar(self, x1, x2, z):
        _registrar(self.hist_luz, x1 * 100.0)
        _registrar(self.hist_sonido, x2 * 100.0)
        _registrar(self.hist_z, normalizar_z(z))

        self.serie_luz.points = [fch.LineChartDataPoint(i, v) for i, v in enumerate(self.hist_luz)]
        self.serie_sonido.points = [fch.LineChartDataPoint(i, v) for i, v in enumerate(self.hist_sonido)]
        self.serie_z.points = [fch.LineChartDataPoint(i, v) for i, v in enumerate(self.hist_z)]