import json
import math
import time

import subprocess

from datetime import datetime, timezone
from pathlib import Path

from src.locacion.proveedor_gps import ProveedorGPS
from src.locacion.ubicacion_gps import UbicacionGPS


class ProveedorUbicacionMacOS(ProveedorGPS):

    def __init__(
        self,
        antiguedad_maxima=30,
        precision_maxima=100
    ):
        self.ruta = (
            Path.home()
            / "Library/Application Support"
            / "SenalesTFG/ubicacion.json"
        )

        self.antiguedad_maxima = antiguedad_maxima
        self.precision_maxima = precision_maxima
        self.estado = "Sin ubicación"
        self._proceso = None

    def obtener_ubicacion(self):
        if (
            self._proceso is not None
            and self._proceso.poll() is not None
        ):
            self.estado = "Auxiliar de ubicación cerrado"
            return None
        try:
            datos = json.loads(
                self.ruta.read_text(encoding="utf-8")
            )

            latitud = float(datos["latitud"])
            longitud = float(datos["longitud"])
            precision = float(datos["precision_m"])
            timestamp = float(datos["timestamp"])

            valores = (
                latitud,
                longitud,
                precision,
                timestamp
            )

            if not all(math.isfinite(v) for v in valores):
                raise ValueError("Valores no finitos")

            if not (
                -90 <= latitud <= 90
                and -180 <= longitud <= 180
            ):
                raise ValueError("Coordenadas inválidas")

            antiguedad = time.time() - timestamp

            if not (
                0 <= antiguedad <= self.antiguedad_maxima
            ):
                self.estado = "Sin ubicación reciente"
                return None

            if not (
                0 <= precision <= self.precision_maxima
            ):
                self.estado = (
                    "Ubicación descartada por precisión"
                )
                return None

            self.estado = (
                f"Ubicación macOS · precisión estimada "
                f"{precision:.0f} m"
            )

            return UbicacionGPS(
                latitud=latitud,
                longitud=longitud,
                fecha_hora=datetime.fromtimestamp(
                    timestamp,
                    tz=timezone.utc
                ),
                precision_m=precision,
                fuente="core_location_macos"
            )

        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            OverflowError
        ):
            self.estado = "Sin ubicación disponible"
            return None

    def iniciar(self):
        if (
            self._proceso is not None
            and self._proceso.poll() is None
        ):
            return

        raiz = Path(__file__).resolve().parents[2]

        ejecutable = (
            raiz
            / "tools/ubicacion/PruebaUbicacion.app"
            / "Contents/MacOS/PruebaUbicacion"
        )

        if not ejecutable.is_file():
            raise FileNotFoundError(
                "No se encontró el auxiliar de ubicación. "
                "Debés compilar PruebaUbicacion.app."
            )

        # No reutilizar una lectura de una ejecución anterior.
        self.ruta.unlink(missing_ok=True)

        self._proceso = subprocess.Popen(
            [str(ejecutable)],
            stdout=subprocess.DEVNULL
        )

        self.estado = "Esperando ubicación de macOS"


    def cerrar(self):
        proceso = self._proceso
        self._proceso = None

        if proceso is not None:
            if proceso.poll() is None:
                proceso.terminate()

                try:
                    proceso.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    proceso.kill()
                    proceso.wait(timeout=1)

            self.ruta.unlink(missing_ok=True)

        self.estado = "Proveedor de ubicación detenido"