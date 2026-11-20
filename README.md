# Neurona Artificial — ESP32

Firmware en MicroPython que lee un sensor de luz y un micrófono, evalúa sus señales con una neurona artificial y controla indicadores, una alarma y una pantalla LCD. La versión actual funciona localmente: no requiere conexión Wi-Fi ni comunicación MQTT.

El proyecto incluye además un dashboard para el computador, hecho con Flet, que simula los sensores y muestra en pantalla la neurona, la LCD y los actuadores sin necesidad de tener el ESP32 conectado.

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

### Firmware (se copian al ESP32)

- `main.py`: inicializa el bus I2C y los componentes, calibra y ejecuta el ciclo principal.
- `config.py`: pines y parámetros ajustables.
- `sensors.py`: lecturas ADC, filtrado y calibración ambiental.
- `neuron.py`: combinación ponderada de las entradas y decisión de alerta con histéresis.
- `actuators.py`: LEDs, buzzers y actualización periódica de la LCD.
- `Lcd.py`: controlador de pantalla LCD por I2C.

### Dashboard (solo se ejecuta en el computador)

- `app.py`: punto de entrada; ensambla los módulos de la interfaz.
- `tema.py`: paleta de colores.
- `barra_lateral.py`: modelo matemático, hiperparámetros, mapeo de pines y botón de recalibración.
- `tarjetas_kpi.py`: tarjetas de luz, sonido, activación Z y estado del sistema.
- `panel_hardware.py`: emulador de la LCD 1602, LEDs y sirena.
- `simulador.py`: sliders de luz y sonido, escenarios rápidos y generador dinámico.
- `grafica.py`: tendencia temporal de luz, sonido y activación.

El dashboard reutiliza `neuron.py` y `config.py` del firmware, así que la simulación usa la misma neurona y los mismos parámetros que el ESP32.

## Funcionamiento

1. Al iniciar, el programa busca dispositivos I2C en los pines configurados y prepara la LCD si está conectada.
2. Calibra el ruido de fondo y toma la luz ambiente como referencia inicial. Mantén el entorno en las condiciones deseadas durante esta calibración.
3. En cada ciclo normaliza la luz (`x1`) y el sonido (`x2`) y calcula `z = x1 × PESO_LUZ + x2 × PESO_SONIDO + SESGO`. La alerta se activa cuando `z >= 0` durante el número de muestras configurado; también se aplica histéresis al desactivarla.
4. El LED verde representa el nivel de sonido; el rojo representa la luz y queda encendido durante una alerta. La alarma alterna los dos tonos y la LCD muestra niveles y estado.
5. Pulsa el botón para apagar los actuadores, recalibrar y reiniciar el estado de la neurona.

La lectura del LDR se promedia y suaviza. Su rango se adapta durante la ejecución a los mínimos y máximos observados. El micrófono se mide por el rango pico a pico en una ventana de muestreo.

## Instalación y ejecución del firmware (ESP32)

1. Graba MicroPython en el ESP32.
2. Copia al dispositivo únicamente los archivos del firmware (`main.py`, `config.py`, `sensors.py`, `neuron.py`, `actuators.py` y `Lcd.py`) usando Thonny, `mpremote` u otra herramienta compatible. No copies los archivos del dashboard: dependen de Flet, que no existe en MicroPython.
3. Configura los pines en `config.py` y conecta los componentes.
4. Ejecuta `main.py` (o configúralo como archivo de inicio, según tu flujo de trabajo).

El sistema también puede operar sin LCD: el programa informa por consola si no detecta un dispositivo I2C. La salida de depuración de luz se controla con `DEPURAR` en `config.py`.

`main.py` solo funciona dentro del ESP32, porque usa el módulo `machine` de MicroPython. Si lo ejecutas en el computador dará el error `No module named 'machine'`.

## Dashboard de monitoreo y simulación (computador)

### Requisitos

- Python 3.10 o superior (se probó con Python 3.13).
- Las librerías `flet` y `flet-charts`.
- Opcional: `pyserial`. Solo cambia la etiqueta de la barra lateral entre "Serial: Disponible" y "Modo: Simulación Activa".

### Instalación

Se recomienda usar un entorno virtual. En Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install flet flet-charts
```

En Linux o macOS, el segundo comando es `source .venv/bin/activate`.

### Ejecución

Desde la carpeta del proyecto:

```bash
python app.py
```

### Qué se puede hacer

- Mover los sliders de luz (`x1`) y sonido (`x2`) y ver cómo responden las tarjetas, la LCD emulada, los LEDs y la gráfica.
- Usar los escenarios rápidos (Oscuridad, Ambiente Normal, Disparar Alerta).
- Activar el generador dinámico, que varía las entradas automáticamente.
- Pulsar "Pulsador Recalibrar", que equivale al botón del GPIO 4: reinicia el estado y la histéresis de la neurona.

Los pesos, el sesgo y las muestras de histéresis que muestra la barra lateral se leen de `config.py`. Si los cambias, reinicia el dashboard para ver los valores nuevos.