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
        self.writes_ok = 0
        self.last_init_try = 0
        self.ok = False
        self._init_lcd()

    @staticmethod
    def _clean_ascii(texto):
        res = []
        for ch in str(texto):
            code = ord(ch)
            if 32 <= code <= 126:
                res.append(ch)
            else:
                res.append("?")
        return "".join(res)

    def _pulse(self, val):
        """Envia un pulso de Enable (EN=1 -> EN=0) identico al driver clasico de LCD1602."""
        self.i2c.writeto(self.addr, bytes([val | self._EN]))
        time.sleep_us(50)
        self.i2c.writeto(self.addr, bytes([val & ~self._EN]))
        time.sleep_us(50)

    def _write_byte(self, data, rs=0):
        """Envia 1 byte en modo 4-bits (nibble alto y luego nibble bajo) con pausas seguras."""
        base = rs | self.backlight
        self._pulse(base | (data & 0xF0))
        self._pulse(base | ((data << 4) & 0xF0))

    def _init_lcd(self):
        self.last_init_try = time.ticks_ms()
        print("[LCD INIT] Buscando pantalla en direccion 0x%02X..." % self.addr)
        try:
            encontrados = self.i2c.scan()
            if self.addr not in encontrados:
                print("[LCD WARN] 0x%02X no detectado en bus I2C (vistos: %s)"
                      % (self.addr, [hex(x) for x in encontrados]))
                for alt_addr in (0x27, 0x3F):
                    if alt_addr in encontrados:
                        print("[LCD AUTO-DETECT] Usando direccion detectada 0x%02X" % alt_addr)
                        self.addr = alt_addr
                        break
        except Exception as e:
            print("[LCD WARN] Error escaneando I2C:", e)

        try:
            time.sleep_ms(60)
            self.i2c.writeto(self.addr, bytes([self.backlight]))
            time.sleep_ms(10)

            # Secuencia estandar de reseteo HD44780 a 4 bits
            for _ in range(3):
                self._pulse(self.backlight | 0x30)
                time.sleep_ms(5)
            self._pulse(self.backlight | 0x20)
            time.sleep_ms(5)

            for cmd in (0x28, 0x08, 0x01, 0x06, 0x0C):
                self._write_byte(cmd, 0)
                time.sleep_ms(3)

            self.cache = ("", "")
            self.ok = True
            print("[LCD OK] Pantalla LCD1602 inicializada en 0x%02X" % self.addr)
            return True
        except Exception as e:
            self.errors += 1
            self.ok = False
            print("[LCD ERROR] No responde en 0x%02X (errores=%d):" % (self.addr, self.errors), e)
            return False

    def ping(self):
        try:
            self.i2c.writeto(self.addr, bytes([self.backlight]))
            return True
        except Exception as e:
            self.errors += 1
            self.ok = False
            print("[LCD PING ERROR] Pantalla desconectada en 0x%02X:" % self.addr, e)
            return False

    def set_backlight(self, encendida=True):
        self.backlight = self._BL if encendida else 0x00
        if self.ok:
            try:
                self.i2c.writeto(self.addr, bytes([self.backlight]))
            except Exception:
                self.errors += 1
                self.ok = False

    def print_lines(self, line1, line2="", force=False):
        if not self.ok:
            ahora = time.ticks_ms()
            retry_ms = getattr(config, "LCD_RETRY_MS", 5000)
            if not force and time.ticks_diff(ahora, self.last_init_try) < retry_ms:
                return False
            if not self._init_lcd():
                return False
            force = True

        texto1 = "%-16.16s" % self._clean_ascii(line1)
        texto2 = "%-16.16s" % self._clean_ascii(line2)
        repintar1 = force or (texto1 != self.cache[0])
        repintar2 = force or (texto2 != self.cache[1])
        if not repintar1 and not repintar2:
            return False
        try:
            if repintar1:
                self._write_byte(0x80, 0)
                for caracter in texto1:
                    self._write_byte(ord(caracter), self._RS)
            if repintar2:
                self._write_byte(0xC0, 0)
                for caracter in texto2:
                    self._write_byte(ord(caracter), self._RS)
            self.cache = (texto1, texto2)
            self.writes_ok += 1
            if getattr(config, "LCD_LOG_WRITES", True):
                print("[LCD WRITE #%d OK] F1: '%s' | F2: '%s'" % (self.writes_ok, texto1, texto2))
            return True
        except Exception as e:
            self.errors += 1
            self.ok = False
            print("[LCD WRITE ERROR] Fallo I2C en 0x%02X:" % self.addr, e)
            return False

    def clear(self):
        if not self.ok:
            return False
        try:
            self._write_byte(0x01, 0)
            time.sleep_ms(3)
            self.cache = ("", "")
            return True
        except Exception:
            self.errors += 1
            self.ok = False
            return False


