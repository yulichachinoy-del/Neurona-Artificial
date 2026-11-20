"""
Neurona Artificial (ESP32) - Monitoreo y Simulación en Tiempo Real
Punto de entrada del dashboard: ensambla los módulos de la interfaz.

Ejecutar desde la carpeta del proyecto:  python app.py
"""

import flet as ft

from neuron import Neurona
from tema import FONDO, PANEL, PANEL_SEC, BORDE, TEXTO, TEXTO_SEC, AZUL
from barra_lateral import crear_barra_lateral
from tarjetas_kpi import TarjetasKPI
from panel_hardware import PanelHardware
from simulador import SimuladorSensores
from grafica import GraficaTendencia

# Soporte opcional para puerto serial (si pyserial está instalado)
try:
    import serial  # noqa: F401
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

# Valores de partida de las entradas (0.0 a 1.0)
X1_INICIAL = 0.30
X2_INICIAL = 0.25


def crear_encabezado():
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column(
                spacing=2,
                controls=[
                    ft.Text("DASHBOARD NEURONA ARTIFICIAL", size=22, weight=ft.FontWeight.BOLD, color=TEXTO),
                    ft.Text("Monitoreo sensorial de Luz y Sonido con decisión de umbral e histéresis",
                            size=12, color=TEXTO_SEC),
                ],
            ),
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=AZUL),
                        ft.Text("ESP32 Firmware Ready", size=11, color=TEXTO, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=6,
                ),
                bgcolor=PANEL,
                padding=ft.Padding(12, 6, 12, 6),
                border_radius=20,
                border=ft.Border.all(1, BORDE),
            ),
        ],
    )


def main(page: ft.Page):
    # ---------- Ventana ----------
    page.title = "Neurona Artificial — Monitoreo y Simulación ESP32"
    page.bgcolor = FONDO
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1920
    page.window.height = 1080
    page.window.min_width = 1600
    page.window.min_height = 900
    page.padding = 10

    # ---------- Componentes ----------
    neurona = Neurona()
    kpis = TarjetasKPI()
    hardware = PanelHardware()
    grafica = GraficaTendencia()

    ultima = {"x1": X1_INICIAL, "x2": X2_INICIAL}  # Última entrada evaluada

    def evaluar(x1, x2):
        """Pasa las entradas por la neurona y refresca todos los paneles."""
        ultima["x1"], ultima["x2"] = x1, x2
        z, alerta = neurona.calcular(x1, x2)
        kpis.actualizar(x1, x2, z, alerta, neurona.contador_on, neurona.contador_off)
        hardware.actualizar(x1, x2, z, alerta)
        grafica.actualizar(x1, x2, z)

    def on_recalibrar(e):
        # Equivale a pulsar el botón GPIO 4 del ESP32: reinicia la histéresis
        neurona.reiniciar()
        evaluar(ultima["x1"], ultima["x2"])
        page.overlay.append(
            ft.SnackBar(
                content=ft.Text("Neurona recalibrada: Estado e histéresis reiniciados (GPIO 4)", color=TEXTO),
                bgcolor=PANEL_SEC,
                open=True,
            )
        )
        page.update()

    simulador = SimuladorSensores(page, evaluar, X1_INICIAL, X2_INICIAL)
    barra_lateral = crear_barra_lateral(on_recalibrar, HAS_SERIAL)

    # ---------- Ensamblado ----------
    dashboard = ft.Column(
        expand=True,
        spacing=16,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            crear_encabezado(),
            kpis.control,
            ft.Row(spacing=14, controls=[simulador.control, hardware.control]),
            grafica.control,
        ],
    )

    evaluar(X1_INICIAL, X2_INICIAL)  # Evaluación inicial
    page.add(
        ft.Row(
            expand=True,
            spacing=10,
            controls=[
                barra_lateral,
                ft.Container(expand=True, padding=10, content=dashboard),
            ],
        )
    )


if __name__ == "__main__":
    ft.run(main)