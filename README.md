# Sistema de Reconocimiento Automático de Señales de Tránsito

Proyecto académico desarrollado en Python para el reconocimiento automático de señales de tránsito mediante visión por computadora.

## Objetivo

Automatizar el procesamiento de imágenes y video de carretera para detectar señales de tránsito y generar información estructurada asociada a cada detección.

## Alcance inicial

Durante las primeras semanas de desarrollo se trabajará en:

- Investigación y selección del modelo de detección.
- Implementación base del módulo de procesamiento de imágenes.
- Diseño de la estructura de almacenamiento de datos.

## Tecnologías

- Python
- OpenCV
- YOLO / Ultralytics
- JSON para registros estructurados
- Almacenamiento local

## Estructura del proyecto

```text
src/
├── domain/
├── processing/
├── detection/
├── storage/
└── dataset/

data/
├── input/
├── processed/
├── evidence/
├── metadata/
└── logs/

docs/
├── investigacion_modelo.md
├── diseno_base_datos.md
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.main
```