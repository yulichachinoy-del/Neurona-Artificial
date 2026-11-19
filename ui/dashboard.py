"""
PROYECTO UNIVERSITARIO: NEURONA ARTIFICIAL (ESP32)
Monitoreo, Diagnóstico y Simulación en Tiempo Real
Detección combinada de Luz (LDR) y Sonido (Micrófono)
"""

import math
import random
import threading
import time
import flet as ft

from neuron import Neurona
from ui.theme import Theme
from sidebar import Sidebar
from kpis import KPISection
from controls_hw import ControlsAndHardwareSection
from chart import TrendChartSection

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


def main(page: ft.Page):
    # ---------- CONFIGURACIÓN DE VENTANA ----------
    page.title = "Neurona Artificial — Monitoreo y Simulación ESP32"
    page.bgcolor = Theme.FONDO
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1920
    page.window.height = 1080
    page.window.min_width = 1600
    page.window.min_height = 900
    page.padding = 10

    # ---------- ESTADO E INSTANCIA ----------
    neurona = Neurona()
    estado = {
        "x1": 0.30,
        "x2": 0.25,
        "z": -3.25,
        "alerta": False,
        "auto_sim": False,
    }

    # ---------- LÓGICA CENTRAL DE ACTUALIZACIÓN ----------
    def actualizar_evaluacion(x1: float, x2: float, refrescar_ui: bool = True):
        estado["x1"] = x1
        estado["x2"] = x2

        z, alerta = neurona.calcular(x1, x2)
        estado["z"] = z
        estado["alerta"] = alerta

        # Normalización de Z: z ∈ [-6, 4] -> [0, 100], umbral z=0 en 60%
        z_norm = max(0.0, min(100.0, (z + 6.0) * 10.0))

        # Delegar actualizaciones a cada módulo visual
        kpis.actualizar(x1, x2, z, z_norm, alerta, neurona.contador_on, neurona.contador_off)
        controles_hw.actualizar_hardware(x1, x2, z, alerta)
        grafica.agregar_punto(x1 * 100.0, x2 * 100.0, z_norm)

        if refrescar_ui:
            page.update()

    # ---------- CALLBACKS DE EVENTOS ----------
    def on_recalibrar_click(e):
        neurona.reiniciar()
        actualizar_evaluacion(estado["x1"], estado["x2"])
        page.overlay.append(
            ft.SnackBar(
                content=ft.Text("Neurona recalibrada: Estado e histéresis reiniciados (GPIO 4)", color=Theme.TEXTO),
                bgcolor=Theme.PANEL_SEC,
                open=True
            )
        )
        page.update()

    def on_manual_input(x1: float, x2: float):
        if not estado["auto_sim"]:
            actualizar_evaluacion(x1, x2)

    def toggle_auto_sim(e):
        estado["auto_sim"] = e.control.value
        controles_hw.set_modo_auto(estado["auto_sim"])
        page.update()

    # ---------- INSTANCIACIÓN DE MÓDULOS UI ----------
    barra_lateral = Sidebar(on_recalibrar=on_recalibrar_click, has_serial=HAS_SERIAL)
    kpis = KPISection()
    controles_hw = ControlsAndHardwareSection(on_valores_cambiados=on_manual_input, on_toggle_auto=toggle_auto_sim)
    grafica = TrendChartSection(max_puntos=20)

    # ---------- HILO DE SIMULACIÓN AUTOMÁTICA ----------
    def auto_sim_worker():
        t = 0.0
        while True:
            if estado["auto_sim"]:
                t += 0.2
                base_luz = 0.45 + 0.35 * math.sin(t * 0.7)
                nueva_luz = max(0.0, min(1.0, base_luz + random.uniform(-0.05, 0.05)))

                base_son = 0.35 + 0.30 * math.cos(t * 1.1)
                nuevo_son = max(0.0, min(1.0, base_son + random.uniform(-0.08, 0.08)))

                controles_hw.sincronizar_sliders(nueva_luz, nuevo_son)
                actualizar_evaluacion(nueva_luz, nuevo_son, refrescar_ui=False)
                try:
                    page.update()
                except Exception:
                    break
                time.sleep(0.4)
            else:
                time.sleep(0.2)

    threading.Thread(target=auto_sim_worker, daemon=True).start()

    # ---------- ENSAMBLADO DEL DASHBOARD ----------
    encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column(
                spacing=2,
                controls=[
                    ft.Text("DASHBOARD NEURONA ARTIFICIAL", size=22, weight=ft.FontWeight.BOLD, color=Theme.TEXTO),
                    ft.Text("Monitoreo sensorial de Luz y Sonido con decisión de umbral e histéresis", size=12, color=Theme.TEXTO_SEC)
                ]
            ),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=Theme.AZUL),
                    ft.Text("ESP32 Firmware Ready", size=11, color=Theme.TEXTO, weight=ft.FontWeight.BOLD)
                ], spacing=6),
                bgcolor=Theme.PANEL,
                padding=ft.Padding(12, 6, 12, 6),
                border_radius=20,
                border=ft.Border.all(1, Theme.BORDE)
            )
        ]
    )

    dashboard = ft.Column(
        expand=True,
        spacing=16,
        scroll=ft.ScrollMode.AUTO,
        controls=[encabezado, kpis, controles_hw, grafica]
    )

    estructura = ft.Row(
        expand=True,
        spacing=10,
        controls=[
            barra_lateral,
            ft.Container(expand=True, padding=10, content=dashboard)
        ]
    )

    actualizar_evaluacion(estado["x1"], estado["x2"], refrescar_ui=False)
    page.add(estructura)


if __name__ == "__main__":
    ft.run(main)