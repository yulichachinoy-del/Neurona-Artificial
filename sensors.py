import time
from machine import Pin, ADC
import config


class TSL2561:
    def __init__(self, i2c, addr=config.I2C_ADDR_TSL2561):
        self.i2c = i2c
        self.addr = addr
        self.errors = 0
        self.last_lux = 0.0
        self.ok = self.init()

    def init(self):
        try:
            self.i2c.writeto_mem(self.addr, 0x80, bytes([0x03]))
            self.i2c.writeto_mem(self.addr, 0x81, bytes([0x02]))
            print("[SENSOR TSL2561] Inicializado correctamente en 0x%02X" % self.addr)
            return True
        except Exception as e:
            self.errors += 1
            print("[SENSOR TSL2561] ERROR de inicializacion en 0x%02X:" % self.addr, e)
            return False

    def read_lux(self):
        try:
            ch0_low = self.i2c.readfrom_mem(self.addr, 0x8C, 1)[0]
            ch0_high = self.i2c.readfrom_mem(self.addr, 0x8D, 1)[0]
            ch1_low = self.i2c.readfrom_mem(self.addr, 0x8E, 1)[0]
            ch1_high = self.i2c.readfrom_mem(self.addr, 0x8F, 1)[0]

            ch0 = (ch0_high << 8) | ch0_low
            ch1 = (ch1_high << 8) | ch1_low

            if ch0 == 0:
                return 0.0

            ratio = ch1 / ch0
            if ratio <= 0.50:
                lux = (0.0304 * ch0) - (0.062 * ch0 * (ratio ** 1.4))
            elif ratio <= 0.61:
                lux = (0.0224 * ch0) - (0.031 * ch1)
            elif ratio <= 0.80:
                lux = (0.0128 * ch0) - (0.0153 * ch1)
            elif ratio <= 1.30:
                lux = (0.00146 * ch0) - (0.00112 * ch1)
            else:
                lux = 0.0

            self.last_lux = max(0.0, lux)
            return self.last_lux
        except Exception as e:
            self.errors += 1
            if config.DEBUG:
                print("[SENSOR TSL2561] Error de lectura:", e)
            return self.last_lux


class LDRSensor:
    """Fotoresistencia leida por ADC (modulo KY-018 o divisor LDR + resistencia).

    Devuelve cuentas ADC (0..ADC_MAX) en lugar de lux, pero con la misma
    interfaz que el TSL2561 para no tocar la logica de la neurona.
    """

    def __init__(self, pin=config.PIN_LDR_AO):
        self.pin_num = pin
        print("[SENSOR LDR] Configurando ADC de fotoresistencia (GPIO %d)..." % pin)
        self.adc = ADC(Pin(pin, Pin.IN))
        try:
            self.adc.atten(ADC.ATTN_11DB)      # fondo de escala ~3.3 V
            self.adc.width(ADC.WIDTH_12BIT)    # 0..4095
        except Exception as e:
            print("[SENSOR LDR] Aviso configurando el ADC:", e)
        self.errors = 0
        self.last_raw = 0
        self.ok = True
        print("[SENSOR LDR] Fotoresistencia lista (invertida=%s, muestras=%d)"
              % (config.LDR_INVERT, config.LDR_SAMPLES))

    def read_raw(self):
        """Promedio de varias lecturas para quitar el ruido del ADC."""
        muestras = config.LDR_SAMPLES if config.LDR_SAMPLES > 0 else 1
        total = 0
        try:
            for _ in range(muestras):
                total += self.adc.read()
        except Exception as e:
            self.errors += 1
            if config.DEBUG:
                print("[SENSOR LDR] Error de lectura:", e)
            return self.last_raw
        valor = total // muestras
        if config.LDR_INVERT:
            valor = config.ADC_MAX - valor
        self.last_raw = valor
        return valor

    def read_lux(self):
        """Se mantiene el nombre para que SensorManager no cambie."""
        return float(self.read_raw())


