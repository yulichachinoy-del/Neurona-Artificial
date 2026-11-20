from datetime import datetime
import flet as ft
from ui.theme import Theme


class HistoryView(ft.Container):
    def __init__(self):
        super().__init__(bgcolor=Theme.PANEL, padding=20, border_radius=16)
        self.tabla = ft.DataTable(
            expand=True,
            heading_row_color=Theme.FONDO,
            columns=[
                ft.DataColumn(ft.Text("Hora", color=Theme.TEXTO_SEC)),
                ft.DataColumn(ft.Text("Evento", color=Theme.TEXTO_SEC)),
                ft.DataColumn(ft.Text("Luz (x1)", color=Theme.AMARILLO)),
                ft.DataColumn(ft.Text("Sonido (x2)", color=Theme.AZUL)),
                ft.DataColumn(ft.Text("Activación Z", color=Theme.MORADO)),
            ],
            rows=[]
        )
        self.content = ft.Column(spacing=12, controls=[
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Text("HISTORIAL DE EVENTOS Y ALERTAS", size=14, weight=ft.FontWeight.BOLD, color=Theme.TEXTO),
                ft.OutlinedButton("Limpiar Registro", icon=ft.Icons.DELETE_OUTLINE, on_click=self._limpiar),
            ]),
            self.tabla
        ])

    def registrar_evento(self, alerta: bool, x1: float, x2: float, z: float):
        hora = datetime.now().strftime("%H:%M:%S")
        estado_txt = "¡ALERTA ACTIVA!" if alerta else "Retorno a Normal"
        color_est = Theme.ROJO if alerta else Theme.VERDE

        nueva_fila = ft.DataRow(cells=[
            ft.DataCell(ft.Text(hora, color=Theme.TEXTO)),
            ft.DataCell(ft.Text(estado_txt, color=color_est, weight=ft.FontWeight.BOLD)),
            ft.DataCell(ft.Text(f"{int(x1 * 100)}% ({x1:.2f})", color=Theme.TEXTO)),
            ft.DataCell(ft.Text(f"{int(x2 * 100)}% ({x2:.2f})", color=Theme.TEXTO)),
            ft.DataCell(ft.Text(f"{z:+.2f}", color=Theme.TEXTO, weight=ft.FontWeight.BOLD)),
        ])
        self.tabla.rows.insert(0, nueva_fila)
        if len(self.tabla.rows) > 30:
            self.tabla.rows.pop()

    def _limpiar(self, e):
        self.tabla.rows.clear()
        e.page.update()