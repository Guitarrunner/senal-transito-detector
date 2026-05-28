# Sistema de Reconocimiento Automático de Señales de Tránsito

Proyecto académico desarrollado en Python para el reconocimiento automático de señales de tránsito mediante visión por computadora.

El sistema permite cargar imágenes, procesarlas, ejecutar detección mediante un modelo YOLO, visualizar resultados con bounding boxes, almacenar detecciones en archivos estructurados y exportar datos en formato compatible con datasets tipo YOLO.

## Objetivo

Automatizar el procesamiento de imágenes y video de carretera para detectar señales de tránsito y generar información estructurada asociada a cada detección, incluyendo evidencia visual, etiquetas y metadatos.

## Funcionalidades implementadas

* Carga de imágenes en formatos JPG, JPEG y PNG.
* Procesamiento base de imágenes mediante OpenCV.
* Integración de modelo YOLO mediante Ultralytics.
* Visualización de detecciones mediante bounding boxes y etiquetas.
* Interfaz gráfica local desarrollada con Tkinter.
* Login básico con usuarios de prueba.
* Almacenamiento local de imágenes, detecciones y etiquetas.
* Generación de archivos JSON para datos estructurados.
* Exportación de dataset en estructura compatible con YOLO.
* Generación de archivo `dataset.yaml`.
* Consulta básica de imágenes, detecciones y distribución por tipo de señal.

## Tecnologías

* Python 3
* OpenCV
* Ultralytics / YOLO
* NumPy
* Pillow
* Tkinter
* JSON
* Almacenamiento local

## Estructura del proyecto

```text
src/
├── dataset/
│   ├── __init__.py
│   └── exportador_dataset.py
├── detection/
│   ├── __init__.py
│   └── detector_senales.py
├── domain/
│   ├── __init__.py
│   ├── deteccion.py
│   ├── etiqueta.py
│   ├── imagen.py
│   └── senal.py
├── processing/
│   ├── __init__.py
│   └── procesador_imagen.py
├── security/
│   ├── __init__.py
│   └── control_acceso.py
├── storage/
│   ├── __init__.py
│   └── gestor_almacenamiento.py
├── ui/
│   ├── __init__.py
│   ├── interfaz_visualizacion.py
│   └── login.py
├── visualization/
│   ├── __init__.py
│   └── visualizador_resultados.py
├── export_main.py
├── main.py
└── ui_main.py

data/
├── input/
├── processed/
├── evidence/
├── metadata/
│   ├── imagenes.json
│   ├── detecciones.json
│   └── etiquetas.json
└── logs/

exports/
└── yolo_dataset/
    ├── images/
    │   └── train/
    ├── labels/
    │   └── train/
    └── dataset.yaml

docs/
├── investigacion_modelo.md
└── diseno_base_datos.md
```

## Instalación

Crear y activar el entorno virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

El archivo `requirements.txt` debe incluir:

```txt
opencv-python
numpy
ultralytics
pillow
```

## Ejecución de la interfaz gráfica

Para iniciar el sistema con login e interfaz gráfica:

```bash
python -m src.ui_main
```

Credenciales de prueba:

```text
Usuario: admin
Contraseña: admin123
```

```text
Usuario: operador
Contraseña: operador123
```

## Ejecución del exportador de dataset

Para exportar los datos almacenados a una estructura compatible con YOLO:

```bash
python -m src.export_main
```

La exportación genera una estructura en:

```text
exports/yolo_dataset/
```

## Flujo general del sistema

```text
Login
→ Carga de imagen
→ Procesamiento
→ Detección YOLO
→ Visualización con bounding boxes
→ Almacenamiento local
→ Exportación de dataset
```

## Archivos generados

Durante la ejecución, el sistema puede generar:

```text
data/processed/
```

Imágenes procesadas.

```text
data/evidence/
```

Imágenes con bounding boxes como evidencia visual.

```text
data/metadata/
```

Archivos JSON con imágenes, detecciones y etiquetas.

```text
exports/yolo_dataset/
```

Dataset exportado en formato compatible con YOLO.

## Consideraciones

El modelo utilizado actualmente corresponde a un modelo YOLO preentrenado, empleado para validar el pipeline funcional del sistema. El reconocimiento especializado de señales de tránsito de Costa Rica requiere la construcción o adaptación de un dataset propio y el entrenamiento o ajuste de un modelo especializado.

## Próximos pasos

* Revisar el prototipo completo.
* Ejecutar pruebas funcionales del sistema.
* Preparar documentación técnica y guía de usuario.
* Construir dataset inicial de señales de tránsito.
* Entrenar o ajustar un modelo YOLO especializado.
