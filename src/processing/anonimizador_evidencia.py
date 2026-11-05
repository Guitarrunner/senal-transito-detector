import math
from pathlib import Path

from ultralytics import YOLO


class AnonimizadorEvidencia:

    def __init__(self):
        raiz = Path(__file__).resolve().parents[2]

        rutas = {
            "rostros": (
                raiz / "models/anonimizacion/rostros.pt"
            ),
            "placas": (
                raiz / "models/anonimizacion/placas.pt"
            )
        }

        for ruta in rutas.values():
            if not ruta.is_file():
                raise FileNotFoundError(
                    f"No se encontró el modelo: {ruta}"
                )

        self.modelos = {
            nombre: YOLO(str(ruta))
            for nombre, ruta in rutas.items()
        }

    def procesar(self, frame):
        if frame is None or frame.size == 0:
            raise ValueError(
                "La evidencia está vacía."
            )

        salida = frame.copy()
        alto, ancho = frame.shape[:2]

        cantidades = {
            "rostros": 0,
            "placas": 0
        }

        for nombre, modelo in self.modelos.items():
            resultado = modelo.predict(
                source=frame,
                conf=0.25,
                imgsz=1280,
                max_det=1000,
                save=False,
                verbose=False
            )[0]

            if resultado.boxes is None:
                continue

            cajas = (
                resultado.boxes.xyxy
                .cpu()
                .tolist()
            )

            for x1, y1, x2, y2 in cajas:
                margen_x = (x2 - x1) * 0.15
                margen_y = (y2 - y1) * 0.15

                izquierda = max(
                    0, math.floor(x1 - margen_x)
                )
                arriba = max(
                    0, math.floor(y1 - margen_y)
                )
                derecha = min(
                    ancho, math.ceil(x2 + margen_x)
                )
                abajo = min(
                    alto, math.ceil(y2 + margen_y)
                )

                if (
                    derecha <= izquierda
                    or abajo <= arriba
                ):
                    continue

                salida[
                    arriba:abajo,
                    izquierda:derecha
                ] = 0

                cantidades[nombre] += 1

        return salida, cantidades