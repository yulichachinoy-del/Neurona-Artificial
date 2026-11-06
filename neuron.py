import config


class Neurona:
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.contador_on = 0
        self.contador_off = 0
        self.alerta = False

    def calcular(self, x1, x2):
        z = x1 * config.PESO_LUZ + x2 * config.PESO_SONIDO + config.SESGO

        # La alerta solo cambia si el resultado se repite varias veces seguidas
        if z >= 0:
            self.contador_on += 1
            self.contador_off = 0
            if self.contador_on >= config.MUESTRAS_ON:
                self.alerta = True
        else:
            self.contador_off += 1
            self.contador_on = 0
            if self.contador_off >= config.MUESTRAS_OFF:
                self.alerta = False

        return z, self.alerta