import flet as ft
from ui.theme import Theme


class WelcomeView(ft.Container):
    PARAMETROS_INICIALES = {
        "peso_luz": 5.0,
        "peso_sonido": 5.0,
        "sesgo": -6.0,
        "muestras_on": 2,
        "muestras_off": 5,
    }

    def __init__(self, on_ir_monitoreo, on_ir_simulador, on_aplicar_parametros, parametros_iniciales=None):
        super().__init__(
            expand=True,
            alignment=ft.Alignment(0, 0),
            padding=30,
        )
        parametros_iniciales = parametros_iniciales or {}
        self.peso_luz = self._campo("Peso de luz", str(parametros_iniciales.get("peso_luz", 5.0)))
        self.peso_sonido = self._campo("Peso de sonido", str(parametros_iniciales.get("peso_sonido", 5.0)))
        self.sesgo = self._campo("Sesgo", str(parametros_iniciales.get("sesgo", -6.0)))
        self.muestras_on = self._campo("Muestras para activar", str(parametros_iniciales.get("muestras_on", 2)))
        self.muestras_off = self._campo("Muestras para desactivar", str(parametros_iniciales.get("muestras_off", 5)))
        self.mensaje_parametros = ft.Text("", size=12, color=Theme.TEXTO_SEC)
        self.content = ft.Container(
            width=900,
            bgcolor=Theme.PANEL,
            padding=36,
            border_radius=20,
            border=ft.Border.all(1, Theme.BORDE),
            content=ft.Column(
                spacing=20,
                tight=True,
                controls=[
                    ft.Row(
                        spacing=14,
                        controls=[
                            ft.Container(
                                bgcolor=Theme.FONDO,
                                padding=14,
                                border_radius=14,
                                content=ft.Icon(ft.Icons.PSYCHOLOGY, color=Theme.AZUL, size=36),
                            ),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Neurona Artificial — ESP32", size=24, weight=ft.FontWeight.BOLD, color=Theme.TEXTO),
                                    ft.Text("Sistema Embebido de Percepción Sensorial", size=13, color=Theme.AZUL),
                                ],
                            ),
                        ],
                    ),
                    ft.Divider(color=Theme.BORDE),
                    ft.Text(
                        "Firmware en MicroPython que lee un sensor de luz y un micrófono, evalúa sus señales "
                        "con una neurona artificial y controla indicadores, una alarma y una pantalla LCD. "
                        "La versión actual funciona localmente: no requiere conexión Wi-Fi ni comunicación MQTT.",
                        size=15,
                        color=Theme.TEXTO,
                        height=1.5,
                    ),
                    ft.Row(
                        spacing=12,
                        controls=[
                            self._chip(ft.Icons.LIGHT_MODE, "Sensor de Luz (LDR)", Theme.AMARILLO),
                            self._chip(ft.Icons.MIC, "Micrófono Ambiental", Theme.AZUL),
                            self._chip(ft.Icons.USB, "Comunicación Serial Local", Theme.VERDE),
                        ],
                    ),
                    ft.Divider(color=Theme.BORDE),
                    ft.Text("Parámetros de activación", size=17, weight=ft.FontWeight.BOLD, color=Theme.TEXTO),
                    ft.Text("Ajusta cómo se combinan luz y sonido y cuántas lecturas consecutivas cambian la alerta.", size=12, color=Theme.TEXTO_SEC),
                    ft.Row(spacing=12, controls=[self.peso_luz, self.peso_sonido, self.sesgo]),
                    ft.Row(spacing=12, controls=[self.muestras_on, self.muestras_off]),
                    ft.Row(spacing=12, controls=[
                        ft.FilledButton("Aplicar parámetros", icon=ft.Icons.SAVE_OUTLINED,
                                        on_click=lambda e: self._aplicar(on_aplicar_parametros)),
                        ft.OutlinedButton("Restablecer iniciales", icon=ft.Icons.RESTART_ALT,
                                          on_click=lambda e: self._restablecer(on_aplicar_parametros)),
                    ]),
                    ft.Text("Se guardan en config.py y se envían al aplicar (la ESP32 requiere el firmware actualizado).", size=12, color=Theme.TEXTO_SEC),
                    ft.Row(spacing=12, controls=[
                        self.mensaje_parametros,
                    ]),
                    ft.Container(height=6),
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.FilledButton(
                                "Ver Monitoreo en Vivo",
                                icon=ft.Icons.DASHBOARD,
                                on_click=lambda e: on_ir_monitoreo(),
                            ),
                            ft.OutlinedButton(
                                "Abrir Simulador y LCD",
                                icon=ft.Icons.TUNE,
                                on_click=lambda e: on_ir_simulador(),
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _campo(self, etiqueta: str, valor: str):
        return ft.TextField(label=etiqueta, value=valor, expand=True, dense=True,
                            keyboard_type=ft.KeyboardType.NUMBER,
                            border_color=Theme.BORDE, focused_border_color=Theme.AZUL,
                            text_size=13)

    def _valores_actuales(self):
        try:
            return {
                "peso_luz": float(self.peso_luz.value),
                "peso_sonido": float(self.peso_sonido.value),
                "sesgo": float(self.sesgo.value),
                "muestras_on": int(self.muestras_on.value),
                "muestras_off": int(self.muestras_off.value),
            }
        except (TypeError, ValueError):
            raise ValueError

    def _aplicar(self, callback, parametros=None):
        aplicado = False
        try:
            parametros = parametros or self._valores_actuales()
            if parametros["muestras_on"] < 1 or parametros["muestras_off"] < 1:
                raise ValueError
            mensaje = callback(parametros)
            self.mensaje_parametros.value = mensaje or "Parámetros aplicados."
            if mensaje and mensaje.startswith("Error:"):
                self.mensaje_parametros.color = Theme.ROJO
            elif mensaje and mensaje.startswith("Aviso:"):
                self.mensaje_parametros.color = Theme.AMARILLO
            else:
                self.mensaje_parametros.color = Theme.VERDE
            aplicado = True
        except (TypeError, ValueError):
            self.mensaje_parametros.value = "Revisa los valores: usa números y muestras ≥ 1."
            self.mensaje_parametros.color = Theme.ROJO
        except OSError:
            self.mensaje_parametros.value = "No se pudo guardar config.py."
            self.mensaje_parametros.color = Theme.ROJO
        try:
            self.mensaje_parametros.update()
        except Exception:
            pass
        return aplicado

    def _restablecer(self, callback):
        valores = dict(self.PARAMETROS_INICIALES)
        if self._aplicar(callback, valores):
            self.peso_luz.value = str(valores["peso_luz"])
            self.peso_sonido.value = str(valores["peso_sonido"])
            self.sesgo.value = str(valores["sesgo"])
            self.muestras_on.value = str(valores["muestras_on"])
            self.muestras_off.value = str(valores["muestras_off"])
            try:
                self.update()
            except Exception:
                pass

    def _chip(self, icono, texto: str, color: str):
        return ft.Container(
            bgcolor=Theme.FONDO,
            padding=ft.Padding(12, 8, 12, 8),
            border_radius=10,
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(icono, size=16, color=color),
                    ft.Text(texto, size=12, color=Theme.TEXTO_SEC),
                ],
            ),
        )
