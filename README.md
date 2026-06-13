# Sistema de Reconocimiento Automático de Señales de Tránsito

Proyecto académico desarrollado en Python para el reconocimiento automático de señales de tránsito mediante visión por computadora. El sistema permite cargar imágenes, procesarlas, ejecutar detección mediante YOLO, visualizar resultados con *bounding boxes*, almacenar detecciones en archivos estructurados y exportar datos en una estructura compatible con datasets tipo YOLO.

El proyecto está construido como un **prototipo funcional modular**. El modelo de detección puede sustituirse por otro archivo `.pt` entrenado posteriormente, sin modificar la arquitectura principal del sistema.

## Estado del proyecto

El prototipo incluye los módulos principales del sistema:

- Procesamiento de imágenes.
- Detección de señales con YOLO.
- Visualización de resultados con *bounding boxes*.
- Almacenamiento local de imágenes, detecciones y etiquetas.
- Exportación de datos en formato compatible con YOLO.
- Interfaz gráfica local con Tkinter.
- Control de acceso básico.
- Estructura de dataset y entrenamiento inicial de modelo especializado.

El entrenamiento del modelo especializado se trabaja como una etapa modular. El desempeño del modelo depende de la cantidad, calidad y balance del dataset utilizado.

## Objetivo

Automatizar el procesamiento de imágenes de carretera para detectar señales de tránsito y generar información estructurada asociada a cada detección, incluyendo evidencia visual, etiquetas y metadatos.

## Funcionalidades implementadas

- Carga de imágenes en formatos JPG, JPEG y PNG.
- Procesamiento base de imágenes mediante OpenCV.
- Integración de modelo YOLO mediante Ultralytics.
- Visualización de detecciones mediante *bounding boxes* y etiquetas.
- Interfaz gráfica local desarrollada con Tkinter.
- Login básico con usuarios de prueba.
- Almacenamiento local de imágenes, detecciones y etiquetas.
- Generación de archivos JSON para datos estructurados.
- Exportación de dataset en estructura compatible con YOLO.
- Generación de archivo `dataset.yaml`.
- Consulta básica de imágenes, detecciones y distribución por tipo de señal.
- Preparación de dataset propio con clases de señales de tránsito.

## Tecnologías utilizadas

- Python 3
- OpenCV
- Ultralytics YOLO
- NumPy
- Pillow
- Tkinter
- JSON
- PyYAML
- Almacenamiento local

## Estructura del proyecto

```text
senal-transito-detector/
├── src/
│   ├── dataset/
│   │   └── exportador_dataset.py
│   ├── detection/
│   │   └── detector_senales.py
│   ├── domain/
│   │   ├── deteccion.py
│   │   ├── etiqueta.py
│   │   ├── imagen.py
│   │   └── senal.py
│   ├── processing/
│   │   └── procesador_imagen.py
│   ├── security/
│   │   └── control_acceso.py
│   ├── storage/
│   │   └── gestor_almacenamiento.py
│   ├── ui/
│   │   ├── interfaz_visualizacion.py
│   │   └── login.py
│   ├── visualization/
│   │   └── visualizador_resultados.py
│   ├── demo_inicial.py
│   ├── export_main.py
│   └── main.py
├── data/
│   ├── processed/
│   ├── evidence/
│   └── metadata/
├── dataset/
│   ├── images/
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   ├── labels/
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   └── dataset.yaml
├── docs/
│   ├── clases_dataset.md
│   ├── control_dataset.md
│   ├── entrenamiento_modelo.md
│   ├── guia_usuario.md
│   └── investigacion_modelo.md
├── exports/
│   └── yolo_dataset/
├── models/
│   └── best.pt
├── predefined_classes.txt
├── requirements.txt
└── README.md
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

Dependencias principales:

```text
opencv-python
numpy
ultralytics
pillow
pyyaml
```

## Ejecución de la interfaz gráfica

Desde la raíz del proyecto:

```bash
python -m src.main
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

## Uso básico del sistema

1. Ejecutar la interfaz gráfica.
2. Iniciar sesión con un usuario de prueba.
3. Seleccionar una imagen desde la opción de procesamiento.
4. El sistema procesa la imagen, ejecuta detección y genera evidencia visual.
5. Las detecciones se muestran en pantalla y se almacenan localmente.

## Modelo de detección

El detector utiliza un modelo YOLO. Para validar el flujo del sistema puede utilizarse un modelo preentrenado como `yolov8n.pt`. Para usar un modelo propio entrenado, se recomienda colocarlo en:

```text
models/best.pt
```

Luego se puede configurar el detector para utilizar ese archivo. El modelo es reemplazable, por lo que futuras versiones pueden incorporar un `.pt` entrenado con más imágenes y clases sin modificar toda la arquitectura del sistema.

## Dataset

El dataset se organiza en formato YOLO:

```text
dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
├── labels/
│   ├── train/
│   ├── val/
│   └── test/
└── dataset.yaml
```

Cada imagen debe tener un archivo `.txt` con el mismo nombre en la carpeta correspondiente de `labels`.

Ejemplo:

```text
dataset/images/train/foto_001.jpg
dataset/labels/train/foto_001.txt
```

Los archivos `.txt` deben contener etiquetas en formato YOLO:

```text
<class_id> <x_center> <y_center> <width> <height>
```

## Clases del dataset

Las clases actuales se definen en `dataset/dataset.yaml` y deben coincidir con el orden de `predefined_classes.txt`.

