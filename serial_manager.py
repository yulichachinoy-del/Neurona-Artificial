import threading
import time

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


class SerialManager:
    def __init__(self, on_data_received, on_status_change):
        self.on_data_received = on_data_received
        self.on_status_change = on_status_change
        self.ser = None
        self.conectado = False
        self._running = False

    def listar_puertos(self) -> list[str]:
        if not HAS_SERIAL:
            return []
        return [p.device for p in serial.tools.list_ports.comports()]

    def conectar(self, puerto: str, baudrate: int = 115200) -> bool:
        self.desconectar()
        if not HAS_SERIAL:
            self.on_status_change(False, "Falta instalar pyserial")
            return False
        if not puerto:
            self.on_status_change(False, "Selecciona un puerto")
            return False
        try:
            self.ser = serial.Serial(
                port=puerto,
                baudrate=baudrate,
                timeout=0.2,
                dsrdtr=False,
                rtscts=False,
            )
            self.ser.dtr = False
            self.ser.rts = False
            time.sleep(0.2)
            self.ser.reset_input_buffer()

            self.conectado = True
            self._running = True
            threading.Thread(target=self._leer_loop, daemon=True).start()
            self.on_status_change(True, f"Conectado ({puerto})")
            return True
        except Exception as e:
            print(f"[SERIAL ERROR] No se pudo conectar a {puerto}: {e}")
            self.conectado = False
            self.on_status_change(False, f"Error: {e}")
            return False

    def desconectar(self):
        self._running = False
        self.conectado = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None
        self.on_status_change(False, "Desconectado")

    def enviar_recalibrar(self) -> bool:
        if self.conectado and self.ser and self.ser.is_open:
            try:
                self.ser.write(b"RECALIBRAR\n")
                self.ser.flush()
                return True
            except Exception as e:
                print(f"[SERIAL ERROR] Al enviar recalibración: {e}")
                return False
        return False

    def _leer_loop(self):
        while self._running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 256:
                    self.ser.reset_input_buffer()

                linea = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if not linea:
                    continue

                datos = self._parsear_linea(linea)
                if datos:
                    self.on_data_received(*datos)
            except Exception as e:
                print(f"[SERIAL LOOP ERROR] {e}")
                self.desconectar()
                break

    def _parsear_linea(self, linea: str):
        linea = linea.strip()
        # Ignora mensajes de arranque, logs o depuración ("LDR crudo:...")
        if not linea.startswith("DATA:"):
            return None

        try:
            payload = linea[5:]  # Quita el prefijo "DATA:"
            partes = payload.split(",")
            if len(partes) >= 4:
                x1 = float(partes[0])
                x2 = float(partes[1])
                z = float(partes[2])
                alerta = bool(int(partes[3]))
                return (
                    max(0.0, min(1.0, x1)),
                    max(0.0, min(1.0, x2)),
                    z,
                    alerta,
                )
        except ValueError:
            return None
        return None