import time
from machine import Pin, PWM
import config


class LCDHelper:
    _RS = 0x01
    _EN = 0x04
    _BL = 0x08

    def __init__(self, i2c, addr=None):
        self.i2c = i2c
        self.addr = config.I2C_ADDR_LCD if addr is None else addr
        self.backlight = self._BL
        self.cache = ("", "")
        self.errors = 0
        self.ok = self._init_lcd()

    def _pulse(self, value):
        self.i2c.writeto(self.addr, bytes([value | self._EN, value]))

    def _write_byte(self, data, rs=0):
        base = rs | self.backlight
        self._pulse(base | (data & 0xF0))
        self._pulse(base | ((data << 4) & 0xF0))

    def _init_lcd(self):
        try:
            time.sleep_ms(60)
            for _ in range(3):
                self._pulse(self.backlight | 0x30)
                time.sleep_ms(6)
            self._pulse(self.backlight | 0x20)
            time.sleep_ms(6)
            for cmd in (0x28, 0x08, 0x01, 0x06, 0x0C):
                self._write_byte(cmd)
                time.sleep_ms(3)
            self.cache = ("", "")
            print("[LCD] Pantalla LCD1602 inicializada en 0x%02X" % self.addr)
            return True
        except Exception as e:
            self.errors += 1
            print("[LCD ERROR] No responde en 0x%02X:" % self.addr, e)
            return False

    def set_backlight(self, encendida=True):
        self.backlight = self._BL if encendida else 0x00
        if self.ok:
            try:
                self.i2c.writeto(self.addr, bytes([self.backlight]))
                self.cache = ("", "")
            except Exception:
                self.errors += 1

    def print_lines(self, line1, line2="", force=False):
        if not self.ok:
            return False
        texto1 = (str(line1)[:16] + " " * 16)[:16]
        texto2 = (str(line2)[:16] + " " * 16)[:16]
        repintar1 = force or texto1 != self.cache[0]
        repintar2 = force or texto2 != self.cache[1]
        if not repintar1 and not repintar2:
            return False
        try:
            if repintar1:
                self._write_byte(0x80)
                for caracter in texto1:
                    self._write_byte(ord(caracter), self._RS)
            if repintar2:
                self._write_byte(0xC0)
                for caracter in texto2:
                    self._write_byte(ord(caracter), self._RS)
            self.cache = (texto1, texto2)
            return True
        except Exception:
            self.errors += 1
            return False

    def clear(self):
        if not self.ok:
            return False
        try:
            self._write_byte(0x01)
            time.sleep_ms(2)
            self.cache = ("", "")
            return True
        except Exception:
            self.errors += 1
            return False


