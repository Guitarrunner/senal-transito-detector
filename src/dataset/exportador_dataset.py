import shutil
from pathlib import Path

import yaml


class ExportadorDataset:
    def __init__(
        self,
        almacenamiento,
        export_dir: str = "exports/yolo_dataset",
        dataset_yaml_path: str = "dataset/dataset.yaml"
    ):
        self.almacenamiento = almacenamiento
        self.export_dir = Path(export_dir)
        self.dataset_yaml_path = Path(dataset_yaml_path)

        self.images_dir = self.export_dir / "images" / "train"
        self.labels_dir = self.export_dir / "labels" / "train"

        self.clases = self._cargar_clases()
        self.nombre_a_id = {
            nombre: clase_id for clase_id, nombre in self.clases.items()
        }

    def exportar(self,solo_aprobadas=True):
        imagenes = self.almacenamiento.obtener_imagenes()

        if solo_aprobadas:
            ids_aprobadas = self.almacenamiento.obtener_imagenes_para_exportacion()

            if not ids_aprobadas:
                return {
                    "imagenes_exportadas": 0,
                    "etiquetas_exportadas": 0,
                    "ruta_exportacion": str(self.export_dir)
                }

            imagenes = [
                imagen for imagen in imagenes
                if imagen["id"] in ids_aprobadas
            ]

        imagenes = [
            imagen for imagen in imagenes
            if Path(imagen["ruta"]).exists()
        ]

        if not imagenes:
            return {
                "imagenes_exportadas": 0,
                "etiquetas_exportadas": 0,
                "ruta_exportacion": str(self.export_dir)
            }

        self._preparar_directorios()

        detecciones = self.almacenamiento.obtener_detecciones()
        etiquetas = self.almacenamiento.obtener_etiquetas()

        detecciones_por_imagen = self._agrupar_detecciones_por_imagen(detecciones)
        etiquetas_por_deteccion = self._agrupar_etiquetas_por_deteccion(etiquetas)

        imagenes_exportadas = 0
        etiquetas_exportadas = 0

        for imagen in imagenes:
            exportada = self._exportar_imagen(imagen)

            if exportada:
                imagenes_exportadas += 1

            etiquetas_exportadas += self._exportar_etiquetas_yolo(
                imagen,
                detecciones_por_imagen,
                etiquetas_por_deteccion
            )

        self._generar_dataset_yaml()

        return {
            "imagenes_exportadas": imagenes_exportadas,
            "etiquetas_exportadas": etiquetas_exportadas,
            "ruta_exportacion": str(self.export_dir)
        }

    def _cargar_clases(self):
        if not self.dataset_yaml_path.exists():
            return {0: "objeto_detectado"}

        with open(self.dataset_yaml_path, "r", encoding="utf-8") as archivo:
            datos = yaml.safe_load(archivo)

        nombres = datos.get("names", {})

        if isinstance(nombres, dict):
            return {int(clase_id): nombre for clase_id, nombre in nombres.items()}

        return {clase_id: nombre for clase_id, nombre in enumerate(nombres)}

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
            return False

        extension = ruta_origen.suffix.lower()
        ruta_destino = self.images_dir / f'{imagen["id"]}{extension}'

        shutil.copyfile(ruta_origen, ruta_destino)

        return True

    def _exportar_etiquetas_yolo(
        self,
        imagen,
        detecciones_por_imagen,
        etiquetas_por_deteccion
    ):
        imagen_id = imagen["id"]
        resolucion = imagen["resolucion"]

        ancho_img, alto_img = self._parsear_resolucion(resolucion)

        ruta_label = self.labels_dir / f"{imagen_id}.txt"

        lineas = []

        for deteccion in detecciones_por_imagen.get(imagen_id, []):
            etiqueta = etiquetas_por_deteccion.get(deteccion["id"])

            if etiqueta is None:
                continue

            clase_id = self._convertir_tipo_a_clase(deteccion["tipo_senal"])

            if clase_id is None:
                continue

            bbox = etiqueta["bounding_box"]

            x = bbox["x"]
            y = bbox["y"]
            ancho = bbox["ancho"]
            alto = bbox["alto"]

            x, y, ancho, alto = self._ajustar_bbox(
                x,
                y,
                ancho,
                alto,
                ancho_img,
                alto_img
            )

            if ancho <= 0 or alto <= 0:
                continue

            x_centro = (x + ancho / 2) / ancho_img
            y_centro = (y + alto / 2) / alto_img
            ancho_norm = ancho / ancho_img
            alto_norm = alto / alto_img

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

        return len(lineas)

    def _parsear_resolucion(self, resolucion):
        ancho, alto = resolucion.split("x")
        return int(ancho), int(alto)

    def _convertir_tipo_a_clase(self, tipo_senal):
        """
        Permite exportar tanto detecciones guardadas con número de clase
        como detecciones guardadas con nombre de clase.
        """
        tipo = str(tipo_senal)

        try:
            clase_id = int(tipo)
            if clase_id in self.clases:
                return clase_id
            return None
        except ValueError:
            return self.nombre_a_id.get(tipo)

    def _ajustar_bbox(self, x, y, ancho, alto, ancho_img, alto_img):
        """
        Evita que una caja se salga de la imagen.
        """
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(ancho_img, x + ancho)
        y2 = min(alto_img, y + alto)

        nuevo_ancho = x2 - x1
        nuevo_alto = y2 - y1

        return x1, y1, nuevo_ancho, nuevo_alto

    def _generar_dataset_yaml(self):
        contenido = {
            "path": str(self.export_dir),
            "train": "images/train",
            "val": "images/train",
            "names": self.clases
        }

        ruta_yaml = self.export_dir / "dataset.yaml"

        with open(ruta_yaml, "w", encoding="utf-8") as archivo:
            yaml.safe_dump(
                contenido,
                archivo,
                allow_unicode=True,
                sort_keys=False
            )

    def _preparar_directorios(self):
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)