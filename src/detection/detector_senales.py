from ultralytics import YOLO
from src.domain.deteccion import Deteccion
from src.domain.etiqueta import Etiqueta
import uuid


class DetectorSenales:
    def __init__(self, modelo_path: str = "runs/detect/senales_cr_v3/weights/best.pt", confianza_minima: float = 0.5):
        self.modelo = YOLO(modelo_path)
        self.confianza_minima = confianza_minima

    def detectar(self, ruta_imagen: str, imagen_id: str):
        resultados = self.modelo(ruta_imagen,
            conf=0.25,
            iou=0.45,
            agnostic_nms=True)
        detecciones = []
        etiquetas = []

        for resultado in resultados:
            for box in resultado.boxes:
                confianza = float(box.conf[0])

                if confianza < self.confianza_minima:
                    continue

                clase_id = int(box.cls[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                deteccion_id = str(uuid.uuid4())
                etiqueta_id = str(uuid.uuid4())

                deteccion = Deteccion(
                    id=deteccion_id,
                    imagen_id=imagen_id,
                    tipo_senal=str(clase_id),
                    distancia=0.0,
                    ubicacion_gps={},
                    confianza=confianza
                )

                etiqueta = Etiqueta(
                    id=etiqueta_id,
                    deteccion_id=deteccion_id,
                    bounding_box={
                        "x": int(x1),
                        "y": int(y1),
                        "ancho": int(x2 - x1),
                        "alto": int(y2 - y1)
                    }
                )

                detecciones.append(deteccion)
                etiquetas.append(etiqueta)

        return detecciones, etiquetas