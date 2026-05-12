import json
from pathlib import Path
from dataclasses import asdict


class GestorAlmacenamiento:
    def __init__(self, metadata_dir: str = "data/metadata"):
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        self.imagenes_path = self.metadata_dir / "imagenes.json"
        self.detecciones_path = self.metadata_dir / "detecciones.json"
        self.etiquetas_path = self.metadata_dir / "etiquetas.json"

        self._inicializar_archivo(self.imagenes_path)
        self._inicializar_archivo(self.detecciones_path)
        self._inicializar_archivo(self.etiquetas_path)

    def _inicializar_archivo(self, ruta):
        if not ruta.exists():
            self._guardar_json(ruta, [])

    def _leer_json(self, ruta):
        with open(ruta, "r", encoding="utf-8") as archivo:
            return json.load(archivo)

    def _guardar_json(self, ruta, datos):
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=4, ensure_ascii=False)

    def guardar_imagen(self, imagen):
        imagenes = self._leer_json(self.imagenes_path)

        if any(img["id"] == imagen.id for img in imagenes):
            return False

        imagenes.append(asdict(imagen))
        self._guardar_json(self.imagenes_path, imagenes)
        return True

    def guardar_detecciones(self, detecciones):
        imagenes = self.obtener_imagenes()
        ids_imagenes = {img["id"] for img in imagenes}

        datos = self._leer_json(self.detecciones_path)
        ids_existentes = {det["id"] for det in datos}

        nuevas = 0

        for deteccion in detecciones:
            if deteccion.imagen_id not in ids_imagenes:
                raise ValueError(
                    f"No existe una imagen asociada con ID: {deteccion.imagen_id}"
                )

            if deteccion.id in ids_existentes:
                continue

            datos.append(asdict(deteccion))
            nuevas += 1

        self._guardar_json(self.detecciones_path, datos)
        return nuevas

    def guardar_etiquetas(self, etiquetas):
        detecciones = self.obtener_detecciones()
        ids_detecciones = {det["id"] for det in detecciones}

        datos = self._leer_json(self.etiquetas_path)
        ids_existentes = {etq["id"] for etq in datos}

        nuevas = 0

        for etiqueta in etiquetas:
            if etiqueta.deteccion_id not in ids_detecciones:
                raise ValueError(
                    f"No existe una detección asociada con ID: {etiqueta.deteccion_id}"
                )

            if etiqueta.id in ids_existentes:
                continue

            datos.append(asdict(etiqueta))
            nuevas += 1

        self._guardar_json(self.etiquetas_path, datos)
        return nuevas

    def obtener_imagenes(self):
        return self._leer_json(self.imagenes_path)

    def obtener_detecciones(self):
        return self._leer_json(self.detecciones_path)

    def obtener_etiquetas(self):
        return self._leer_json(self.etiquetas_path)

    def obtener_detecciones_por_imagen(self, imagen_id: str):
        return [
            deteccion for deteccion in self.obtener_detecciones()
            if deteccion["imagen_id"] == imagen_id
        ]

    def obtener_etiquetas_por_deteccion(self, deteccion_id: str):
        return [
            etiqueta for etiqueta in self.obtener_etiquetas()
            if etiqueta["deteccion_id"] == deteccion_id
        ]

    def contar_imagenes(self):
        return len(self.obtener_imagenes())

    def contar_detecciones(self):
        return len(self.obtener_detecciones())

    def contar_etiquetas(self):
        return len(self.obtener_etiquetas())

    def distribucion_por_tipo_senal(self):
        distribucion = {}

        for deteccion in self.obtener_detecciones():
            tipo = deteccion["tipo_senal"]
            distribucion[tipo] = distribucion.get(tipo, 0) + 1

        return distribucion