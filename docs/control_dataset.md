# Control del dataset

## Clases iniciales

| ID | Clase |
|---|---|
| 0 | alto |
| 1 | ceda |
| 2 | velocidad |
| 3 | curva |
| 4 | peatones |

## Criterios de selección de imágenes

- Imágenes con señales visibles.
- Imágenes con resolución suficiente para identificar la señal.
- Variaciones de ángulo, distancia e iluminación.
- Preferencia por imágenes del contexto vial costarricense.
- Exclusión de imágenes extremadamente borrosas u obstruidas.

## Reglas de etiquetado

- Usar formato YOLO.
- Dibujar un bounding box por cada señal visible.
- Mantener el identificador de clase según `dataset.yaml`.
- Revisar manualmente las etiquetas antes de entrenar.
- No modificar el orden de clases una vez iniciado el etiquetado.

## Distribución sugerida

- 70% entrenamiento
- 20% validación
- 10% prueba