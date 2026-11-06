# Neurona-Artificial

# Sistema de Clasificación Ambiental con Neurona Artificial (Edge AI) en ESP32

## 📌 Descripción del Proyecto
Este proyecto implementa un sistema de Inteligencia Artificial en el Borde (*Edge AI*) ejecutado en un microcontrolador **ESP32** programado en **MicroPython**. El sistema evalúa en tiempo real las condiciones del entorno a través del nivel de **iluminación** y **ruido**, utilizando un algoritmo de Perceptrón Simple para determinar si el ambiente se encuentra en **Estado Normal (Clase 0)** o **Estado de Alerta (Clase 1)**.

El ESP32 realiza la inferencia matemática de forma local e independiente para activar actuadores físicos (LEDs y alarma sonora). De manera simultánea, transmite datos por Wi-Fi utilizando la arquitectura **MQTT** en formato JSON hacia una interfaz gráfica desarrollada en Python, permitiendo visualizar la frontera de decisión 2D, monitorear sensores y ajustar la sensibilidad de la neurona de forma remota.


## 🛠️ Componentes Utilizados y Conexiones
