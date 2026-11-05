from abc import ABC, abstractmethod

from src.locacion.ubicacion_gps import (
    UbicacionGPS
)


class ProveedorGPS(ABC):

    @abstractmethod
    def obtener_ubicacion(
        self
    ) -> UbicacionGPS | None:
        pass