# Guía de usuario

Esta guía describe el uso básico del sistema de reconocimiento automático de señales de tránsito mediante visión por computadora.

## Requisitos previos

* Python 3 instalado.
* Entorno virtual creado y activado.
* Dependencias instaladas desde `requirements.txt`.
* Modelo YOLO disponible.

El sistema puede ejecutarse con el modelo base de YOLO (`yolov8n.pt`) o con un modelo entrenado propio. Para utilizar un modelo entrenado, se recomienda colocarlo en:

```text
models/best.pt
```

Si el archivo `models/best.pt` no existe, el sistema utiliza el modelo base `yolov8n.pt` como respaldo.

## Instalación

Desde la raíz del proyecto:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

Para ejecutar la interfaz gráfica del sistema:

```bash
python -m src.main
```

Al iniciar, se muestra la ventana de inicio de sesión. La ventana se abre centrada y al frente de la pantalla.

## Inicio de sesión

Usuarios de prueba:

```text
Usuario: admin
Contraseña: admin123
```

```text
Usuario: operador
Contraseña: operador123
```

Para ingresar, se puede presionar el botón **Ingresar** o utilizar la tecla **Enter** después de escribir las credenciales.

## Procesamiento de una imagen

Para procesar una imagen:

1. Iniciar sesión en el sistema.
2. Presionar el botón para seleccionar o procesar una imagen.
3. Seleccionar una imagen en formato JPG, JPEG o PNG.
4. Esperar a que el sistema procese la imagen.
5. Revisar la imagen generada con bounding boxes.
6. Revisar el panel de detecciones.

El sistema realiza el procesamiento de la imagen, ejecuta el modelo YOLO, muestra las detecciones encontradas y guarda la información generada en archivos locales.

## Resultados generados

Durante la ejecución, el sistema puede generar archivos en las siguientes carpetas:

```text
data/processed/   imágenes procesadas
data/evidence/    imágenes con bounding boxes
data/metadata/    archivos JSON con datos estructurados
```

Los archivos JSON almacenan información relacionada con imágenes procesadas, detecciones, etiquetas y datos necesarios para la exportación.

## Exportación de dataset

El sistema permite exportar imágenes y etiquetas en una estructura compatible con YOLO. Sin embargo, la exportación no se realiza automáticamente con todas las detecciones, ya que algunas detecciones podrían ser incorrectas.

El flujo recomendado es:

1. Procesar una imagen.
2. Revisar visualmente las detecciones y bounding boxes generadas.
3. Si las detecciones son correctas, presionar el botón **Agregar a exportación**.
4. Repetir el proceso con otras imágenes si se desea.
5. Presionar el botón **Exportar dataset YOLO**.

De esta forma, solo se exportan las imágenes aprobadas manualmente por el usuario.

Cada vez que se realiza una exportación, el sistema crea una carpeta nueva dentro de:

```text
exports/
```

Por ejemplo:

```text
exports/yolo_dataset_20260613_143210/
```

Dentro de esa carpeta se genera una estructura compatible con YOLO:

```text
images/train/
labels/train/
dataset.yaml
```
La exportación desde la interfaz coloca las imágenes aprobadas en el conjunto train. La separación en val y test no se realiza automáticamente, ya que requiere una selección controlada del dataset. En caso de utilizar las exportaciones para entrenamiento formal, se recomienda revisar las etiquetas y dividir manualmente el dataset en entrenamiento, validación y prueba.

El archivo `dataset.yaml` contiene las clases configuradas para el modelo.

## Cola de exportación

La cola de exportación almacena las imágenes aprobadas por el usuario durante una sesión de uso.

Al iniciar nuevamente la aplicación, la cola de exportación se limpia para comenzar desde cero. Sin embargo, las carpetas de exportación generadas anteriormente dentro de `exports/` se conservan como evidencia de exportaciones previas.

## Cambio de modelo

El modelo de detección es reemplazable. Para utilizar un modelo entrenado propio, se recomienda copiarlo a:

```text
models/best.pt
```

Por ejemplo:

```bash
mkdir -p models
cp runs/detect/senales_cr_v3/weights/best.pt models/best.pt
```

Una vez colocado el archivo en esa ruta, el sistema lo utilizará automáticamente al iniciar. Si el archivo no existe, el sistema utiliza `yolov8n.pt` como modelo de respaldo.

Esto permite actualizar el modelo de detección sin modificar la arquitectura principal del sistema.

## Consideraciones

* El sistema funciona como prototipo local.
* La calidad de la detección depende del modelo utilizado.
* Las detecciones automáticas deben revisarse antes de ser utilizadas para entrenamiento.
* El dataset exportado desde la interfaz debe entenderse como un conjunto aprobado por el usuario durante la sesión.
* El modelo especializado puede mejorar con más imágenes, mejor balance entre clases y revisión de etiquetas.
* La funcionalidad de video queda como una línea de mejora futura y requiere validación adicional.