class ActuatorManager:
    def __init__(self, i2c_bus, pin_green=None, pin_red=None, pin_buzzer1=None, pin_buzzer2=None, lcd_addr=None):
        print("[ACTUADORES] Inicializando PWM Buzzer 1 (GPIO %d)..." % (
            config.PIN_BUZZER_1 if pin_buzzer1 is None else pin_buzzer1))
        self.buzzer1 = PWM(Pin(config.PIN_BUZZER_1 if pin_buzzer1 is None else pin_buzzer1), freq=2000, duty=0)

        print("[ACTUADORES] Inicializando PWM Buzzer 2 (GPIO %d)..." % (
            config.PIN_BUZZER_2 if pin_buzzer2 is None else pin_buzzer2))
        self.buzzer2 = PWM(Pin(config.PIN_BUZZER_2 if pin_buzzer2 is None else pin_buzzer2), freq=1000, duty=0)

        print("[ACTUADORES] Inicializando PWM LED Verde (GPIO %d)..." % (
            config.PIN_LED_GREEN if pin_green is None else pin_green))
        self.pwm_green = PWM(Pin(config.PIN_LED_GREEN if pin_green is None else pin_green), freq=config.PWM_FREQ_LED,
                             duty=0)

        print("[ACTUADORES] Inicializando PWM LED Rojo (GPIO %d)..." % (
            config.PIN_LED_RED if pin_red is None else pin_red))
        self.pwm_red = PWM(Pin(config.PIN_LED_RED if pin_red is None else pin_red), freq=config.PWM_FREQ_LED, duty=0)

        self.lcd = LCDHelper(i2c_bus, lcd_addr)
        self.alert_since = None
        self.alarm_step = 0
        self.alarm_step_time = 0
        self.last_lcd_update = 0
        self.peer_alert = None
        self.peer_until = 0
        self.alert_count = 0
        self.last_state = None

    def test_buzzers(self):
        print("--- Probando Buzzers ---")
        print("[PRUEBA BUZZER 1] Sonando a 2000Hz (150ms)...")
        self.buzzer1.freq(2000)
        self.buzzer1.duty(512)
        time.sleep_ms(150)
        self.buzzer1.duty(0)

        time.sleep_ms(100)

        print("[PRUEBA BUZZER 2] Sonando a 1000Hz (150ms)...")
        self.buzzer2.freq(1000)
        self.buzzer2.duty(512)
        time.sleep_ms(150)
        self.buzzer2.duty(0)
        print("[BUZZERS OK]")

    def test_leds(self):
        print("--- Probando LEDs PWM ---")
        print("[PRUEBA LED VERDE] Encendiendo...")
        self.pwm_green.duty(config.PWM_MAX_DUTY)
        time.sleep_ms(300)
        self.pwm_green.duty(0)

        print("[PRUEBA LED ROJO] Encendiendo...")
        self.pwm_red.duty(config.PWM_MAX_DUTY)
        time.sleep_ms(300)
        self.pwm_red.duty(0)
        print("[LEDS OK]")

    def _duty(self, value):
        if value < 0.0:
            value = 0.0
        elif value > 1.0:
            value = 1.0
        return int((value ** 2) * config.PWM_MAX_DUTY)

    def _stop_buzzers(self):
        self.buzzer1.duty(0)
        self.buzzer2.duty(0)

    def _update_alarm(self, now, alerta):
        if not alerta:
            self.alert_since = None
            self.alarm_step = 0
            self._stop_buzzers()
            return
        if self.alert_since is None:
            self.alert_since = now
            self.alert_count += 1
            self.alarm_step_time = now
        if time.ticks_diff(now, self.alert_since) < config.ALARM_DELAY_MS:
            self._stop_buzzers()
            return
        if time.ticks_diff(now, self.alarm_step_time) >= config.ALARM_PATTERN_MS:
            self.alarm_step_time = now
            self.alarm_step = 1 - self.alarm_step
            if self.alarm_step == 0:
                self.buzzer2.duty(0)
                self.buzzer1.freq(2000)
                self.buzzer1.duty(512)
            else:
                self.buzzer1.duty(0)
                self.buzzer2.freq(1000)
                self.buzzer2.duty(512)

    def _refresh_lcd(self, now, linea_luz, linea_sonido, alerta):
        peer_activo = (self.peer_alert is not None and time.ticks_diff(self.peer_until, now) > 0)
        if not peer_activo:
            self.peer_alert = None
            linea1 = config.NODE_NAME + (" ALERTA" if alerta else " NORMAL")
        else:
            linea1 = "ALERTA:" + str(self.peer_alert)[-9:]
        linea2 = linea_luz + " " + linea_sonido
        self.lcd.print_lines(linea1, linea2, force=alerta)

    def notify_peer_alert(self, nodo, ms=None):
        self.peer_alert = str(nodo)
        margen = config.PEER_ALERT_SHOW_MS if ms is None else ms
        self.peer_until = time.ticks_add(time.ticks_ms(), margen)
        print("[ACTUADORES] Alerta recibida de nodo remoto:", nodo)

    def set_state(self, now_ms, luz_contar, sonido_raw, alerta):
        ldr_max = config.LDR_REF if config.LIGHT_SENSOR.strip().lower().startswith("tsl") is False else 1.0
        if ldr_max <= 0:
            ldr_max = 1.0
        rl = luz_contar / ldr_max
        if rl > 1.0:
            rl = 1.0
        por_luz = int(rl * 100)
        por_sonido = int(sonido_raw * 100)
        if por_sonido > 99:
            por_sonido = 99

        if alerta:
            self.pwm_green.duty(0)
            self.pwm_red.duty(self._duty(1))   # rojo lleno cuando hay alarma remota
        else:
            self.pwm_green.duty(0)
            self.pwm_red.duty(self._duty(rl))  # rojo: mas luz = mas led rojo

        self._update_alarm(now_ms, alerta)

        if time.ticks_diff(now_ms, self.last_lcd_update) >= config.LCD_INTERVAL_MS:
            self.last_lcd_update = now_ms
            self._refresh_lcd(now_ms,
                              "L%d%%" % por_luz,
                              "S%d%%" % por_sonido,
                              alerta)
        self.last_state = {
            "luz": round(luz_contar, 1),
            "sonido_raw": round(sonido_raw, 1),
            "por_luz": por_luz,
            "por_sonido": por_sonido,
            "alerta": bool(alerta),
        }

        if now_ms - self.last_lcd_update >= config.LCD_INTERVAL_MS:
            self.last_lcd_update = now_ms
            self._refresh_lcd(now_ms,
                              "L%d%%" % por_luz,
                              "S%d%%" % por_sonido,
                              alerta)

        if now_ms - self.last_lcd_update >= config.LCD_INTERVAL_MS:
            self.last_lcd_update = now_ms
            self._refresh_lcd(now_ms,
                              "L%d%%" % por_luz,
                              "S%d%%" % por_sonido,
                              alerta)

        if now_ms - self.last_lcd_update >= config.LCD_INTERVAL_MS:
            self.last_lcd_update = now_ms
            self._refresh_lcd(now_ms,
                              "L%d%%" % por_luz,
                              "S%d%%" % por_sonido,
                              alerta)
        self.last_state = {
            "luz": round(luz_contar, 1),
            "sonido_raw": round(sonido_raw, 1),
            "por_luz": por_luz,
            "por_sonido": por_sonido,
            "alerta": bool(alerta),
        }

    def show_message(self, linea1, linea2=""):
        self.last_lcd_update = time.ticks_ms()
        return self.lcd.print_lines(linea1, linea2, force=True)

    def all_off(self):
        self.pwm_green.duty(0)
        self.pwm_red.duty(0)
        self._stop_buzzers()
        self.alert_since = None
        self.alarm_step = 0

    def status(self):
        return {
            "lcd_ok": self.lcd.ok,
            "lcd_errores": self.lcd.errors,
            "alertas": self.alert_count,
            "alerta_remota": self.peer_alert,
            "estado": self.last_state,
        }