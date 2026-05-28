# Definición inicial de clases del dataset

Para la primera etapa de entrenamiento del modelo especializado se utilizará un subconjunto inicial de señales de tránsito comunes y relevantes para el contexto vial costarricense.

## Clases seleccionadas

| ID | Clase |
|---|---|
| 0 | alto |
| 1 | ceda |
| 2 | velocidad |
| 3 | curva |
| 4 | peatones |

## Justificación

Se seleccionaron estas clases por su relevancia en seguridad vial, frecuencia de aparición y facilidad relativa de identificación visual. Esta selección permite iniciar el entrenamiento con un alcance controlado, evitando abarcar desde el inicio todo el catálogo de señales de tránsito de Costa Rica.

## Consideraciones

El orden de las clases debe mantenerse fijo durante el proceso de etiquetado y entrenamiento, ya que los archivos de anotación en formato YOLO utilizan el identificador numérico de clase.

En etapas posteriores, el dataset podrá ampliarse para incluir nuevas señales del catálogo oficial.