NODE_NAME = "nodo1"

PIN_SDA = 21
PIN_SCL = 22
I2C_FREQ = 100000

I2C_ADDR_LCD = 0x27
I2C_ADDR_TSL2561 = 0x39

PIN_KY038_AO = 35
PIN_BTN_CAL = 4

LIGHT_SENSOR = "ldr"          # "ldr" = fotoresistencia (ADC) | "tsl2561" = sensor I2C
PIN_LDR_AO = 34
LDR_INVERT = True             # True = corrige que al tapar el LDR suba el ADC (ahora: mas luz = mas LED)
LDR_ABSOLUTE_MODE = True      # True = x1 mide la luz real (0..100%) sin que la calibracion la ponga en 0
LDR_SAMPLES = 8               # lecturas promediadas por muestra

LUX_REF = 500.0
MIC_REF = 350                 # Bajado de 1200 a 350 para que el KY-038 sea sensible a voz y aplausos
LDR_REF = 3200                # Cuentas ADC para 100% de luz (sobre 4095)
ADC_MAX = 4095

SAMPLING_WINDOW_MS = 40       # Ventana de 40ms para capturar mejor las ondas graves/medias del microfono
CALIBRATION_MS = 2000
CALIBRATION_SAMPLES = 100
CALIB_FLOOR_PERCENTILE = 15

PIN_LED_GREEN = 18
PIN_LED_RED = 19
PIN_BUZZER_1 = 23
PIN_BUZZER_2 = 25
PWM_FREQ_LED = 1000
PWM_MAX_DUTY = 1023

LCD_INTERVAL_MS = 300
LCD_RETRY_MS = 5000
LCD_LOG_WRITES = True         # Imprime en consola lo que se envia a la pantalla
ALARM_DELAY_MS = 3000
ALARM_PATTERN_MS = 250
PEER_ALERT_SHOW_MS = 6000

DEFAULT_W1 = 5.0
DEFAULT_W2 = 5.0
DEFAULT_BIAS = -4.0
W_LIMIT = 20.0

ALERT_ON_SAMPLES = 2
ALERT_OFF_SAMPLES = 5
ALERT_REBROADCAST_MS = 5000

WIFI_SSID = "Coeur"
WIFI_PASS = "12052026"
WIFI_TIMEOUT_S = 15
WIFI_RETRY_MS = 15000

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_USER = ""
MQTT_PASS = ""
MQTT_KEEPALIVE_S = 30
MQTT_RECONNECT_MS = 5000

TOPIC_BASE = "neurona"
TOPIC_NODE = TOPIC_BASE + "/" + NODE_NAME

TOPIC_TELEMETRY = TOPIC_NODE + "/telemetria"
TOPIC_STATUS = TOPIC_NODE + "/estado"
TOPIC_NODE_COMMANDS = TOPIC_NODE + "/comandos"

TOPIC_BROADCAST_COMMANDS = TOPIC_BASE + "/comandos"
TOPIC_ALERTS = TOPIC_BASE + "/alertas"

TELEMETRY_INTERVAL_MS = 500
STATUS_INTERVAL_MS = 30000
DIAG_INTERVAL_MS = 30000

DEBUG = True
USE_WATCHDOG = True
WDT_TIMEOUT_MS = 20000
