import time
from machine import Pin, ADC
import config


def crear_adc(pin):
    adc = ADC(Pin(pin))
    adc.atten(ADC.ATTN_11DB)  # Permite leer de 0 a 3.3 V
    return adc


class Sensores:
    def __init__(self):
        self.boton = Pin(config.PIN_BOTON, Pin.IN, Pin.PULL_UP)
        self.microfono = crear_adc(config.PIN_MICROFONO)
        self.ldr = crear_adc(config.PIN_LDR)
        self.ruido_base = 0
        self.luz_suave = 0     # Luz con "memoria": cambia poco a poco
        self.luz_min = 0       # Lo mas oscuro que ha visto el LDR
        self.luz_max = 4095    # Lo mas claro que ha visto el LDR

    def boton_pulsado(self):
        # Con PULL_UP el boton da 0 cuando se aprieta
        return self.boton.value() == 0

    def leer_luz(self):
        # Promedio de varias lecturas para quitar ruido
        total = 0
        for i in range(config.LUZ_MUESTRAS):
            total += self.ldr.read()
        return total // config.LUZ_MUESTRAS

    def leer_ruido(self):
        # El sonido es una onda: medimos cuanto sube y baja en un rato
        inicio = time.ticks_ms()
        minimo = 4095
        maximo = 0
        while time.ticks_diff(time.ticks_ms(), inicio) < config.VENTANA_MIC_MS:
            valor = self.microfono.read()
            if valor < minimo:
                minimo = valor
            if valor > maximo:
                maximo = valor
        return maximo - minimo

    def calibrar(self):
        # Promedio del ruido del ambiente = lo que se considera "silencio"
        total = 0
        for i in range(config.MUESTRAS_CALIBRACION):
            total += self.leer_ruido()
        self.ruido_base = total // config.MUESTRAS_CALIBRACION

        # Luz del ambiente = punto de partida: aqui la luz vale 0%
        ambiente = self.leer_luz()
        self.luz_suave = ambiente
        self.luz_min = ambiente
        self.luz_max = min(4095, ambiente + config.LUZ_MARGEN)
        print("Calibrado. Ruido de fondo:", self.ruido_base, "| Luz ambiente:", ambiente)

    def leer_entradas(self):
        # x1 y x2 son valores entre 0.0 y 1.0
        # Luz con memoria: 85% del valor anterior + 15% de la lectura nueva
        lectura = self.leer_luz()
        self.luz_suave = self.luz_suave * (1 - config.LUZ_SUAVIZADO) + lectura * config.LUZ_SUAVIZADO
        luz = int(self.luz_suave)
        ruido = self.leer_ruido()

        # El rango del LDR se ajusta solo: tapar baja el minimo, alumbrar sube el maximo
        if luz < self.luz_min:
            self.luz_min = luz
        if luz > self.luz_max:
            self.luz_max = luz
        rango = max(1, self.luz_max - self.luz_min)  # Evita dividir entre 0
        x1 = (luz - self.luz_min) / rango

        x2 = min(1.0, max(0, ruido - self.ruido_base) / config.MIC_MAXIMO)
        return x1, x2, luz, ruido