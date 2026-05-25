import shutil
from pathlib import Path


class ExportadorDataset:
    def __init__(self, almacenamiento, export_dir: str = "exports/yolo_dataset"):
        self.almacenamiento = almacenamiento
        self.export_dir = Path(export_dir)

        self.images_dir = self.export_dir / "images"
        self.labels_dir = self.export_dir / "labels"

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)

    def exportar(self):
        imagenes = self.almacenamiento.obtener_imagenes()
        detecciones = self.almacenamiento.obtener_detecciones()
        etiquetas = self.almacenamiento.obtener_etiquetas()

        detecciones_por_imagen = self._agrupar_detecciones_por_imagen(
            detecciones
        )

        etiquetas_por_deteccion = self._agrupar_etiquetas_por_deteccion(
            etiquetas
        )

        for imagen in imagenes:
            self._exportar_imagen(
                imagen
            )

            self._exportar_etiquetas_yolo(
                imagen,
                detecciones_por_imagen,
                etiquetas_por_deteccion
            )

        self._generar_dataset_yaml()

    def _agrupar_detecciones_por_imagen(self, detecciones):
        agrupadas = {}

        for deteccion in detecciones:
            imagen_id = deteccion["imagen_id"]

            if imagen_id not in agrupadas:
                agrupadas[imagen_id] = []

            agrupadas[imagen_id].append(deteccion)

        return agrupadas

    def _agrupar_etiquetas_por_deteccion(self, etiquetas):
        agrupadas = {}

        for etiqueta in etiquetas:
            deteccion_id = etiqueta["deteccion_id"]
            agrupadas[deteccion_id] = etiqueta

        return agrupadas

    def _exportar_imagen(self, imagen):
        ruta_origen = Path(imagen["ruta"])

        if not ruta_origen.exists():
            return

        extension = ruta_origen.suffix
        ruta_destino = self.images_dir / f'{imagen["id"]}{extension}'

        shutil.copyfile(
            ruta_origen,
            ruta_destino
        )

    def _exportar_etiquetas_yolo(
        self,
        imagen,
        detecciones_por_imagen,
        etiquetas_por_deteccion
    ):
        imagen_id = imagen["id"]
        resolucion = imagen["resolucion"]

        ancho_img, alto_img = self._parsear_resolucion(
            resolucion
        )

        ruta_label = self.labels_dir / f"{imagen_id}.txt"

        lineas = []

        for deteccion in detecciones_por_imagen.get(imagen_id, []):
            etiqueta = etiquetas_por_deteccion.get(
                deteccion["id"]
            )

            if etiqueta is None:
                continue

            bbox = etiqueta["bounding_box"]

            x = bbox["x"]
            y = bbox["y"]
            ancho = bbox["ancho"]
            alto = bbox["alto"]

            x_centro = (x + ancho / 2) / ancho_img
            y_centro = (y + alto / 2) / alto_img
            ancho_norm = ancho / ancho_img
            alto_norm = alto / alto_img

            clase_id = self._convertir_tipo_a_clase(
                deteccion["tipo_senal"]
            )

            linea = (
                f"{clase_id} "
                f"{x_centro:.6f} "
                f"{y_centro:.6f} "
                f"{ancho_norm:.6f} "
                f"{alto_norm:.6f}"
            )

            lineas.append(linea)

        with open(ruta_label, "w", encoding="utf-8") as archivo:
            archivo.write("\n".join(lineas))

    def _parsear_resolucion(self, resolucion):
        ancho, alto = resolucion.split("x")
        return int(ancho), int(alto)

    def _convertir_tipo_a_clase(self, tipo_senal):
        try:
            return int(tipo_senal)
        except ValueError:
            return 0

    def _generar_dataset_yaml(self):
        contenido = """path: exports/yolo_dataset
train: images
val: images

names:
  0: objeto
"""

        ruta_yaml = self.export_dir / "dataset.yaml"

        with open(ruta_yaml, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)