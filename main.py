import gc
import time
import network
import machine
from machine import I2C, Pin, WDT

import config
from sensors import SensorManager
from neuron import Neuron
from actuators import ActuatorManager
from mqtt_client import MQTTHandler

wdt = None


def alimentar_wdt():
    if wdt:
        wdt.feed()


def conectar_wifi():
    print("\n==========================================")
    print(" PASO 5: CONEXION WI-FI")
    print("==========================================")
    print("[WIFI] SSID:", config.WIFI_SSID)
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)
        time.sleep_ms(200)

    if wlan.isconnected():
        print("[WIFI OK] Ya estaba conectado. IP:", wlan.ifconfig()[0])
        return True

    try:
        wlan.disconnect()
        time.sleep_ms(100)
    except Exception:
        pass

    try:
        wlan.connect(config.WIFI_SSID, config.WIFI_PASS)
        inicio = time.time()
        while not wlan.isconnected() and (time.time() - inicio) < config.WIFI_TIMEOUT_S:
            alimentar_wdt()
            print("[WIFI] Conectando...")
            time.sleep_ms(500)
    except Exception as e:
        print("[WIFI ERROR]", e)

    if wlan.isconnected():
        print("[WIFI OK] Conectado exitosamente! IP:", wlan.ifconfig()[0])
        return True
    else:
        print("[WIFI WARN] No se pudo conectar a Wi-Fi (Timeout)")
        return False


def main():
    global wdt
    print("\n==========================================")
    print(" PASO 1: CARGA ESP32 Y MEMORIA RAM")
    print("==========================================")
    print("[ESP32] Nodo ID:", config.NODE_NAME)
    print("[ESP32] Frecuencia CPU:", machine.freq() // 1000000, "MHz")
    print("[ESP32] RAM libre inicial:", gc.mem_free(), "bytes")

    if config.USE_WATCHDOG:
        try:
            wdt = WDT(timeout=config.WDT_TIMEOUT_MS)
            print("[ESP32] Watchdog (WDT) activado (%d ms)" % config.WDT_TIMEOUT_MS)
        except Exception as e:
            print("[ESP32 ERROR] No se pudo activar el WDT:", e)

    print("\n==========================================")
    print(" PASO 2: ESCANEO I2C Y SENSORES")
    print("==========================================")
    print("[I2C] Inicializando bus en SDA=%d, SCL=%d..." % (config.PIN_SDA, config.PIN_SCL))
    i2c_bus = I2C(0, scl=Pin(config.PIN_SCL), sda=Pin(config.PIN_SDA), freq=config.I2C_FREQ)

    dispositivos_i2c = i2c_bus.scan()
    print("[I2C SCAN] Dispositivos encontrados en el bus:", [hex(d) for d in dispositivos_i2c])

    sensors = SensorManager(i2c_bus)
    sensors.test_sensors()

    print("\n==========================================")
    print(" PASO 3: DIAGNOSTICO DE BUZZERS")
    print("==========================================")
    actuators = ActuatorManager(i2c_bus)
    actuators.test_buzzers()

    print("\n==========================================")
    print(" PASO 4: DIAGNOSTICO DE LEDS Y PANTALLA")
    print("==========================================")
    actuators.test_leds()
    actuators.show_message("Test Hardware", config.NODE_NAME)

    neuron = Neuron()
    print("[NEURONA] Inicializada -> W1=%.1f, W2=%.1f, Bias=%.1f" % (neuron.w1, neuron.w2, neuron.bias))

    def on_mqtt_command(cmd):
        print("[MQTT CMD] Recibido comando:", cmd)
        if "w1" in cmd or "w2" in cmd or "bias" in cmd:
            neuron.set_weights(cmd.get("w1"), cmd.get("w2"), cmd.get("bias"))

    def on_remote_alert(nodo, payload):
        print("[ALERT REMOTA] De %s:" % nodo, payload)
        actuators.notify_peer_alert(nodo)

    mqtt = MQTTHandler(on_command_callback=on_mqtt_command, on_alert_callback=on_remote_alert)

    wifi_ok = conectar_wifi()
    if wifi_ok:
        print("[MQTT] Intentando conectar al broker:", config.MQTT_BROKER)
        if mqtt.connect():
            print("[MQTT OK] Conectado y suscrito a los topics!")
        else:
            print("[MQTT ERROR] Fallo la conexion al broker MQTT")

    print("\n==========================================")
    print(" PASO 6: INICIANDO BUCLE PRINCIPAL")
    print("==========================================")
    actuators.show_message("Calibrando...", "Silencio/Luz base")
    sensors.calibrate()
    actuators.show_message("Sistema Listo", config.NODE_NAME)
    time.sleep_ms(1000)

    estado = {
        "boton_ts": 0,
        "boton_prev": False,
        "ultimo_telemetry": 0,
        "ultimo_status": 0,
        "ultimo_rebroadcast": 0,
        "ultima_alerta": False,
        "ultimo_wifi_retry": 0
    }

    def boton_pulsado(ahora):
        pulsado = sensors.is_button_pressed()
        if pulsado and not estado["boton_prev"]:
            if time.ticks_diff(ahora, estado["boton_ts"]) >= 300:
                estado["boton_ts"] = me = ahora
                estado["boton_prev"] = True
                print("[EVENTO] Boton de autocalibracion presionado!")
                return True
        elif not pulsado:
            estado["boton_prev"] = False
        return False

    while True:
        ahora = time.ticks_ms()
        alimentar_wdt()

        if boton_pulsado(ahora):
            actuators.show_message("Calibrando...", "Espere...")
            sensors.calibrate()

        x1, x2, raw_light, raw_mic = sensors.get_normalized_inputs()
        z, alerta = neuron.predict(x1, x2)
        actuators.set_state(x1, x2, z, alerta)

        if alerta != estado["ultima_alerta"]:
            estado["ultima_alerta"] = alerta
            estado["ultimo_rebroadcast"] = ahora
            print("[CAMBIO ESTADO] Alerta local pasa a:", alerta, "| Z:", round(z, 2))
            mqtt.publish_alert(alerta, z)
        elif alerta and time.ticks_diff(ahora, estado["ultimo_rebroadcast"]) >= config.ALERT_REBROADCAST_MS:
            estado["ultimo_rebroadcast"] = ahora
            mqtt.publish_alert(alerta, z)

        if time.ticks_diff(ahora, estado["ultimo_telemetry"]) >= config.TELEMETRY_INTERVAL_MS:
            estado["ultimo_telemetry"] = ahora
            mqtt.publish_telemetry(x1, x2, z, alerta, raw_light, raw_mic)

        if time.ticks_diff(ahora, estado["ultimo_status"]) >= config.STATUS_INTERVAL_MS:
            estado["ultimo_status"] = ahora
            print("[STATUS] RAM Libre: %d bytes" % gc.mem_free())
            stats = actuators.status()
            stats.update(neuron.get_params())
            mqtt.publish_status(stats)
            gc.collect()

        if not mqtt.connected and time.ticks_diff(ahora, estado["ultimo_wifi_retry"]) >= config.WIFI_RETRY_MS:
            estado["ultimo_wifi_retry"] = ahora
            if conectar_wifi():
                mqtt.connect()

        mqtt.loop(ahora)
        time.sleep_ms(20)


if __name__ == "__main__":
    main()