#  Neurona Artificial (ESP32)

Este proyecto implementa una red neuronal artificial de una sola capa (Perceptrón) en un microcontrolador ESP32 ejecutando MicroPython. El sistema evalúa continuamente variables de entorno (intensidad lumínica y nivel de sonido) para determinar estados de alerta ambiental en tiempo real y coordinarse con otros nodos a través de la red.

---

## 🛠️ Componentes Utilizados

### Hardware
* **Microcontrolador:** ESP32 (Wi-Fi + Bluetooth).
* **Sensores:**
  * Sensor de Sonido / Micrófono analógico (`KY-038`).
  * Sensor de Luz: Fotoresistencia (`LDR` vía ADC) o Sensor digital I2C (`TSL2561`).
* **Actuadores e Indicadores:**
  * Pantalla LCD 1602 con módulo adaptador I2C (`PCF8574`).
  * LED Verde (Indicación de estado normal mediante PWM).
  * LED Rojo (Indicación de estado de alerta mediante PWM).
  * 2 Buzzers piezoeléctricos (Generación de patrones tonales de alarma por PWM).
* **Entradas de usuario:**
  * Botón pulsador (Autocalibración de nivel de ruido base).

### Software y Protocolos
* **Lenguaje:** MicroPython.
* **Protocolo I2C:** Comunicación con pantalla LCD y sensor de luz digital.
* **Protocolo MQTT:** Publicación de telemetría, estados de alerta y recepción de comandos remotos.
* **Watchdog Timer (WDT):** Reinicio automático ante congelamiento del sistema.

---

## 🚀 Funcionalidades Implementadas

1. **Lectura y Normalización de Sensores:**
   * Muestreo de picos de señal analógica para el micrófono.
   * Filtro de ruido por promediado en lecturas de fototransistor/LDR.
   * Normalización de variables de entrada a un rango relativo $[0.0, 1.0]$.

2. **Autocalibración Ambiental:**
   * Calibración inicial y a demanda mediante pulsador para establecer los niveles base de luz y sonido del entorno (Floor Calibration).

3. **Inferencia por Neurona Artificial:**
   * Combinación lineal $z = (x_1 \cdot w_1) + (x_2 \cdot w_2) + \text{bias}$.
   * Función de activación por umbral ($z \ge 0$).
   * Filtro de histéresis por conteo de muestras consecutivas para evitar falsos positivos por picos aislados.

4. **Gestión de Alarma y Actuadores:**
   * Variación progresiva del brillo de los LEDs según el nivel de señal.
   * Patrón de sirena alternada entre dos buzzers con retardo de seguridad.
   * Visualización dinámica en pantalla LCD de estados, parámetros $Z$ y alertas recibidas.

5. **Conectividad e IoT (MQTT):**
   * Envío continuo de telemetría (`/telemetria`) y estado general (`/estado`).
   * Transmisión de alertas en tiempo real al topic global (`/alertas`).
   * Recepción de alertas remotas para notificar eventos detectados por otros nodos.
   * **Reconfiguración remota:** Modificación dinámica de pesos ($w_1$, $w_2$) y sesgo ($\text{bias}$) mediante mensajes MQTT sin reiniciar el hardware.
