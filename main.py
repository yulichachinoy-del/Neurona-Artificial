import sys
import time
import os
try:
    import uselect
except ImportError:
    import select as uselect
from machine import I2C, Pin
import config
from sensors import Sensores
from neuron import Neurona
from actuators import Actuadores
from Lcd import LCD


def escanear(sda, scl):
    i2c = I2C(0, sda=Pin(sda), scl=Pin(scl), freq=100000)
    return i2c, i2c.scan()


def aplicar_parametros_config(datos):
    """Guarda y activa los parámetros que llegan desde la interfaz por USB."""
    if len(datos) != 5:
        raise ValueError("Se esperaban cinco parámetros")
    valores = {
        "PESO_LUZ": float(datos[0]),
        "PESO_SONIDO": float(datos[1]),
        "SESGO": float(datos[2]),
        "MUESTRAS_ON": int(datos[3]),
        "MUESTRAS_OFF": int(datos[4]),
    }
    if valores["MUESTRAS_ON"] < 1 or valores["MUESTRAS_OFF"] < 1:
        raise ValueError("Las muestras deben ser mayores que cero")

    try:
        with open("config.py", "r") as archivo:
            lineas = archivo.readlines()
        encontrados = {}
        for indice in range(len(lineas)):
            linea = lineas[indice]
            for nombre in valores:
                if linea.startswith(nombre + " ="):
                    lineas[indice] = "%s = %s\n" % (nombre, valores[nombre])
                    encontrados[nombre] = True
        if len(encontrados) != len(valores):
            raise ValueError("Faltan parámetros en config.py")

        with open("config.tmp", "w") as archivo:
            for linea in lineas:
                archivo.write(linea)
        try:
            os.remove("config.py")
        except OSError:
            pass
        os.rename("config.tmp", "config.py")
    except Exception as error:
        # Los valores sí quedan activos durante esta ejecución aunque no se
        # hayan podido guardar en el sistema de archivos de la placa.
        for nombre in valores:
            setattr(config, nombre, valores[nombre])
        return str(error)

    for nombre in valores:
        setattr(config, nombre, valores[nombre])
    return None


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

    # Escucha comandos de la interfaz sin detener la lectura de sensores.
    poll_usb = uselect.poll()
    poll_usb.register(sys.stdin, uselect.POLLIN)

    print("Sistema en marcha")
    print("PARAMS:ACTIVOS:%s,%s,%s,%s,%s" % (
        config.PESO_LUZ, config.PESO_SONIDO, config.SESGO,
        config.MUESTRAS_ON, config.MUESTRAS_OFF,
    ))
    alerta_anterior = False
    ultimo_print = time.ticks_ms()
    ultima_telemetria = time.ticks_ms()

    while True:
        if poll_usb.poll(0):
            comando = sys.stdin.readline().strip()
            if comando == "RECALIBRAR":
                actuadores.apagar_todo()
                lcd.escribir("Calibrando...", "Silencio, por favor")
                sensores.calibrar()
                neurona.reiniciar()
                alerta_anterior = False
                lcd.escribir("Sistema listo", "")
                time.sleep_ms(400)
            elif comando.startswith("PARAMS:"):
                try:
                    error_guardado = aplicar_parametros_config(comando[7:].split(","))
                    neurona.reiniciar()
                    if error_guardado:
                        print("PARAMS:OK:VOLATILE", error_guardado)
                    else:
                        print("PARAMS:OK")
                except Exception as error:
                    print("PARAMS:ERROR", error)

        # Boton: recalibrar
        if sensores.boton_pulsado():
            actuadores.apagar_todo()
            lcd.escribir("Calibrando...", "Espere...")
            sensores.calibrar()
            neurona.reiniciar()
            while sensores.boton_pulsado():  # Esperar a que suelten el boton
                time.sleep_ms(50)
            lcd.escribir("Sistema listo", "")

        # Leer, decidir y actuar
        x1, x2, luz, ruido = sensores.leer_entradas()
        z, alerta = neurona.calcular(x1, x2)
        actuadores.actualizar(x1, x2, z, alerta)

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
            print("LDR crudo:", luz, "| ambiente:", sensores.luz_ambiente, "| x1: %.2f" % x1)

        time.sleep_ms(10)

main()
