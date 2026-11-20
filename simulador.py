import math
import random
import threading
import time

import flet as ft

from tema import PANEL, PANEL_SEC, TEXTO, TEXTO_SEC, AZUL, AMARILLO


class SimuladorSensores:
    def __init__(self, page, on_cambio, x1=0.30, x2=0.25):
        """page: la página de Flet.
        on_cambio: función que recibe (x1, x2) cada vez que cambian las entradas.
        """
        self.page = page
        self.on_cambio = on_cambio
        self.auto_activo = False

        # Porcentajes junto a cada slider
        self.txt_luz_pct = ft.Text(f"{x1 * 100:.0f}%", size=12, color=TEXTO)
        self.txt_sonido_pct = ft.Text(f"{x2 * 100:.0f}%", size=12, color=TEXTO)

        self.slider_luz = ft.Slider(
            min=0.0, max=1.0, value=x1, divisions=100,
            active_color=AMARILLO, inactive_color=PANEL_SEC,
            on_change=self._on_slider,
        )
        self.slider_sonido = ft.Slider(
            min=0.0, max=1.0, value=x2, divisions=100,
            active_color=AZUL, inactive_color=PANEL_SEC,
            on_change=self._on_slider,
        )

        self.switch_auto = ft.Switch(
            label="Generador Dinámico en Vivo",
            value=False,
            active_color=AZUL,
            on_change=self._on_switch,
        )

        self.botones = [
            ft.OutlinedButton("Oscuridad", on_click=lambda e: self.fijar(0.10, 0.15)),
            ft.OutlinedButton("Ambiente Normal", on_click=lambda e: self.fijar(0.40, 0.30)),
            ft.OutlinedButton("Disparar Alerta", on_click=lambda e: self.fijar(0.85, 0.80)),
        ]

        self.control = ft.Container(
            expand=1,
            bgcolor=PANEL,
            padding=16,
            border_radius=14,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("SIMULADOR DE SENSORES (x1 y x2)", size=12,
                                    weight=ft.FontWeight.BOLD, color=TEXTO_SEC),
                            self.switch_auto,
                        ],
                    ),
                    # Luz
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Luz LDR (x1):", size=12, color=AMARILLO, weight=ft.FontWeight.BOLD),
                            self.txt_luz_pct,
                        ],
                    ),
                    self.slider_luz,
                    # Sonido
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Micrófono (x2):", size=12, color=AZUL, weight=ft.FontWeight.BOLD),
                            self.txt_sonido_pct,
                        ],
                    ),
                    self.slider_sonido,
                    # Escenarios rápidos
                    ft.Row(spacing=8, controls=self.botones),
                ],
            ),
        )

        # Hilo del generador: siempre vivo, pero solo actúa si auto_activo es True
        threading.Thread(target=self._generador, daemon=True).start()

    # ---------- utilidades internas ----------
    def _mostrar(self, x1, x2):
        """Refleja los valores en los sliders y en los porcentajes."""
        self.slider_luz.value = x1
        self.slider_sonido.value = x2
        self.txt_luz_pct.value = f"{x1 * 100:.0f}%"
        self.txt_sonido_pct.value = f"{x2 * 100:.0f}%"

    def _notificar(self, x1, x2):
        self.on_cambio(x1, x2)
        self.page.update()

    # ---------- eventos ----------
    def fijar(self, x1, x2):
        """Pone ambas entradas en un valor concreto (escenarios rápidos)."""
        if self.auto_activo:
            return
        self._mostrar(x1, x2)
        self._notificar(x1, x2)

    def _on_slider(self, e):
        x1 = self.slider_luz.value
        x2 = self.slider_sonido.value
        self._mostrar(x1, x2)
        self._notificar(x1, x2)

    def _on_switch(self, e):
        self.auto_activo = e.control.value
        # Con el generador encendido, los controles manuales se bloquean
        for control in (self.slider_luz, self.slider_sonido, *self.botones):
            control.disabled = self.auto_activo
        self.page.update()

    # ---------- generador dinámico ----------
    def _generador(self):
        t = 0.0
        while True:
            if not self.auto_activo:
                time.sleep(0.2)
                continue

            t += 0.2
            # Oscilación suave más una pequeña fluctuación aleatoria
            x1 = 0.45 + 0.35 * math.sin(t * 0.7) + random.uniform(-0.05, 0.05)
            x2 = 0.35 + 0.30 * math.cos(t * 1.1) + random.uniform(-0.08, 0.08)
            x1 = max(0.0, min(1.0, x1))
            x2 = max(0.0, min(1.0, x2))

            self._mostrar(x1, x2)
            try:
                self._notificar(x1, x2)
            except Exception:
                break  # la ventana se cerró: terminar el hilo
            time.sleep(0.4)