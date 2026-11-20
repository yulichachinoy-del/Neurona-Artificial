import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import math
import random
import threading
import time
import flet as ft

from neuron import Neurona
from serial_manager import SerialManager
from ui.theme import Theme
from ui.sidebar import Sidebar
from ui.view_welcome import WelcomeView
from ui.kpis import KPISection
from ui.controls_hw import ControlsAndHardwareSection
from ui.chart import TrendChartSection
from ui.view_history import HistoryView


def main(page: ft.Page):
    page.title = "Neurona Artificial — ESP32"
    page.bgcolor = Theme.FONDO
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1366
    page.window.height = 768
    page.window.min_width = 1100
    page.window.min_height = 700
    page.window.maximized = True
    page.padding = 10

    neurona = Neurona()
    estado = {"x1": 0.30, "x2": 0.25, "z": -3.25, "alerta": False, "auto_sim": False}

    # --- Vistas y Módulos ---
    kpis = KPISection()
    controles_hw = ControlsAndHardwareSection(
        on_valores_cambiados=lambda x1, x2: actualizar_evaluacion(x1, x2) if not estado["auto_sim"] and not serial_mgr.conectado else None,
        on_toggle_auto=lambda e: toggle_auto_sim(e)
    )
    grafica = TrendChartSection(max_puntos=20)
    vista_historial = HistoryView()

    def actualizar_evaluacion(x1: float, x2: float, z_externo=None, alerta_externa=None, refrescar_ui: bool = True):
        estado["x1"], estado["x2"] = x1, x2
        alerta_previa = estado["alerta"]

        # Si el ESP32 envió Z y Alerta reales, usarlos; si no, calcular localmente
        if z_externo is not None and alerta_externa is not None:
            z, alerta = z_externo, alerta_externa
        else:
            z, alerta = neurona.calcular(x1, x2)

        estado["z"], estado["alerta"] = z, alerta

        if alerta != alerta_previa:
            vista_historial.registrar_evento(alerta, x1, x2, z)

        z_norm = max(0.0, min(100.0, (z + 6.0) * 10.0))
        kpis.actualizar(x1, x2, z, z_norm, alerta, neurona.contador_on, neurona.contador_off)
        controles_hw.actualizar_hardware(x1, x2, z, alerta)
        grafica.agregar_punto(x1 * 100.0, x2 * 100.0, z_norm)

        if refrescar_ui:
            try:
                page.update()
            except Exception:
                pass

    # --- Gestión de Serial con el Circuito ESP32 ---
    def on_datos_serial(x1, x2, z, alerta):
        controles_hw.sincronizar_sliders(x1, x2)
        actualizar_evaluacion(x1, x2, z_externo=z, alerta_externa=alerta, refrescar_ui=True)

    def on_estado_serial(conectado: bool, mensaje: str):
        barra_lateral.actualizar_estado_serial(conectado, mensaje)
        badge_fuente.content.controls[1].value = f"Circuito: {mensaje}" if conectado else "Modo Local / Simulación"
        badge_fuente.content.controls[0].color = Theme.VERDE if conectado else Theme.AZUL
        try:
            page.update()
        except Exception:
            pass

    serial_mgr = SerialManager(on_data_received=on_datos_serial, on_status_change=on_estado_serial)

    def toggle_conexion_serial(puerto: str):
        if serial_mgr.conectado:
            serial_mgr.desconectar()
        else:
            serial_mgr.conectar(puerto)

    def refrescar_puertos(e=None):
        barra_lateral.actualizar_puertos(serial_mgr.listar_puertos())
        page.update()

    def on_recalibrar_circuito(e):
        enviado = serial_mgr.enviar_recalibrar()
        msg = "Comando de recalibración enviado al circuito ESP32." if enviado else "Conecta el ESP32 por USB para recalibrar el circuito."
        page.overlay.append(ft.SnackBar(content=ft.Text(msg, color=Theme.TEXTO), bgcolor=Theme.PANEL_SEC, open=True))
        page.update()

    def toggle_auto_sim(e):
        estado["auto_sim"] = e.control.value
        controles_hw.set_modo_auto(estado["auto_sim"])
        page.update()

    def auto_sim_worker():
        t = 0.0
        while True:
            if estado["auto_sim"] and not serial_mgr.conectado:
                t += 0.2
                luz = max(0.0, min(1.0, 0.45 + 0.35 * math.sin(t * 0.7) + random.uniform(-0.05, 0.05)))
                son = max(0.0, min(1.0, 0.35 + 0.30 * math.cos(t * 1.1) + random.uniform(-0.08, 0.08)))
                controles_hw.sincronizar_sliders(luz, son)
                actualizar_evaluacion(luz, son, refrescar_ui=True)
                time.sleep(0.4)
            else:
                time.sleep(0.2)

    threading.Thread(target=auto_sim_worker, daemon=True).start()

    # --- Encabezado y Navegación de Vistas ---
    badge_fuente = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.USB, size=16, color=Theme.AZUL), ft.Text("Modo Local / Simulación", size=11, color=Theme.TEXTO, weight=ft.FontWeight.BOLD)], spacing=6),
        bgcolor=Theme.PANEL, padding=ft.Padding(12, 6, 12, 6), border_radius=20, border=ft.Border.all(1, Theme.BORDE),
    )

    encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column(spacing=2, controls=[
                ft.Text("NEURONA ARTIFICIAL — ESP32", size=22, weight=ft.FontWeight.BOLD, color=Theme.TEXTO),
                ft.Text("Monitoreo sensorial local de Luz y Sonido", size=12, color=Theme.TEXTO_SEC),
            ]),
            badge_fuente,
        ],
    )

    vista_bienvenida = WelcomeView(
        on_ir_monitoreo=lambda: barra_lateral.seleccionar("monitoreo"),
        on_ir_simulador=lambda: barra_lateral.seleccionar("simulador"),
    )

    # Inicia mostrando la descripción de bienvenida
    dashboard = ft.Column(expand=True, spacing=16, scroll=ft.ScrollMode.AUTO, controls=[vista_bienvenida])

    def cambiar_vista(vista: str):
        vistas = {
            "inicio": [vista_bienvenida],
            "monitoreo": [encabezado, kpis, grafica],
            "simulador": [encabezado, controles_hw],
            "historial": [encabezado, vista_historial],
        }
        dashboard.controls = vistas.get(vista, vistas["inicio"])
        page.update()

    barra_lateral = Sidebar(
        on_navegar=cambiar_vista,
        on_conectar_serial=toggle_conexion_serial,
        on_refrescar_puertos=refrescar_puertos,
        on_recalibrar_circuito=on_recalibrar_circuito,
    )

    barra_lateral.actualizar_puertos(serial_mgr.listar_puertos())
    actualizar_evaluacion(estado["x1"], estado["x2"], refrescar_ui=False)
    page.add(ft.Row(expand=True, spacing=10, controls=[barra_lateral, ft.Container(expand=True, padding=10, content=dashboard)]))


if __name__ == "__main__":
    ft.run(main)