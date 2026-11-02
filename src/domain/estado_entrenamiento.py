from enum import Enum


class EstadoEntrenamiento(Enum):
    PENDIENTE = "PENDIENTE"
    ENTRENANDO = "ENTRENANDO"
    COMPLETADO = "COMPLETADO"
    ERROR = "ERROR"