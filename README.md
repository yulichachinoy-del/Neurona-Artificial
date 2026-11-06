# Sistema de Clasificación Ambiental con Neurona Artificial  en ESP32

## 📌 Descripción del Proyecto
Este proyecto implementa un sistema de Inteligencia Artificial en el Borde (*Edge AI*) ejecutado en un microcontrolador **ESP32** programado en **MicroPython**. El sistema evalúa en tiempo real las condiciones del entorno a través del nivel de **iluminación** y **ruido**, utilizando un algoritmo de Perceptrón Simple para determinar si el ambiente se encuentra en **Estado Normal (Clase 0)** o **Estado de Alerta (Clase 1)**.

El ESP32 realiza la inferencia matemática de forma local e independiente para activar actuadores físicos (LEDs y alarma sonora). De manera simultánea, transmite datos por Wi-Fi utilizando la arquitectura **MQTT** en formato JSON hacia una interfaz gráfica desarrollada en Python, permitiendo visualizar la frontera de decisión 2D, monitorear sensores y ajustar la sensibilidad de la neurona de forma remota.


## 🛠️ Componentes Utilizados y Conexiones

* **Microcontrolador:** ESP32 (NodeMCU / ESP-WROOM-32).
* **Sensor de Luz Digital:** Módulo GY-2561 con sensor TSL2561 (Bus I2C).
  * `VCC` $\rightarrow$ 3.3V
  * `GND` $\rightarrow$ GND
  * `SDA` $\rightarrow$ GPIO 21
  * `SCL` $\rightarrow$ GPIO 22
* **Sensor de Sonido:** Módulo amplificado con micrófono electret MAX4466.
  * `VCC` $\rightarrow$ 3.3V
  * `GND` $\rightarrow$ GND
  * `OUT` $\rightarrow$ GPIO 34 (Entrada Analógica ADC1)
* **Actuadores e Indicadores:**
  * LED Verde (Estado Normal) $\rightarrow$ GPIO 18 (Resistencia de 220 Ω)
  * LED Rojo (Estado de Alerta) $\rightarrow$ GPIO 19 (Resistencia de 220 Ω)
  * Buzzer (Alarma sonora) $\rightarrow$ GPIO 23
* **Control Local:**
  * Botón Pulsador (Reinicio / Calibración) $\rightarrow$ GPIO 4 (Pull-Up interno)
