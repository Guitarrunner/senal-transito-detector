import cv2
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Optional

from src.domain.imagen import Imagen


class ProcesadorImagen:
    """
    Módulo encargado de cargar, validar y preprocesar imágenes.
    """

    FORMATOS_SOPORTADOS = [".jpg", ".jpeg", ".png"]

    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def cargar_imagen(self, ruta: str):
        ruta_imagen = Path(ruta)

        if not ruta_imagen.exists():
            raise FileNotFoundError(f"No se encontró la imagen: {ruta}")

        if ruta_imagen.suffix.lower() not in self.FORMATOS_SOPORTADOS:
            raise ValueError(
                f"Formato no soportado: {ruta_imagen.suffix}. "
                f"Formatos permitidos: {self.FORMATOS_SOPORTADOS}"
            )

        imagen = cv2.imread(str(ruta_imagen))

        if imagen is None:
            raise ValueError(f"No se pudo leer la imagen: {ruta}")

        return imagen
    
    def cargar_video(self, ruta: str):
    
        cap = cv2.VideoCapture(ruta)

        if not cap.isOpened():
            raise ValueError(f"No se pudo abrir el video: {ruta}")

        return cap

    def obtener_metadata(self, ruta: str, imagen) -> Dict:
        alto, ancho = imagen.shape[:2]

        return {
            "ruta_original": ruta,
            "fecha_carga": datetime.now().isoformat(),
            "ancho": ancho,
            "alto": alto,
            "canales": imagen.shape[2] if len(imagen.shape) == 3 else 1,
            "origen": "carga_manual"
        }

    def crear_entidad_imagen(self, ruta: str, imagen_id: str) -> Imagen:
        imagen = self.cargar_imagen(ruta)
        metadata = self.obtener_metadata(ruta, imagen)

        resolucion = f"{metadata['ancho']}x{metadata['alto']}"

        return Imagen(
            id=imagen_id,
            ruta=ruta,
            fecha_captura=metadata["fecha_carga"],
            resolucion=resolucion,
            metadata=metadata
        )

    def redimensionar(self, imagen, size: Tuple[int, int] = (640, 640)):
        return cv2.resize(imagen, size)

    def normalizar(self, imagen):
        return imagen / 255.0

    def guardar_imagen_procesada(self, imagen, nombre_archivo: str) -> str:
        ruta_salida = self.output_dir / nombre_archivo

        resultado = cv2.imwrite(str(ruta_salida), imagen)

        if not resultado:
            raise IOError(f"No se pudo guardar la imagen procesada en: {ruta_salida}")

        return str(ruta_salida)
    
    def convertir_rgb(self, imagen):
        return cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)

    def procesar_imagen(
        self,
        ruta: str,
        imagen_id: str,
        size: Optional[Tuple[int, int]] = (640, 640)
    ) -> Dict:
        imagen_original = self.cargar_imagen(ruta)
        entidad_imagen = self.crear_entidad_imagen(ruta, imagen_id)

        imagen_procesada = self.redimensionar(imagen_original, size)

        nombre_salida = f"{imagen_id}_procesada.png"
        ruta_procesada = self.guardar_imagen_procesada(
            imagen_procesada,
            nombre_salida
        )

        return {
            "imagen": entidad_imagen,
            "ruta_procesada": ruta_procesada,
            "metadata": entidad_imagen.metadata
        }
