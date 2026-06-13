# Control del dataset

Este documento describe las reglas utilizadas para organizar, revisar y mantener el dataset de señales de tránsito del proyecto.

## Estructura esperada

El dataset debe mantenerse en formato YOLO:

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

Cada imagen debe tener un archivo `.txt` correspondiente con el mismo nombre.

Ejemplo:

```text
dataset/images/train/foto_001.jpg
dataset/labels/train/foto_001.txt
```

## Formato de etiquetas

Cada línea dentro de un archivo `.txt` representa una señal etiquetada:

```text
<class_id> <x_center> <y_center> <width> <height>
```

Las coordenadas deben estar normalizadas entre 0 y 1.

Ejemplo:

```text
8 0.512300 0.438100 0.120000 0.180000
```

## Reglas de etiquetado

- Usar formato YOLO en LabelImg.
- Dibujar un bounding box por cada señal visible perteneciente a las clases del proyecto.
- Etiquetar todas las señales visibles de las clases definidas, aunque haya varias señales en una misma imagen.
- No etiquetar carros, peatones reales, postes, árboles u otros elementos de contexto.
- No etiquetar señales que no pertenezcan a las clases actuales, salvo que se agreguen formalmente al dataset.
- No inventar partes ocultas de una señal; el bounding box debe cubrir la parte visible de la señal.
- Revisar que la clase asignada sea correcta.
- Mantener consistencia en los nombres de clase.

## Calidad de imágenes

Se priorizan imágenes con:

- Señales visibles y reconocibles.
- Resolución suficiente.
- Variedad de distancia, ángulo e iluminación.
- Contexto vial real.
- Diferentes estados de conservación de las señales.

Se pueden incluir señales deterioradas, vandalizadas o parcialmente obstruidas si aún son reconocibles. Esto ayuda a que el sistema se adapte mejor a condiciones reales de carretera.

Se deben evitar imágenes donde:

- La señal esté demasiado borrosa.
- La señal sea demasiado pequeña.
- La señal esté cortada de forma significativa.
- La clase no pueda identificarse con seguridad.

## Orientación de imágenes

Si las imágenes tomadas con celular aparecen rotadas en LabelImg, puede deberse a metadatos EXIF. Antes de etiquetar se recomienda normalizar la orientación de las imágenes con `fix_orientation.py`


## Distribución del dataset

Distribución recomendada:

- 70% entrenamiento (`train`)
- 20% validación (`val`)
- 10% prueba (`test`)

Para un prototipo, puede trabajarse con una distribución aproximada, siempre que `val` tenga suficientes imágenes variadas para evaluar el modelo.

Una validación con muy pocas imágenes no representa adecuadamente el rendimiento del modelo, especialmente cuando existen muchas clases.

## Balance por clase

El balance por clase es importante. Si una clase tiene muchos ejemplos y otra tiene muy pocos, el modelo aprenderá mejor la clase dominante y puede fallar en clases con menos imágenes.

Como referencia inicial:

- Menos de 5 objetos por clase: muy insuficiente.
- 10 a 20 objetos por clase: útil para pruebas, pero débil.
- 30 a 50 objetos por clase: base inicial razonable.
- Más de 50 objetos por clase: mejor para entrenamiento.

## Problemas comunes

### YOLO indica muchas imágenes como background

Si durante el entrenamiento aparece algo como:

```text
0 images, 599 backgrounds
```

probablemente las etiquetas están en una carpeta incorrecta o están vacías. Las etiquetas deben estar en `dataset/labels/train`, `dataset/labels/val` o `dataset/labels/test`, según corresponda.

### Los archivos `.txt` tienen nombres de clases

Los archivos `.txt` no deben contener texto como `alto` o `velocidad_maxima`. Deben contener el ID numérico de la clase.

Correcto:

```text
8 0.512300 0.438100 0.120000 0.180000
```

Incorrecto:

```text
alto 0.512300 0.438100 0.120000 0.180000
```

### Cache desactualizado

Después de mover imágenes o etiquetas, borrar los archivos cache:

```bash
rm -f dataset/labels/train.cache dataset/labels/val.cache dataset/labels/test.cache
```

## Estado actual del dataset

El dataset actual permite validar el flujo de entrenamiento y detección, pero aún puede mejorar. Algunas clases cuentan con menos ejemplos que otras, por lo que el desempeño del modelo no será uniforme en todas las señales.

El objetivo principal en esta etapa es validar el prototipo y demostrar que el sistema permite preparar, entrenar y sustituir modelos de detección de forma modular.
