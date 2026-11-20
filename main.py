import sys
import time
import uselect
from machine import I2C, Pin
import config
from sensors import Sensores
from neuron import Neurona
from actuators import Actuadores
from Lcd import LCD


def escanear(sda, scl):
    i2c = I2C(0, sda=Pin(sda), scl=Pin(scl), freq=100000)
    return i2c, i2c.scan()


def ejecutar_recalibracion(sensores, neurona, actuadores, lcd):
    actuadores.apagar_todo()
    lcd.escribir("Calibrando...", "Silencio, por favor")
    sensores.calibrar()
    neurona.reiniciar()
    lcd.escribir("Sistema listo", "")
    time.sleep_ms(400)


def main():
    print("Arrancando en 3 s (Ctrl+C para interrumpir)...")
    time.sleep(3)

    # --- Buscar la LCD en el bus I2C ---
    print("Buscando LCD con SDA=%d, SCL=%d ..." % (config.PIN_SDA, config.PIN_SCL))
    i2c, dispositivos = escanear(config.PIN_SDA, config.PIN_SCL)

    if not dispositivos:
        print("Nada. Probando con SDA y SCL invertidos...")
        i2c, dispositivos = escanear(config.PIN_SCL, config.PIN_SDA)
        if dispositivos:
            print("Tus cables estan al reves. Intercambia PIN_SDA y PIN_SCL en config.py")

    if dispositivos:
        direccion = dispositivos[0]
        print("Dispositivos encontrados (decimal):", dispositivos)
        print("ID de la LCD:", hex(direccion))
    else:
        direccion = None
        print("NO se detecta ningun dispositivo I2C.")
        print("Revisa: VCC a 5V, GND comun, cables SDA/SCL y soldaduras.")

    # --- Crear los objetos ---
    lcd = LCD(i2c, direccion)
    sensores = Sensores()
    neurona = Neurona()
    actuadores = Actuadores(lcd)
    actuadores.probar()

    # --- Calibrar ---
    lcd.escribir("Calibrando...", "Silencio, por favor")
    sensores.calibrar()
    lcd.escribir("Sistema listo", "")
    time.sleep(1)

    # --- Configurar escucha no bloqueante del USB Serial ---
    poll_usb = uselect.poll()
    poll_usb.register(sys.stdin, uselect.POLLIN)

    print("Sistema en marcha")
    alerta_anterior = False
    ultimo_print = time.ticks_ms()
    ultima_telemetria = time.ticks_ms()

    while True:
        # 1. Revisar si la interfaz PC envió orden de recalibrar por USB
        if poll_usb.poll(0):
            comando = sys.stdin.readline().strip().upper()
            if comando == "RECALIBRAR":
                ejecutar_recalibracion(sensores, neurona, actuadores, lcd)
                alerta_anterior = False

        # 2. Boton físico: recalibrar
        if sensores.boton_pulsado():
            ejecutar_recalibracion(sensores, neurona, actuadores, lcd)
            alerta_anterior = False
            while sensores.boton_pulsado():
                time.sleep_ms(50)

        # 3. Leer, decidir y actuar
        x1, x2, luz, ruido = sensores.leer_entradas()
        z, alerta = neurona.calcular(x1, x2)
        actuadores.actualizar(x1, x2, z, alerta)

        # 4. Enviar datos en tiempo real a la interfaz PC (cada 200 ms)
        ahora = time.ticks_ms()
        if time.ticks_diff(ahora, ultima_telemetria) >= 200:
            ultima_telemetria = ahora
            print("DATA:%.3f,%.3f,%.3f,%d" % (x1, x2, z, 1 if alerta else 0))

        # Avisar por consola solo cuando cambia la alerta
        if alerta != alerta_anterior:
            alerta_anterior = alerta
            print("Alerta:", alerta, "| Z:", z, "| luz:", luz, "| ruido:", ruido)

        # Depuracion del LDR: una linea por segundo
        if config.DEPURAR and time.ticks_diff(ahora, ultimo_print) >= 1000:
            ultimo_print = ahora
            print("LDR crudo:", luz, "| min:", sensores.luz_min, "| max:", sensores.luz_max, "| x1: %.2f" % x1)

        time.sleep_ms(10)


main()