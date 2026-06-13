import cv2
from pathlib import Path
from datetime import datetime
from typing import Tuple

from src.domain.imagen import Imagen


class ProcesadorVideo:
    """
    Módulo encargado de cargar videos y extraer frames para análisis.
    No trabaja en tiempo real ni usa cámara.
    """

    FORMATOS_SOPORTADOS = [".mp4", ".avi", ".mov"]

    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def procesar_video(
        self,
        ruta: str,
        video_id: str,
        intervalo_segundos: int = 1,
        max_frames: int = 30,
        size: Tuple[int, int] = (640, 640)
    ):
        ruta_video = Path(ruta)

        if not ruta_video.exists():
            raise FileNotFoundError(f"No se encontró el video: {ruta}")

        if ruta_video.suffix.lower() not in self.FORMATOS_SOPORTADOS:
            raise ValueError(
                f"Formato no soportado: {ruta_video.suffix}. "
                f"Formatos permitidos: {self.FORMATOS_SOPORTADOS}"
            )

        captura = cv2.VideoCapture(str(ruta_video))

        if not captura.isOpened():
            raise ValueError(f"No se pudo abrir el video: {ruta}")

        fps = captura.get(cv2.CAP_PROP_FPS)

        if fps <= 0:
            fps = 30

        total_frames = int(captura.get(cv2.CAP_PROP_FRAME_COUNT))
        intervalo_frames = max(int(fps * intervalo_segundos), 1)

        frames_procesados = []
        frame_actual = 0
        muestras = 0

        while True:
            exito, frame = captura.read()

            if not exito:
                break

            if frame_actual % intervalo_frames == 0:
                frame_redimensionado = cv2.resize(frame, size)

                imagen_id = f"{video_id}_frame_{frame_actual}"
                nombre_salida = f"{imagen_id}_procesado.png"
                ruta_salida = self.output_dir / nombre_salida

                guardado = cv2.imwrite(
                    str(ruta_salida),
                    frame_redimensionado
                )

                if not guardado:
                    raise IOError(
                        f"No se pudo guardar el frame procesado: {ruta_salida}"
                    )

                alto, ancho = frame_redimensionado.shape[:2]
                segundo = frame_actual / fps

                metadata = {
                    "origen": "video",
                    "ruta_original": str(ruta_video),
                    "video_id": video_id,
                    "frame": frame_actual,
                    "segundo": round(segundo, 2),
                    "fps": fps,
                    "total_frames": total_frames,
                    "resolucion_procesada": f"{ancho}x{alto}"
                }

                imagen = Imagen(
                    id=imagen_id,
                    ruta=str(ruta_salida),
                    fecha_captura=datetime.now().isoformat(),
                    resolucion=f"{ancho}x{alto}",
                    metadata=metadata
                )

                frames_procesados.append(
                    {
                        "imagen": imagen,
                        "ruta_procesada": str(ruta_salida),
                        "frame": frame_actual,
                        "segundo": round(segundo, 2)
                    }
                )

                muestras += 1

                if muestras >= max_frames:
                    break

            frame_actual += 1

        captura.release()

        if not frames_procesados:
            raise ValueError("No se pudo extraer ningún frame del video.")

        return {
            "video_id": video_id,
            "ruta_video": str(ruta_video),
            "fps": fps,
            "total_frames": total_frames,
            "frames_analizados": len(frames_procesados),
            "frames": frames_procesados
        }