class ActuatorManager:
    def __init__(self, i2c_bus, pin_green=None, pin_red=None, pin_buzzer1=None, pin_buzzer2=None, lcd_addr=None):
        p_b1 = config.PIN_BUZZER_1 if pin_buzzer1 is None else pin_buzzer1
        p_b2 = config.PIN_BUZZER_2 if pin_buzzer2 is None else pin_buzzer2
        p_lg = config.PIN_LED_GREEN if pin_green is None else pin_green
        p_lr = config.PIN_LED_RED if pin_red is None else pin_red

        print("[ACTUADORES] Inicializando PWM Buzzer 1 (GPIO %d)..." % p_b1)
        self.buzzer1 = PWM(Pin(p_b1), freq=2000, duty=0)

        print("[ACTUADORES] Inicializando PWM Buzzer 2 (GPIO %d)..." % p_b2)
        self.buzzer2 = PWM(Pin(p_b2), freq=1000, duty=0)

        print("[ACTUADORES] Inicializando PWM LED Verde (GPIO %d)..." % p_lg)
        self.pwm_green = PWM(Pin(p_lg), freq=config.PWM_FREQ_LED, duty=0)

        print("[ACTUADORES] Inicializando PWM LED Rojo (GPIO %d)..." % p_lr)
        self.pwm_red = PWM(Pin(p_lr), freq=config.PWM_FREQ_LED, duty=0)

        self.duty_green = 0
        self.duty_red = 0
        self.lcd = LCDHelper(i2c_bus, lcd_addr)
        self.alert_since = None
        self.alarm_active = False
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
        self.buzzer1.duty(512)
        time.sleep_ms(150)
        self.buzzer1.duty(0)

        time.sleep_ms(100)

        print("[PRUEBA BUZZER 2] Sonando a 1000Hz (150ms)...")
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

    def test_lcd(self):
        print("--- Probando Pantalla LCD1602 I2C ---")
        if not self.lcd.ok:
            print("[PRUEBA LCD ERROR] Pantalla no detectada en 0x%02X. Revisa SDA/SCL y 5V." % self.lcd.addr)
            return False

        print("[PRUEBA LCD] Parpadeando luz de fondo...")
        self.lcd.set_backlight(False)
        time.sleep_ms(300)
        self.lcd.set_backlight(True)
        time.sleep_ms(300)

        ok = self.show_message("Test Hardware", config.NODE_NAME)
        if ok:
            print("[PRUEBA LCD OK] Texto enviado a 0x%02X correctamente." % self.lcd.addr)
        else:
            print("[PRUEBA LCD ERROR] Fallo al enviar texto de prueba.")
        return ok

    @staticmethod
    def _duty(value):
        if value <= 0.0:
            return 0
        if value >= 1.0:
            return config.PWM_MAX_DUTY
        return int((value * value) * config.PWM_MAX_DUTY)

    def _stop_buzzers(self):
        self.buzzer1.duty(0)
        self.buzzer2.duty(0)

    def _update_alarm(self, now, alerta):
        if not alerta:
            if self.alert_since is not None or self.alarm_active:
                self.alert_since = None
                self.alarm_active = False
                self.alarm_step = 0
                self._stop_buzzers()
            return

        if self.alert_since is None:
            self.alert_since = now
            self.alert_count += 1
            self.alarm_active = False

        if time.ticks_diff(now, self.alert_since) < config.ALARM_DELAY_MS:
            return

        if not self.alarm_active:
            self.alarm_active = True
            self.alarm_step = 0
            self.alarm_step_time = now
            self.buzzer2.duty(0)
            self.buzzer1.duty(512)
            return

        if time.ticks_diff(now, self.alarm_step_time) >= config.ALARM_PATTERN_MS:
            self.alarm_step_time = now
            self.alarm_step = 1 - self.alarm_step
            if self.alarm_step == 0:
                self.buzzer2.duty(0)
                self.buzzer1.duty(512)
            else:
                self.buzzer1.duty(0)
                self.buzzer2.duty(512)

    def _refresh_lcd(self, now, por_luz, por_sonido, z, alerta):
        peer_activo = (self.peer_alert is not None and time.ticks_diff(self.peer_until, now) > 0)
        if not peer_activo:
            self.peer_alert = None
            linea1 = config.NODE_NAME + (" ALERTA" if alerta else " NORMAL")
        else:
            linea1 = "ALERTA:" + str(self.peer_alert)[-9:]
        linea2 = "L%d%% S%d%% Z%.1f" % (por_luz, por_sonido, z)
        self.lcd.print_lines(linea1, linea2)

    def notify_peer_alert(self, nodo, ms=None):
        self.peer_alert = str(nodo)
        margen = config.PEER_ALERT_SHOW_MS if ms is None else ms
        self.peer_until = time.ticks_add(time.ticks_ms(), margen)
        print("[ACTUADORES] Alerta recibida de nodo remoto:", nodo)

    def set_state(self, x1, x2, z, alerta):
        now_ms = time.ticks_ms()

        por_luz = min(100, max(0, int(x1 * 100)))
        por_sonido = min(99, max(0, int(x2 * 100)))

        if alerta:
            self.duty_green = 0
            self.duty_red = max(300, self._duty(x2))
        else:
            self.duty_green = self._duty(x1)
            self.duty_red = 0

        self.pwm_green.duty(self.duty_green)
        self.pwm_red.duty(self.duty_red)

        self._update_alarm(now_ms, alerta)

        if time.ticks_diff(now_ms, self.last_lcd_update) >= config.LCD_INTERVAL_MS:
            self.last_lcd_update = now_ms
            self._refresh_lcd(now_ms, por_luz, por_sonido, z, alerta)

        self.last_state = {
            "x1": round(x1, 3),
            "x2": round(x2, 3),
            "z": round(z, 2),
            "por_luz": por_luz,
            "por_sonido": por_sonido,
            "alerta": bool(alerta),
        }

    def show_message(self, linea1, linea2=""):
        self.last_lcd_update = time.ticks_ms()
        return self.lcd.print_lines(linea1, linea2, force=True)

    def all_off(self):
        self.duty_green = 0
        self.duty_red = 0
        self.pwm_green.duty(0)
        self.pwm_red.duty(0)
        self._stop_buzzers()
        self.alert_since = None
        self.alarm_active = False
        self.alarm_step = 0

    def status(self):
        return {
            "lcd_ok": self.lcd.ok,
            "lcd_addr": hex(self.lcd.addr),
            "lcd_writes": self.lcd.writes_ok,
            "lcd_errores": self.lcd.errors,
            "alertas": self.alert_count,
            "alerta_remota": self.peer_alert,
            "estado": self.last_state,
        }
