import time
from machine import Pin, PWM
import config


def crear_pwm(pin, frecuencia):
    # Crea una salida PWM apagada (duty 0 = apagado, 1023 = maximo)
    return PWM(Pin(pin), freq=frecuencia, duty=0)


class Actuadores:
    def __init__(self, lcd):
        self.lcd = lcd

        self.led_verde = crear_pwm(config.PIN_LED_VERDE, 1000)
        self.led_rojo = crear_pwm(config.PIN_LED_ROJO, 1000)

        # Dos tonos distintos para que la alarma suene como sirena
        self.buzzer_agudo = crear_pwm(config.PIN_BUZZER_AGUDO, 2000)
        self.buzzer_grave = crear_pwm(config.PIN_BUZZER_GRAVE, 1000)

        # Grupos, para apagarlos con un solo for
        self.leds = (self.led_verde, self.led_rojo)
        self.buzzers = (self.buzzer_agudo, self.buzzer_grave)

        self.tono_agudo = True
        self.ultimo_cambio = 0
        self.ultimo_lcd = 0

    def probar(self):
        # Enciende cada salida un momento al arrancar
        for led in self.leds:
            led.duty(500)
            time.sleep_ms(150)
            led.duty(0)
        for buzzer in self.buzzers:
            buzzer.duty(300)
            time.sleep_ms(100)
            buzzer.duty(0)

    def silenciar(self):
        for buzzer in self.buzzers:
            buzzer.duty(0)

    def apagar_todo(self):
        for led in self.leds:
            led.duty(0)
        self.silenciar()

    def sonar_alarma(self, alerta):
        if not alerta:
            self.silenciar()
            return

        # Cambia de tono cada ALARMA_MS
        ahora = time.ticks_ms()
        if time.ticks_diff(ahora, self.ultimo_cambio) >= config.ALARMA_MS:
            self.ultimo_cambio = ahora
            self.tono_agudo = not self.tono_agudo

        if self.tono_agudo:
            self.buzzer_agudo.duty(512)
            self.buzzer_grave.duty(0)
        else:
            self.buzzer_agudo.duty(0)
            self.buzzer_grave.duty(512)

    def actualizar(self, x1, x2, z, alerta):
        # Verde = sonido. Rojo = luz (fijo si hay alerta)
        self.led_verde.duty(int(x2 * 1023))
        if alerta:
            self.led_rojo.duty(1023)
        else:
            self.led_rojo.duty(int(x1 * x1 * 1023))  # x1*x1: el cambio se nota mas

        self.sonar_alarma(alerta)

        # La pantalla se refresca mas lento que el resto
        ahora = time.ticks_ms()
        if time.ticks_diff(ahora, self.ultimo_lcd) >= config.LCD_MS:
            self.ultimo_lcd = ahora
            linea1 = "Luz:%d%% Son:%d%%" % (int(x1 * 100), int(x2 * 99))
            if alerta:
                linea2 = "Z:%.1f ALERTA!" % z
            else:
                linea2 = "Z:%.1f NORMAL" % z
            self.lcd.escribir(linea1, linea2)