# Entrenamiento del modelo

Este documento resume el proceso para preparar el dataset y entrenar un modelo YOLO especializado para señales de tránsito.

## 1. Preparar clases

El archivo `predefined_classes.txt` debe tener las mismas clases y el mismo orden que `dataset/dataset.yaml`.

No se debe cambiar el orden de las clases después de haber etiquetado imágenes.

## 2. Etiquetar imágenes con LabelImg

Abrir LabelImg desde la raíz del proyecto:

```bash
labelImg dataset/images/train predefined_classes.txt
```

Seleccionar formato YOLO antes de guardar etiquetas.

Cada imagen debe tener su archivo `.txt` correspondiente en la carpeta de labels:

```text
dataset/images/train/foto_001.jpg
dataset/labels/train/foto_001.txt
```

## 3. Verificar formato de etiquetas

Los labels deben tener este formato:

```text
<class_id> <x_center> <y_center> <width> <height>
```

Ejemplo:

```text
8 0.512300 0.438100 0.120000 0.180000
```

No deben contener nombres de clases.


## 4. Borrar cache si se movieron archivos

```bash
rm -f dataset/labels/train.cache dataset/labels/val.cache dataset/labels/test.cache
```

## 5. Entrenamiento de prueba

Antes de entrenar muchas épocas, ejecutar una prueba corta:

```bash
yolo detect train model=yolov8n.pt data=dataset/dataset.yaml epochs=3 imgsz=640 batch=2 name=test_dataset
```

Si el dataset está bien, YOLO debe indicar imágenes con etiquetas en `train` y `val`, no solo `backgrounds`.

## 6. Entrenamiento completo

```bash
yolo detect train model=yolov8n.pt data=dataset/dataset.yaml epochs=50 imgsz=640 batch=4 name=senales_cr_v3
```

O una versión más ligera:

```bash
yolo detect train model=yolov8n.pt data=dataset/dataset.yaml epochs=30 imgsz=640 batch=2 name=senales_cr_v3
```

## 7. Probar predicción

```bash
yolo detect predict model=runs/detect/senales_cr_v3/weights/best.pt source=dataset/images/val conf=0.10
```

## 8. Usar el modelo en el sistema

El mejor modelo entrenado queda en:

```text
runs/detect/senales_cr_v3/weights/best.pt
```

Para usarlo de forma estable en el sistema, se recomienda copiarlo a:

```text
models/best.pt
```

## 9. Consideraciones finales

El entrenamiento es un proceso incremental. Si el modelo detecta parcialmente o confunde clases, se recomienda:

- Agregar más imágenes por clase.
- Balancear clases con pocos ejemplos.
- Revisar bounding boxes inconsistentes.
- Eliminar etiquetas ambiguas.
- Separar mejor imágenes de validación.
- Reentrenar con un dataset más limpio.
