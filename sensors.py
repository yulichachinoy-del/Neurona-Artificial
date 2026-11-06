import gc
import time
from machine import Pin, ADC
import config


class TSL2561:
    def __init__(self, i2c, addr=config.I2C_ADDR_TSL2561):
        self.i2c = i2c
        self.addr = addr
        self.errors = 0
        self.last_lux = 0.0
        self._buf = bytearray(2)
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
            self.i2c.readfrom_mem_into(self.addr, 0xAC, self._buf)
            ch0 = (self._buf[1] << 8) | self._buf[0]
            self.i2c.readfrom_mem_into(self.addr, 0xAE, self._buf)
            ch1 = (self._buf[1] << 8) | self._buf[0]

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
    def __init__(self, pin=config.PIN_LDR_AO):
        self.pin_num = pin
        print("[SENSOR LDR] Configurando ADC de fotoresistencia (GPIO %d)..." % pin)
        self.adc = ADC(Pin(pin, Pin.IN))
        try:
            self.adc.atten(ADC.ATTN_11DB)
            self.adc.width(ADC.WIDTH_12BIT)
        except Exception as e:
            print("[SENSOR LDR] Aviso configurando el ADC:", e)
        self.errors = 0
        self.last_adc_puro = 0
        self.last_raw = 0
        self.ok = True
        self._samples = max(1, config.LDR_SAMPLES)
        print("[SENSOR LDR] Fotoresistencia lista (invertida=%s, muestras=%d)"
              % (config.LDR_INVERT, self._samples))

    def read_raw(self):
        total = 0
        try:
            for _ in range(self._samples):
                total += self.adc.read()
        except Exception as e:
            self.errors += 1
            if config.DEBUG:
                print("[SENSOR LDR] Error de lectura:", e)
            return self.last_raw

        adc_puro = total // self._samples
        self.last_adc_puro = adc_puro

        if config.LDR_INVERT:
            valor = config.ADC_MAX - adc_puro
        else:
            valor = adc_puro

        self.last_raw = max(0, min(config.ADC_MAX, valor))
        return self.last_raw

    def read_lux(self):
        return float(self.read_raw())


class SensorManager:
    def __init__(self, i2c_bus):
        print("[SENSORES] Configurando entrada de boton (GPIO %d)..." % config.PIN_BTN_CAL)
        self.btn_cal = Pin(config.PIN_BTN_CAL, Pin.IN, Pin.PULL_UP)

        print("[SENSORES] Configurando ADC de microfono (GPIO %d)..." % config.PIN_KY038_AO)
        self.mic_adc = ADC(Pin(config.PIN_KY038_AO, Pin.IN))
        try:
            self.mic_adc.atten(ADC.ATTN_11DB)
            self.mic_adc.width(ADC.WIDTH_12BIT)
        except Exception:
            pass

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
        self.last_mic_dc = 0

    def test_sensors(self):
        print("--- Probando lecturas iniciales de sensores ---")
        mic_test = self.read_mic_peak(40)
        print("[PRUEBA MIC] Nivel DC=%d ADC | Pico-a-Pico (40ms)=%d ADC (ref=%d)"
              % (self.last_mic_dc, mic_test, config.MIC_REF))
        if self.last_mic_dc in (0, config.ADC_MAX):
            print("[PRUEBA MIC WARN] El pin AO del microfono esta saturado en %d. Gira el tornillo del KY-038."
                  % self.last_mic_dc)

        luz_test = self.read_light()
        if self.light_type == "ldr":
            print("[PRUEBA LUZ] LDR GPIO %d -> ADC puro=%d | Luz corregida=%.0f (invert=%s, ref=%d)"
                  % (config.PIN_LDR_AO, self.light_sensor.last_adc_puro, luz_test, config.LDR_INVERT, config.LDR_REF))
        else:
            print("[PRUEBA LUZ] Lectura inicial TSL2561: %.2f lux" % luz_test)

        btn_val = self.is_button_pressed()
        print("[PRUEBA BOTON] Estado inicial: %s" % ("PRESIONADO (LOW)" if btn_val else "NO PRESIONADO (HIGH)"))

    def is_button_pressed(self):
        return self.btn_cal.value() == 0

    def read_mic_peak(self, window_ms=config.SAMPLING_WINDOW_MS):
        """Mide la amplitud pico-a-pico de la onda de audio en la ventana de tiempo."""
        start = time.ticks_ms()
        min_val = config.ADC_MAX
        max_val = 0
        suma = 0
        conteo = 0
        adc_read = self.mic_adc.read
        ticks_ms = time.ticks_ms
        ticks_diff = time.ticks_diff

        while ticks_diff(ticks_ms(), start) < window_ms:
            val = adc_read()
            if val < min_val:
                min_val = val
            if val > max_val:
                max_val = val
            suma += val
            conteo += 1

        if conteo > 0:
            self.last_mic_dc = suma // conteo
        if max_val < min_val:
            return 0
        return max_val - min_val

    def read_light(self):
        if self.light_sensor is None:
            return 0.0
        return self.light_sensor.read_lux()

    def calibrate(self, wdt_cb=None):
        print("[CALIBRACION] Iniciando autocalibracion de ambiente (%d ms)..." % config.CALIBRATION_MS)
        n_samples = max(1, config.CALIBRATION_SAMPLES)
        lux_samples = [0.0] * n_samples
        mic_samples = [0] * n_samples
        step_ms = max(1, config.CALIBRATION_MS // n_samples)

        for i in range(n_samples):
            if wdt_cb:
                wdt_cb()
            lux_samples[i] = self.read_light()
            mic_samples[i] = self.read_mic_peak(15)
            time.sleep_ms(step_ms)

        lux_samples.sort()
        mic_samples.sort()

        idx_lux = min(n_samples - 1, max(0, int((config.CALIB_FLOOR_PERCENTILE / 100.0) * n_samples)))
        # Para el microfono usamos el percentil 75 del silencio para evitar falsas alarmas por ruido electrico
        idx_mic = min(n_samples - 1, max(0, int(0.75 * n_samples)))

        self.lux_floor = lux_samples[idx_lux]
        self.mic_floor = mic_samples[idx_mic]
        print("[CALIBRACION OK] Suelo Luz: %.1f | Suelo Ruido Mic: %d ADC (DC=%d)"
              % (self.lux_floor, self.mic_floor, self.last_mic_dc))
        gc.collect()

    def get_normalized_inputs(self):
        raw_light = self.read_light()
        raw_mic = self.read_mic_peak()

        ref_light = float(config.LUX_REF if self.light_type == "tsl2561" else config.LDR_REF)
        if ref_light <= 0.0:
            ref_light = 1.0

        # Si LDR_ABSOLUTE_MODE es True, x1 refleja directamente el nivel de luz (0..1)
        # Asi el LED verde brilla cuando hay luz y se apaga al tapar la fotoresistencia.
        if self.light_type == "ldr" and getattr(config, "LDR_ABSOLUTE_MODE", True):
            x1 = min(1.0, max(0.0, raw_light / ref_light))
        else:
            lux_diff = max(0.0, raw_light - self.lux_floor)
            x1 = min(1.0, lux_diff / ref_light)

        mic_diff = max(0, raw_mic - self.mic_floor)
        ref_mic = max(1.0, float(config.MIC_REF))
        x2 = min(1.0, mic_diff / ref_mic)

        return x1, x2, raw_light, raw_mic
