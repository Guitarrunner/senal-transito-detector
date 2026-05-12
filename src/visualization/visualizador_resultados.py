import cv2
from pathlib import Path


class VisualizadorResultados:
    def __init__(self, output_dir: str = "data/evidence"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def dibujar_detecciones(self, ruta_imagen: str, detecciones, etiquetas, nombre_salida: str):
        imagen = cv2.imread(ruta_imagen)

        if imagen is None:
            raise ValueError(f"No se pudo leer la imagen: {ruta_imagen}")

        etiquetas_por_deteccion = {
            etiqueta.deteccion_id: etiqueta for etiqueta in etiquetas
        }

        for deteccion in detecciones:
            etiqueta = etiquetas_por_deteccion.get(deteccion.id)

            if etiqueta is None:
                continue

            bbox = etiqueta.bounding_box
            x = bbox["x"]
            y = bbox["y"]
            ancho = bbox["ancho"]
            alto = bbox["alto"]

            cv2.rectangle(
                imagen,
                (x, y),
                (x + ancho, y + alto),
                (0, 255, 0),
                2
            )

            texto = f"{deteccion.tipo_senal} {deteccion.confianza:.2f}"

            cv2.putText(
                imagen,
                texto,
                (x, max(y - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        ruta_salida = self.output_dir / nombre_salida
        cv2.imwrite(str(ruta_salida), imagen)

        return str(ruta_salida)