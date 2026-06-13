# Clases del dataset

Este documento define las clases utilizadas para el entrenamiento del modelo de detección de señales de tránsito. Las clases están organizadas para trabajar con YOLO, por lo que el orden numérico debe mantenerse fijo durante el etiquetado y entrenamiento.

## Criterio de selección

Para esta etapa del proyecto se decidió trabajar con clases específicas de señales de tránsito, en lugar de utilizar únicamente familias generales como "reglamentación", "prevención" o "información". Esto permite que el modelo aprenda a diferenciar señales concretas como `alto`, `ceda`, `no_estacionar` o `velocidad_maxima`.

Las categorías generales pueden utilizarse para análisis o documentación, pero las etiquetas del modelo deben corresponder a las clases definidas en `dataset.yaml`.

## Clases actuales

| ID | Clase |
|---:|---|
| 0 | velocidad_maxima |
| 1 | parada_buses |
| 2 | parada_taxis |
| 3 | estacionamiento |
| 4 | no_hay_paso |
| 5 | no_estacionar |
| 6 | silencio |
| 7 | ceda |
| 8 | alto |
| 9 | no_virar_izquierda |
| 10 | no_virar_derecha |
| 11 | curva_derecha |
| 12 | curva_izquierda |
| 13 | transeunte |
| 14 | zona_escolar |
| 15 | precaucion |
| 16 | semaforo |
| 17 | pendiente |
| 18 | reductor_velocidad |
| 19 | dos_carriles_a_uno |
| 20 | interseccion |
| 21 | tren |
| 22 | reductores_de_velocidad |
| 23 | informacion |
| 24 | turismo |
| 25 | obras |
| 26 | lugares |
| 27 | rotonda |
| 28 | giro_amplio |
| 29 | no_vehiculos_pesados |
| 30 | carril_reversible |
| 31 | carril_exclusivo |
| 32 | delineador_curva |
| 33 | obstaculo |
| 34 | altura_maxima |

## Relación con `predefined_classes.txt`

El archivo `predefined_classes.txt` debe contener las mismas clases y en el mismo orden que `dataset/dataset.yaml`.

En LabelImg se selecciona el nombre de la clase, pero el archivo de etiqueta YOLO guarda el identificador numérico.

Ejemplo:

```text
alto
```

se guarda como:

```text
8 0.512300 0.438100 0.120000 0.180000
```

porque `alto` corresponde al ID 8.

## Reglas importantes

- No cambiar el orden de las clases después de haber etiquetado imágenes.
- Si se agregan nuevas clases, agregarlas al final de la lista.
- No eliminar clases existentes si ya hay etiquetas generadas.
- No mezclar nombres y números dentro de los archivos `.txt` de etiquetas.
- Los `.txt` de YOLO deben contener únicamente números y coordenadas normalizadas.

## Objetos que no se etiquetan

En esta etapa no se etiquetan carros, peatones reales, árboles, postes, edificios, aceras ni otros elementos del entorno. Estos objetos pueden aparecer en las imágenes como contexto, pero no forman parte de las clases objetivo del modelo.

La clase `transeunte` se refiere a la señal de tránsito asociada a peatones o cruce peatonal, no a personas reales caminando.

## Señales deterioradas u obstruidas

Las señales deterioradas, vandalizadas, inclinadas o parcialmente obstruidas pueden ser útiles para entrenar el modelo en condiciones reales. Sin embargo, se deben etiquetar solo si la señal sigue siendo reconocible.

Se recomienda etiquetar:

- Señales claras y completas.
- Señales algo inclinadas o con perspectiva.
- Señales viejas o sucias, pero reconocibles.
- Señales parcialmente tapadas, si la clase se identifica con seguridad.

Se recomienda no etiquetar:

- Señales demasiado borrosas.
- Señales muy lejanas.
- Señales cortadas a la mitad.
- Señales donde no se puede identificar la clase con seguridad.

## Ampliación futura

El sistema es escalable. Que una clase no esté incluida en esta primera versión no impide agregarla posteriormente. Para hacerlo correctamente, se debe:

1. Agregar la clase al final de `dataset.yaml`.
2. Agregar la misma clase al final de `predefined_classes.txt`.
3. Recolectar imágenes suficientes de esa clase.
4. Etiquetar las imágenes con consistencia.
5. Reentrenar el modelo.
