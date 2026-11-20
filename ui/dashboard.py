import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import math
import re
import threading
import time
import flet as ft

from neuron import Neurona
import config
from serial_manager import SerialManager
from ui.theme import Theme
from ui.sidebar import Sidebar
from ui.view_welcome import WelcomeView
from ui.kpis import KPISection
from ui.controls_hw import ControlsAndHardwareSection
from ui.chart import TrendChartSection
from ui.view_history import HistoryView
from pathlib import Path

def main(page: ft.Page):
    RUTA_ICONO = Path(__file__).parent / "assets" / "icono.ico"
    if RUTA_ICONO.exists():
        page.window.icon = str(RUTA_ICONO)
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
    # Estado separado para En Vivo vs Simulador
    estado = {
        "vista_actual": "inicio",
        "x1": 0.30,
        "x2": 0.25,
        "z": -3.25,
        "alerta": False,
        "auto_sim": False,
        "sim_x1": 0.30,
        "sim_x2": 0.25,
        "sim_alerta": False,
        "ultimo_cambio_alerta": 0.0,
    }
    lock_ui = threading.Lock()

    # --- Vistas y Módulos ---
    kpis = KPISection()
    controles_hw = ControlsAndHardwareSection(
        on_valores_cambiados=lambda x1, x2: actualizar_simulacion(x1, x2) if not estado["auto_sim"] else None,
        on_toggle_auto=lambda e: toggle_auto_sim(e)
    )
    grafica = TrendChartSection(max_puntos=20)
    vista_historial = HistoryView()

    async def _refrescar_pagina_async():
        try:
            page.update()
        except Exception:
            pass

    def _refrescar_seguro():
        try:
            page.run_task(_refrescar_pagina_async)
        except Exception:
            try:
                page.update()
            except Exception:
                pass

    def _aplicar_histeresis(z: float, alerta_actual: bool, alerta_modelo: bool) -> bool:
        """Evita saltos/rebote de alerta cuando z oscila cerca del umbral 0.0."""
        ahora = time.time()
        if ahora - estado["ultimo_cambio_alerta"] < 0.8:
            return alerta_actual

        if not alerta_actual and (z > 0.35 or (alerta_modelo and z > 0.15)):
            estado["ultimo_cambio_alerta"] = ahora
            return True
        elif alerta_actual and (z < -0.35 or (not alerta_modelo and z < -0.15)):
            estado["ultimo_cambio_alerta"] = ahora
            return False
        return alerta_actual

    # --- 1. ACTUALIZACIÓN EXCLUSIVA PARA MONITOREO EN VIVO (ESP32) ---
    def actualizar_en_vivo(x1: float, x2: float, z_externo=None, alerta_externa=None, refrescar_ui: bool = True):
        with lock_ui:
            estado["x1"], estado["x2"] = x1, x2
            alerta_previa = estado["alerta"]

            if z_externo is not None and alerta_externa is not None:
                # Respeta el cálculo y estado exacto que envía el ESP32
                z, alerta = z_externo, alerta_externa
            else:
                z, alerta_raw = neurona.calcular(x1, x2)
                alerta = _aplicar_histeresis(z, alerta_previa, alerta_raw)

            estado["z"], estado["alerta"] = z, alerta

            if alerta != alerta_previa:
                vista_historial.registrar_evento(alerta, x1, x2, z)

            z_norm = max(0.0, min(100.0, (z + 6.0) * 10.0))
            kpis.actualizar(x1, x2, z, z_norm, alerta, neurona.contador_on, neurona.contador_off)
            grafica.agregar_punto(x1 * 100.0, x2 * 100.0, z_norm)

            if estado["vista_actual"] != "simulador":
                controles_hw.actualizar_hardware(x1, x2, z, alerta)

        if refrescar_ui and estado["vista_actual"] == "monitoreo":
            _refrescar_seguro()

    # --- 2. ACTUALIZACIÓN EXCLUSIVA PARA EL SIMULADOR (AISLADA DEL ESP32) ---
    def actualizar_simulacion(x1: float, x2: float, refrescar_ui: bool = True):
        with lock_ui:
            estado["sim_x1"], estado["sim_x2"] = x1, x2
            z, alerta_raw = neurona.calcular(x1, x2)
            if estado["auto_sim"]:
                alerta = _aplicar_histeresis(z, estado["sim_alerta"], alerta_raw)
            else:
                alerta = alerta_raw
            estado["sim_alerta"] = alerta

            controles_hw.actualizar_hardware(x1, x2, z, alerta)

        if refrescar_ui and estado["vista_actual"] == "simulador":
            _refrescar_seguro()

    # --- Gestión de Serial con el Circuito ESP32 ---
    def on_datos_serial(x1, x2, z, alerta):
        if estado["vista_actual"] != "simulador":
            controles_hw.sincronizar_sliders(x1, x2)
        actualizar_en_vivo(x1, x2, z_externo=z, alerta_externa=alerta, refrescar_ui=True)

    def on_estado_serial(conectado: bool, mensaje: str):
        barra_lateral.actualizar_estado_serial(conectado, mensaje)
        if estado["vista_actual"] == "simulador":
            badge_fuente.content.controls[1].value = "Modo Simulación Independiente"
            badge_fuente.content.controls[0].color = Theme.AZUL
        else:
            badge_fuente.content.controls[1].value = f"Circuito: {mensaje}" if conectado else "Modo Local / En Espera"
            badge_fuente.content.controls[0].color = Theme.VERDE if conectado else Theme.AZUL
        _refrescar_seguro()

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
        parametros = estado.get("parametros_activacion", {
            "peso_luz": config.PESO_LUZ,
            "peso_sonido": config.PESO_SONIDO,
            "sesgo": config.SESGO,
            "muestras_on": config.MUESTRAS_ON,
            "muestras_off": config.MUESTRAS_OFF,
        })
        enviado = serial_mgr.enviar_parametros_y_recalibrar(parametros)
        if enviado:
            detalle = serial_mgr.ultimo_error_parametros
            msg = ("Parámetros activos, pero no guardados en la ESP32: " + detalle + " Recalibración iniciada.") if detalle else "Parámetros confirmados por la ESP32 y recalibración iniciada."
        elif serial_mgr.conectado:
            detalle = serial_mgr.ultimo_error_parametros
            msg = ("Error: la ESP32 rechazó los parámetros: " + detalle) if detalle else "Error: la ESP32 no respondió. Carga el main.py actualizado en la placa."
        else:
            msg = "Conecta el ESP32 por USB para recalibrar el circuito."
        page.overlay.append(ft.SnackBar(content=ft.Text(msg, color=Theme.TEXTO), bgcolor=Theme.PANEL_SEC, open=True))
        page.update()

    def toggle_auto_sim(e):
        estado["auto_sim"] = e.control.value
        controles_hw.set_modo_auto(estado["auto_sim"])
        page.update()

    def aplicar_parametros_activacion(parametros):
        ruta_config = Path(__file__).resolve().parent.parent / "config.py"
        contenido = ruta_config.read_text(encoding="utf-8")
        asignaciones = {
            "PESO_LUZ": parametros["peso_luz"],
            "PESO_SONIDO": parametros["peso_sonido"],
            "SESGO": parametros["sesgo"],
            "MUESTRAS_ON": parametros["muestras_on"],
            "MUESTRAS_OFF": parametros["muestras_off"],
        }
        for nombre, valor in asignaciones.items():
            contenido, cambios = re.subn(
                rf"(?m)^{nombre}\s*=.*$", f"{nombre} = {valor}", contenido, count=1
            )
            if cambios != 1:
                raise ValueError(f"No se encontró {nombre} en config.py")
        ruta_temporal = ruta_config.with_suffix(".py.tmp")
        ruta_temporal.write_text(contenido, encoding="utf-8")
        ruta_temporal.replace(ruta_config)

        config.PESO_LUZ = parametros["peso_luz"]
        config.PESO_SONIDO = parametros["peso_sonido"]
        config.SESGO = parametros["sesgo"]
        config.MUESTRAS_ON = parametros["muestras_on"]
        config.MUESTRAS_OFF = parametros["muestras_off"]
        estado["parametros_activacion"] = dict(parametros)
        neurona.reiniciar()
        estado["ultimo_cambio_alerta"] = 0.0
        actualizar_simulacion(estado["sim_x1"], estado["sim_x2"], refrescar_ui=False)
        if estado["vista_actual"] == "monitoreo" and not serial_mgr.conectado:
            actualizar_en_vivo(estado["x1"], estado["x2"], refrescar_ui=False)
        enviado_esp32 = serial_mgr.enviar_parametros(parametros) if serial_mgr.conectado else False
        page.update()
        if enviado_esp32:
            if serial_mgr.ultimo_error_parametros:
                return "Aviso: aplicados en la ESP32, pero no guardados allí: " + serial_mgr.ultimo_error_parametros
            return "Guardados y confirmados por el ESP32; z se actualizará con la siguiente lectura."
        if serial_mgr.conectado:
            if serial_mgr.ultimo_error_parametros:
                return "Error: la ESP32 rechazó los parámetros: " + serial_mgr.ultimo_error_parametros
            return "Error: la ESP32 no confirmó. Actualiza su main.py."
        return "Guardados en este equipo. Conecta la ESP32 para sincronizarlos."

    def auto_sim_worker():
        t = 0.0
        while True:
            if estado["auto_sim"] and estado["vista_actual"] == "simulador":
                t += 0.15
                luz = max(0.0, min(1.0, 0.50 + 0.35 * math.sin(t * 0.6)))
                son = max(0.0, min(1.0, 0.45 + 0.30 * math.cos(t * 0.9)))
                controles_hw.sincronizar_sliders(luz, son)
                actualizar_simulacion(luz, son, refrescar_ui=True)
                time.sleep(0.5)
            else:
                time.sleep(0.2)

    threading.Thread(target=auto_sim_worker, daemon=True).start()

    # --- Encabezado y Navegación de Vistas ---
    badge_fuente = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.USB, size=16, color=Theme.AZUL), ft.Text("Modo Local / En Espera", size=11, color=Theme.TEXTO, weight=ft.FontWeight.BOLD)], spacing=6),
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
        on_aplicar_parametros=aplicar_parametros_activacion,
        parametros_iniciales={
            "peso_luz": config.PESO_LUZ,
            "peso_sonido": config.PESO_SONIDO,
            "sesgo": config.SESGO,
            "muestras_on": config.MUESTRAS_ON,
            "muestras_off": config.MUESTRAS_OFF,
        },
    )

    dashboard = ft.Column(expand=True, spacing=16, scroll=ft.ScrollMode.AUTO, controls=[vista_bienvenida])

    def cambiar_vista(vista: str):
        estado["vista_actual"] = vista

        if vista == "simulador":
            badge_fuente.content.controls[1].value = "Modo Simulación Independiente"
            badge_fuente.content.controls[0].color = Theme.AZUL
            controles_hw.sincronizar_sliders(estado["sim_x1"], estado["sim_x2"])
            actualizar_simulacion(estado["sim_x1"], estado["sim_x2"], refrescar_ui=False)
        else:
            if serial_mgr.conectado:
                badge_fuente.content.controls[1].value = "Circuito: Conectado"
                badge_fuente.content.controls[0].color = Theme.VERDE
            else:
                badge_fuente.content.controls[1].value = "Modo Local / En Espera"
                badge_fuente.content.controls[0].color = Theme.AZUL

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
    actualizar_en_vivo(estado["x1"], estado["x2"], refrescar_ui=False)
    actualizar_simulacion(estado["sim_x1"], estado["sim_x2"], refrescar_ui=False)
    page.add(ft.Row(expand=True, spacing=10, controls=[barra_lateral, ft.Container(expand=True, padding=10, content=dashboard)]))


if __name__ == "__main__":
    ft.run(main)
