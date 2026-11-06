# Neurona Artificial — ESP32

Firmware en MicroPython que lee un sensor de luz y un micrófono, evalúa sus señales con una neurona artificial y controla indicadores, una alarma y una pantalla LCD. La versión actual funciona localmente: no requiere conexión Wi-Fi ni comunicación MQTT.

## Hardware

- ESP32 compatible con MicroPython.
- Fotoresistencia (LDR) y micrófono analógico.
- Pantalla LCD 1602 con adaptador I2C PCF8574 (opcional).
- Pulsador para recalibrar.
- LEDs verde y rojo y dos buzzers piezoeléctricos.

### Pines predeterminados

| Elemento | GPIO |
| --- | ---: |
| LCD SDA / SCL (I2C) | 21 / 22 |
| Micrófono analógico | 35 |
| LDR analógica | 34 |
| Pulsador (entrada con pull-up) | 4 |
| LED verde / LED rojo | 18 / 19 |
| Buzzer agudo / buzzer grave | 23 / 25 |

Los pines y parámetros de filtrado, calibración, alarma y neurona se pueden cambiar en `config.py`. Verifica la compatibilidad eléctrica de los módulos con el ESP32 antes de conectarlos.

## Archivos

- `main.py`: inicializa el bus I2C y los componentes, calibra y ejecuta el ciclo principal.
- `config.py`: pines y parámetros ajustables.
- `sensors.py`: lecturas ADC, filtrado y calibración ambiental.
- `neuron.py`: combinación ponderada de las entradas y decisión de alerta con histéresis.
- `actuators.py`: LEDs, buzzers y actualización periódica de la LCD.
- `Lcd.py`: controlador de pantalla LCD por I2C.

## Funcionamiento

1. Al iniciar, el programa busca dispositivos I2C en los pines configurados y prepara la LCD si está conectada.
2. Calibra el ruido de fondo y toma la luz ambiente como referencia inicial. Mantén el entorno en las condiciones deseadas durante esta calibración.
3. En cada ciclo normaliza la luz (`x1`) y el sonido (`x2`) y calcula `z = x1 × PESO_LUZ + x2 × PESO_SONIDO + SESGO`. La alerta se activa cuando `z >= 0` durante el número de muestras configurado; también se aplica histéresis al desactivarla.
4. El LED verde representa el nivel de sonido; el rojo representa la luz y queda encendido durante una alerta. La alarma alterna los dos tonos y la LCD muestra niveles y estado.
5. Pulsa el botón para apagar los actuadores, recalibrar y reiniciar el estado de la neurona.

La lectura del LDR se promedia y suaviza. Su rango se adapta durante la ejecución a los mínimos y máximos observados. El micrófono se mide por el rango pico a pico en una ventana de muestreo.

## Instalación y ejecución

1. Graba MicroPython en el ESP32.
2. Copia los archivos `.py` de este proyecto al dispositivo usando Thonny, `mpremote` u otra herramienta compatible.
3. Configura los pines en `config.py` y conecta los componentes.
4. Ejecuta `main.py` (o configúralo como archivo de inicio, según tu flujo de trabajo).

El sistema también puede operar sin LCD: el programa informa por consola si no detecta un dispositivo I2C. La salida de depuración de luz se controla con `DEPURAR` en `config.py`.
