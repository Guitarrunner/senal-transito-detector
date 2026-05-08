import json
from dataclasses import asdict
from pathlib import Path


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
            with open(ruta, "w", encoding="utf-8") as archivo:
                json.dump([], archivo, indent=4, ensure_ascii=False)

    def _leer_json(self, ruta):
        with open(ruta, "r", encoding="utf-8") as archivo:
            return json.load(archivo)

    def _guardar_json(self, ruta, datos):
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=4, ensure_ascii=False)

    def guardar_imagen(self, imagen):
        datos = self._leer_json(self.imagenes_path)
        datos.append(asdict(imagen))
        self._guardar_json(self.imagenes_path, datos)

    def guardar_detecciones(self, detecciones):
        datos = self._leer_json(self.detecciones_path)
        datos.extend([asdict(deteccion) for deteccion in detecciones])
        self._guardar_json(self.detecciones_path, datos)

    def guardar_etiquetas(self, etiquetas):
        datos = self._leer_json(self.etiquetas_path)
        datos.extend([asdict(etiqueta) for etiqueta in etiquetas])
        self._guardar_json(self.etiquetas_path, datos)