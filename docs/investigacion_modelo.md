## Introducción

El presente documento tiene como objetivo analizar y seleccionar un modelo de detección de objetos adecuado para el sistema de reconocimiento automático de señales de tránsito.

La selección del modelo es un componente crítico, ya que impacta directamente la precisión, el tiempo de procesamiento y la viabilidad del sistema en un entorno local.

## Requisitos del sistema

El modelo de detección debe cumplir con las siguientes condiciones:

- Ser compatible con Python
- Integrarse con OpenCV
- Permitir detección de múltiples objetos en imágenes
- Funcionar en entorno local sin depender de servicios externos
- Mantener tiempos de procesamiento razonables (< 1 segundo por detección)
- Ser adaptable a señales de tránsito de Costa Rica

## Modelos evaluados

### YOLO (You Only Look Once)
Modelo de detección en una sola pasada, conocido por su velocidad y buen balance entre precisión y rendimiento.

### SSD (Single Shot Detector)
Modelo eficiente de detección en tiempo real, aunque con menor soporte actual comparado con YOLO.

### Faster R-CNN
Modelo de dos etapas con alta precisión, pero mayor complejidad y costo computacional.

## Comparación de modelos

| Modelo | Precisión | Velocidad | Complejidad | Uso en local |
|--------|----------|----------|------------|-------------|
| YOLO   | Alta     | Alta     | Media      | Sí          |
| SSD    | Media    | Alta     | Media      | Sí          |
| Faster R-CNN | Muy alta | Baja | Alta | Limitado |

## Modelo seleccionado

Se selecciona YOLOv8 como modelo de detección principal para el sistema.

## Justificación

YOLOv8 es seleccionado debido a las siguientes razones:

- Cumple con la restricción de uso de modelos tipo YOLO establecida en el proyecto
- Permite detección rápida en imágenes, alineándose con el requisito de tiempo de respuesta
- Puede ejecutarse en un entorno local sin necesidad de infraestructura adicional
- Cuenta con implementaciones modernas en Python (Ultralytics)
- Facilita la integración con OpenCV
- Permite detectar múltiples objetos en una sola pasada

Adicionalmente, su arquitectura permite sustituir el modelo en el futuro sin afectar el diseño del sistema, lo cual es consistente con el enfoque modular definido.

## Alcance en esta etapa

En esta fase del proyecto, YOLOv8 será utilizado como modelo base para validar el flujo de procesamiento de imágenes y detección.

El entrenamiento o ajuste específico del modelo para señales de tránsito de Costa Rica no forma parte del alcance actual y será considerado en etapas posteriores.

## Conclusión

La selección de YOLOv8 permite establecer una base sólida para el desarrollo del sistema, equilibrando precisión, rendimiento y facilidad de implementación, lo cual es fundamental en un entorno de ejecución local.

Esta decisión permite avanzar hacia la implementación del módulo de detección sin comprometer la arquitectura ni los objetivos del proyecto.

## Referencias

- Ultralytics YOLOv8 Documentation
- Papers mencionados en el plan de proyecto