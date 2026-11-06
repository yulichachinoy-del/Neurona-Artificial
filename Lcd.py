import time

# NOTA: esta clase es "caja negra". Solo hay que usar:
#   lcd = LCD(i2c, direccion)
#   lcd.escribir("linea 1", "linea 2")
# El resto es el protocolo interno que usa la pantalla (4 bits por I2C).


class LCD:
    def __init__(self, i2c, direccion):
        self.i2c = i2c
        self.direccion = direccion
        self.ok = False

        if direccion is None:
            print("[LCD] Sin direccion: se trabaja sin pantalla")
            return

        try:
            time.sleep_ms(50)
            for i in range(3):
                self.enviar_mitad(0x30)
                time.sleep_ms(5)
            self.enviar_mitad(0x20)
            time.sleep_ms(5)
            # Modo 4 bits, apagar, borrar, modo escritura, encender
            for comando in (0x28, 0x08, 0x01, 0x06, 0x0C):
                self.enviar_byte(comando, False)
                time.sleep_ms(3)
            self.ok = True
            print("[LCD] Lista en", hex(direccion))
        except OSError:
            print("[LCD] No responde. Revisa los cables")

    def enviar_mitad(self, valor):
        # 0x08 = luz de fondo, 0x04 = pulso "enable"
        self.i2c.writeto(self.direccion, bytes([valor | 0x08 | 0x04]))
        time.sleep_us(50)
        self.i2c.writeto(self.direccion, bytes([(valor | 0x08) & 0xFB]))
        time.sleep_us(50)

    def enviar_byte(self, dato, es_caracter):
        modo = 1 if es_caracter else 0
        self.enviar_mitad((dato & 0xF0) | modo)
        self.enviar_mitad(((dato << 4) & 0xF0) | modo)

    def escribir(self, linea1, linea2=""):
        if not self.ok:
            return
        # Rellena con espacios y corta a 16 caracteres
        linea1 = (linea1 + " " * 16)[:16]
        linea2 = (linea2 + " " * 16)[:16]
        try:
            self.enviar_byte(0x80, False)  # Cursor al inicio de la linea 1
            for letra in linea1:
                self.enviar_byte(ord(letra), True)
            self.enviar_byte(0xC0, False)  # Cursor al inicio de la linea 2
            for letra in linea2:
                self.enviar_byte(ord(letra), True)
        except OSError:
            pass  # Si falla una vez, se intenta en la siguiente vuelta