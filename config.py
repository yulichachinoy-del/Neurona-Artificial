# ---------- PANTALLA LCD (I2C) ----------
PIN_SDA = 21
PIN_SCL = 22

# ---------- SENSORES ----------
PIN_MICROFONO = 35
PIN_LDR = 34
PIN_BOTON = 4

LUZ_MUESTRAS = 32        # Lecturas que se promedian cada vez (mas = mas estable)
LUZ_SUAVIZADO = 0.15     # 0.05 = muy estable pero lento | 0.5 = rapido pero tembloroso
LUZ_MARGEN = 150         # Cuanto debe subir la luz sobre el ambiente para llegar al 100% (al inicio)
DEPURAR = True           # True = imprime las lecturas del LDR cada segundo
MIC_MAXIMO = 350         # Ruido sobre el fondo que cuenta como 100%
VENTANA_MIC_MS = 40      # Tiempo que se escucha el microfono en cada medida
MUESTRAS_CALIBRACION = 50

# ---------- SALIDAS ----------
PIN_LED_VERDE = 18       # Brilla con el SONIDO
PIN_LED_ROJO = 19        # Brilla con la LUZ (fijo si hay alerta)
PIN_BUZZER_AGUDO = 23
PIN_BUZZER_GRAVE = 25

ALARMA_MS = 200          # Cada cuanto cambia el tono de la alarma
LCD_MS = 300             # Cada cuanto se actualiza la pantalla

# ---------- NEURONA ----------
PESO_LUZ = 5.0
PESO_SONIDO = 5.0
SESGO = -6.0
MUESTRAS_ON = 2          # Lecturas seguidas para activar la alerta
MUESTRAS_OFF = 5         # Lecturas seguidas para desactivarla