class SensorManager:
    def __init__(self, i2c_bus):
        print("[SENSORES] Configurando entrada de boton (GPIO %d)..." % config.PIN_BTN_CAL)
        self.btn_cal = Pin(config.PIN_BTN_CAL, Pin.IN, Pin.PULL_UP)

        print("[SENSORES] Configurando ADC de microfono (GPIO %d)..." % config.PIN_KY038_AO)
        self.mic_adc = ADC(Pin(config.PIN_KY038_AO))
        self.mic_adc.atten(ADC.ATTN_11DB)

        tipo = config.LIGHT_SENSOR.strip().lower()
        if tipo.startswith("tsl"):
            print("[SENSORES] Modulo de luz seleccionado: TSL2561 (I2C)")
            self.light_type = "tsl2561"
            self.light_sensor = TSL2561(i2c_bus)
        else:
            print("[SENSORES] Modulo de luz seleccionado: LDR (GPIO %d)" % config.PIN_LDR_AO)
            self.light_type = "ldr"
            self.light_sensor = LDRSensor()
        self.light_ok = self.light_sensor.ok

        self.lux_floor = 0.0
        self.mic_floor = 0

    def test_sensors(self):
        print("--- Probrando lecturas iniciales de sensores ---")
        mic_test = self.read_mic_peak(10)
        print("[PRUEBA MIC] Lectura de pico inicial (10ms): %d ADC" % mic_test)

        luz_test = self.read_light()
        if self.light_type == "ldr":
            print("[PRUEBA LUZ] LDR en GPIO %d -> %d cuentas ADC (ref %d)"
                  % (config.PIN_LDR_AO, self.light_sensor.last_raw, config.LDR_REF))
        print("[PRUEBA LUZ] Lectura inicial de luz: %.2f" % luz_test)

        btn_val = self.is_button_pressed()
        print("[PRUEBA BOTON] Estado inicial: %s" % ("PRESIONADO (LOW)" if btn_val else "NO PRESIONADO (HIGH)"))

    def is_button_pressed(self):
        return self.btn_cal.value() == 0

    def read_mic_peak(self, window_ms=config.SAMPLING_WINDOW_MS):
        start = time.ticks_ms()
        min_val = config.ADC_MAX
        max_val = 0
        while time.ticks_diff(time.ticks_ms(), start) < window_ms:
            val = self.mic_adc.read()
            if val < min_val:
                min_val = val
            if val > max_val:
                max_val = val
        return max_val - min_val

    def read_light(self):
        if self.light_sensor is None:
            return 0.0
        return self.light_sensor.read_lux()

    def calibrate(self):
        print("[CALIBRACION] Iniciando autocalibracion de ambiente (%d ms)..." % config.CALIBRATION_MS)
        lux_samples = []
        mic_samples = []
        step_ms = max(1, config.CALIBRATION_MS // config.CALIBRATION_SAMPLES)

        for i in range(config.CALIBRATION_SAMPLES):
            lux_samples.append(self.read_light())
            mic_samples.append(self.read_mic_peak(10))
            time.sleep_ms(step_ms)

        lux_samples.sort()
        mic_samples.sort()

        idx = int((config.CALIB_FLOOR_PERCENTILE / 100.0) * len(lux_samples))
        self.lux_floor = lux_samples[idx]
        self.mic_floor = mic_samples[idx]
        print("[CALIBRACION OK] Suelo de Luz: %.2f | Suelo de Ruido: %d ADC" % (self.lux_floor, self.mic_floor))

    def get_normalized_inputs(self):
        raw_light = self.read_light()
        raw_mic = self.read_mic_peak()

        lux_diff = max(0.0, raw_light - self.lux_floor)
        mic_diff = max(0, raw_mic - self.mic_floor)

        ref_light = config.LUX_REF if self.light_type == "tsl2561" else config.LDR_REF
        if ref_light <= 0:
            ref_light = 1.0
        x1 = min(1.0, lux_diff / ref_light)
        x2 = min(1.0, mic_diff / config.MIC_REF)

        return x1, x2, raw_light, raw_mic