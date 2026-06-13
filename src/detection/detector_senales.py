from ultralytics import YOLO
from src.domain.deteccion import Deteccion
from src.domain.etiqueta import Etiqueta
from pathlib import Path
import uuid
import yaml



class DetectorSenales:
    def __init__(self, modelo_path: str = "models/best.pt", confianza_minima: float = 0.5):
        self.modelo_path = self._resolver_modelo(modelo_path)
        self.modelo = YOLO(self.modelo_path)
        self.confianza_minima = confianza_minima
        self.clases = self._cargar_clases()

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
                    tipo_senal=self.clases.get(clase_id, str(clase_id)),
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
    
    def _resolver_modelo(self, modelo_path: str):
        ruta_modelo = Path(modelo_path)

        if ruta_modelo.exists():
            return str(ruta_modelo)

        print(
            "Advertencia: no se encontró el modelo entrenado en "
            f"'{modelo_path}'. Se usará el modelo base 'yolov8n.pt'."
        )

        return "yolov8n.pt"
    
    def _cargar_clases(self, yaml_path="dataset/dataset.yaml"):
        ruta = Path(yaml_path)

        if not ruta.exists():
            return {}

        with open(ruta, "r", encoding="utf-8") as archivo:
            datos = yaml.safe_load(archivo)

        nombres = datos.get("names", {})

        if isinstance(nombres, dict):
            return {int(k): v for k, v in nombres.items()}

        return {i: nombre for i, nombre in enumerate(nombres)}