```text
0  velocidad_maxima
1  parada_buses
2  parada_taxis
3  estacionamiento
4  no_hay_paso
5  no_estacionar
6  silencio
7  ceda
8  alto
9  no_virar_izquierda
10 no_virar_derecha
11 curva_derecha
12 curva_izquierda
13 transeunte
14 zona_escolar
15 precaucion
16 semaforo
17 pendiente
18 reductor_velocidad
19 dos_carriles_a_uno
20 interseccion
21 tren
22 reductores_de_velocidad
23 informacion
24 turismo
25 obras
26 lugares
27 rotonda
28 giro_amplio
29 no_vehiculos_pesados
30 carril_reversible
31 carril_exclusivo
32 delineador_curva
33 obstaculo
34 altura_maxima
```

## Etiquetado con LabelImg

Para abrir LabelImg con las clases del proyecto:

```bash
labelImg dataset/images/train predefined_classes.txt
```

En LabelImg se debe usar el formato **YOLO**. En la interfaz se selecciona el nombre de la clase, por ejemplo `alto` o `ceda`; el archivo `.txt` se guarda con el identificador numérico correspondiente.

No se deben etiquetar carros, peatones reales, postes, edificios u otros elementos si no forman parte de las clases del dataset. Estos objetos pueden aparecer en la imagen como contexto, pero no deben anotarse como clases.

## Entrenamiento del modelo

Entrenamiento de prueba:

```bash
yolo detect train model=yolov8n.pt data=dataset/dataset.yaml epochs=3 imgsz=640 batch=2 name=test_dataset
```

Entrenamiento completo inicial:

```bash
yolo detect train model=yolov8n.pt data=dataset/dataset.yaml epochs=50 imgsz=640 batch=4 name=senales_cr_v3
```

Si el entrenamiento es muy lento o la computadora no responde bien:

```bash
yolo detect train model=yolov8n.pt data=dataset/dataset.yaml epochs=30 imgsz=640 batch=2 name=senales_cr_v3
```

El mejor modelo queda en una ruta como:

```text
runs/detect/senales_cr_v3/weights/best.pt
```

## Predicción con modelo entrenado

```bash
yolo detect predict model=runs/detect/senales_cr_v3/weights/best.pt source=dataset/images/val conf=0.10
```

## Exportación de dataset desde el sistema

El sistema permite exportar imágenes procesadas y detecciones aprobadas por el usuario a una estructura compatible con YOLO.

La exportación se realiza desde la interfaz gráfica mediante el siguiente flujo:

1. Procesar una imagen desde la aplicación.
2. Revisar visualmente las detecciones y los bounding boxes generados.
3. Si las detecciones son correctas, presionar el botón **Agregar a exportación**.
4. Repetir el proceso con las imágenes que se deseen incluir.
5. Presionar el botón **Exportar dataset YOLO**.

La exportación genera una nueva carpeta dentro de:

```text
exports/
```

Cada carpeta exportada utiliza un nombre con fecha y hora, por ejemplo:

```text
exports/yolo_dataset_20260613_143210/
```

Dentro de esa carpeta se genera una estructura compatible con YOLO:

```text
images/train/
labels/train/
dataset.yaml
```

Las imágenes aprobadas se exportan en el conjunto `train`. La separación automática en `val` y `test` no se realiza desde la interfaz, ya que para un entrenamiento formal se recomienda revisar las etiquetas y dividir manualmente el dataset en entrenamiento, validación y prueba.

Este exportador no sustituye el dataset etiquetado manualmente con herramientas como LabelImg. Su función es convertir detecciones almacenadas y aprobadas desde el sistema en datos reutilizables para construir, revisar o ampliar datasets en futuras etapas.

## Archivos generados

Durante la ejecución, el sistema puede generar:

```text
data/processed/      imágenes procesadas
data/evidence/       imágenes con bounding boxes
data/metadata/       archivos JSON con imágenes, detecciones y etiquetas
exports/yolo_dataset/ dataset exportado en formato YOLO
runs/                resultados de entrenamiento y predicción
```

Estos archivos no deberían versionarse en GitHub, salvo ejemplos puntuales necesarios para evidencias.

## Consideraciones sobre video

El proyecto contempla imágenes y video a nivel de alcance general. Sin embargo, la versión actual se validó principalmente con imágenes estáticas, ya que permiten comprobar de forma más controlada el flujo completo de procesamiento, detección, visualización, almacenamiento y exportación.

El procesamiento de video queda como una línea de mejora futura o validación adicional, especialmente para escenarios de tiempo real o semitiempo real.

## Limitaciones actuales

- El desempeño del modelo depende directamente de la calidad y balance del dataset.
- Algunas clases tienen pocas imágenes, por lo que su detección puede ser limitada.
- Las señales deterioradas, vandalizadas, cortadas o parcialmente obstruidas requieren más ejemplos para mejorar la generalización.
- La validación del componente de video no está completamente consolidada.
- El sistema es un prototipo funcional, no una solución lista para toma de decisiones críticas en seguridad vial.

## Mejoras futuras

- Ampliar y balancear el dataset por clase.
- Agregar más imágenes en condiciones reales de carretera.
- Reentrenar el modelo con clases más equilibradas.
- Mejorar la validación del procesamiento de video.
- Agregar métricas de evaluación más completas.
- Integrar hardware de captura y procesamiento local.
- Permitir configuración del modelo desde archivo externo o interfaz.

## Repositorio

```text
https://github.com/Guitarrunner/senal-transito-detector
```
