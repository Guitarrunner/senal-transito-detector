import os

from datetime import datetime
from dotenv import load_dotenv

from src.locacion.ubicacion_gps import (
    UbicacionGPS
)

from src.locacion.proveedor_gps import (
    ProveedorGPS
)


load_dotenv()


class ProveedorGPSFijo(
    ProveedorGPS
):

    def __init__(self):

        latitud = os.getenv(
            "GPS_LATITUD"
        )

        longitud = os.getenv(
            "GPS_LONGITUD"
        )

        self.latitud = (
            float(latitud)
            if latitud is not None
            else None
        )

        self.longitud = (
            float(longitud)
            if longitud is not None
            else None
        )

    def obtener_ubicacion(
        self
    ) -> UbicacionGPS | None:

        if (
            self.latitud is None
            or self.longitud is None
        ):
            return None

        return UbicacionGPS(
            latitud=self.latitud,
            longitud=self.longitud,
            fecha_hora=datetime.now()
        )