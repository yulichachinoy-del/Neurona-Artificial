import json
import time
import ubinascii
import machine
from umqtt.simple import MQTTClient
import config

class MQTTHandler:
    def __init__(self, on_command_callback=None, on_alert_callback=None, feed=None):
        chip_id = ubinascii.hexlify(machine.unique_id()).decode('utf-8')
        self.client_id = config.NODE_NAME + "_" + chip_id
        self.client = None
        self.connected = False
        self.last_reconnect = 0
        self.on_command = on_command_callback
        self.on_alert = on_alert_callback
        self.feed = feed

    def _alimentar(self):
        """Avisa al watchdog antes de una llamada de red que puede bloquear.

        connect() espera el CONNACK del broker y puede tardar varios segundos
        (medidos ~7 s con broker.hivemq.com); si el WDT vence ahi, MicroPython
        hace panic y la placa se reinicia en bucle.
        """
        if not self.feed:
            return
        try:
            self.feed()
        except Exception:
            pass

    def connect(self):
        user = config.MQTT_USER.strip() if config.MQTT_USER else None
        password = str(config.MQTT_PASS) if config.MQTT_PASS is not None else ""

        if not user:
            user = None
            password = None

        try:
            if user:
                self.client = MQTTClient(
                    client_id=self.client_id,
                    server=config.MQTT_BROKER,
                    port=config.MQTT_PORT,
                    user=user,
                    password=password,
                    keepalive=config.MQTT_KEEPALIVE_S
                )
            else:
                self.client = MQTTClient(
                    client_id=self.client_id,
                    server=config.MQTT_BROKER,
                    port=config.MQTT_PORT,
                    keepalive=config.MQTT_KEEPALIVE_S
                )

            self.client.set_callback(self._sub_cb)
            self._alimentar()
            self.client.connect()
            self.client.subscribe(config.TOPIC_NODE_COMMANDS)
            self.client.subscribe(config.TOPIC_BROADCAST_COMMANDS)
            self.client.subscribe(config.TOPIC_ALERTS)
            self._alimentar()
            self.connected = True
            return True
        except Exception as e:
            if config.DEBUG:
                print("[mqtt] error de conexion:", e)
            self.connected = False
            return False

    def check_msg(self):
        if not self.connected:
            return
        try:
            self.client.check_msg()
        except Exception as e:
            if config.DEBUG:
                print("[mqtt] error check_msg:", e)
            self.connected = False

    def loop(self, now):
        if not self.connected:
            if time.ticks_diff(now, self.last_reconnect) >= config.MQTT_RECONNECT_MS:
                self.last_reconnect = now
                self.connect()
        else:
            self.check_msg()

    def _sub_cb(self, topic, msg):
        try:
            top_str = topic.decode('utf-8')
            payload = json.loads(msg.decode('utf-8'))
            if top_str in (config.TOPIC_NODE_COMMANDS, config.TOPIC_BROADCAST_COMMANDS):
                if self.on_command:
                    self.on_command(payload)
            elif top_str == config.TOPIC_ALERTS:
                nodo_origen = payload.get("nodo")
                if nodo_origen and nodo_origen != config.NODE_NAME and payload.get("alerta"):
                    if self.on_alert:
                        self.on_alert(nodo_origen, payload)
        except Exception as e:
            if config.DEBUG:
                print("[mqtt] error procesando mensaje:", e)

    def publish_telemetry(self, x1, x2, z, alerta, raw_light, raw_mic):
        if not self.connected:
            return
        data = {
            "nodo": config.NODE_NAME,
            "x1": round(x1, 3),
            "x2": round(x2, 3),
            "z": round(z, 2),
            "alerta": bool(alerta),
            "lux": round(raw_light, 1),
            "mic": int(raw_mic)
        }
        try:
            self.client.publish(config.TOPIC_TELEMETRY, json.dumps(data))
        except Exception:
            self.connected = False

    def publish_alert(self, alerta, z):
        if not self.connected:
            return
        data = {
            "nodo": config.NODE_NAME,
            "alerta": bool(alerta),
            "z": round(z, 2),
            "timestamp": time.ticks_ms()
        }
        try:
            self.client.publish(config.TOPIC_ALERTS, json.dumps(data))
        except Exception:
            self.connected = False

    def publish_status(self, stats):
        if not self.connected:
            return
        stats["nodo"] = config.NODE_NAME
        try:
            self.client.publish(config.TOPIC_STATUS, json.dumps(stats))
        except Exception:
            self.connected = False