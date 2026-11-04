from dataclasses import dataclass
import time

import numpy as np


@dataclass
class CandidatoTemporal:
    tipo_senal: str

    bbox_actual: dict
    mejor_bbox: dict

    mejor_confianza: float
    mejor_frame: np.ndarray

    apariciones: int
    ultima_vez: float

    confirmado: bool = False


class RastreadorTemporal:

    def __init__(
        self,
        apariciones_minimas: int = 3,
        iou_minimo: float = 0.25,
        tiempo_expiracion: float = 1.0
    ):
        self.apariciones_minimas = (
            apariciones_minimas
        )

        self.iou_minimo = iou_minimo

        self.tiempo_expiracion = (
            tiempo_expiracion
        )

        self.candidatos = []

    def reiniciar(self):
        self.candidatos = []

    def actualizar(
        self,
        frame,
        detecciones,
        etiquetas
    ):
        ahora = time.monotonic()

        etiquetas_por_deteccion = {
            etiqueta.deteccion_id: etiqueta
            for etiqueta in etiquetas
        }

        candidatos_usados = set()

        confirmados = []

        for deteccion in detecciones:

            etiqueta = (
                etiquetas_por_deteccion.get(
                    deteccion.id
                )
            )

            if etiqueta is None:
                continue

            bbox = etiqueta.bounding_box

            candidato = (
                self._buscar_candidato(
                    deteccion.tipo_senal,
                    bbox,
                    candidatos_usados
                )
            )

            if candidato is None:

                candidato = CandidatoTemporal(
                    tipo_senal=(
                        deteccion.tipo_senal
                    ),

                    bbox_actual=bbox.copy(),
                    mejor_bbox=bbox.copy(),

                    mejor_confianza=(
                        deteccion.confianza
                    ),

                    mejor_frame=frame.copy(),

                    apariciones=1,
                    ultima_vez=ahora
                )

                self.candidatos.append(
                    candidato
                )

            else:

                candidato.apariciones += 1

                candidato.bbox_actual = (
                    bbox.copy()
                )

                candidato.ultima_vez = (
                    ahora
                )

                if (
                    deteccion.confianza
                    > candidato.mejor_confianza
                ):
                    candidato.mejor_confianza = (
                        deteccion.confianza
                    )

                    candidato.mejor_bbox = (
                        bbox.copy()
                    )

                    candidato.mejor_frame = (
                        frame.copy()
                    )

            candidatos_usados.add(
                id(candidato)
            )

            if (
                candidato.apariciones
                >= self.apariciones_minimas
                and not candidato.confirmado
            ):
                candidato.confirmado = True

                confirmados.append(
                    candidato
                )

        self.candidatos = [
            candidato
            for candidato in self.candidatos
            if (
                ahora
                - candidato.ultima_vez
                <= self.tiempo_expiracion
            )
        ]

        return confirmados

    def _buscar_candidato(
        self,
        tipo_senal,
        bbox,
        candidatos_usados
    ):

        mejor = None
        mejor_iou = 0.0

        for candidato in self.candidatos:

            if id(candidato) in candidatos_usados:
                continue

            if (
                candidato.tipo_senal
                != tipo_senal
            ):
                continue

            iou = self._calcular_iou(
                candidato.bbox_actual,
                bbox
            )

            if (
                iou >= self.iou_minimo
                and iou > mejor_iou
            ):
                mejor = candidato
                mejor_iou = iou

        return mejor

    def _calcular_iou(
        self,
        bbox_a,
        bbox_b
    ):

        ax1 = bbox_a["x"]
        ay1 = bbox_a["y"]
        ax2 = ax1 + bbox_a["ancho"]
        ay2 = ay1 + bbox_a["alto"]

        bx1 = bbox_b["x"]
        by1 = bbox_b["y"]
        bx2 = bx1 + bbox_b["ancho"]
        by2 = by1 + bbox_b["alto"]

        inter_x1 = max(
            ax1,
            bx1
        )

        inter_y1 = max(
            ay1,
            by1
        )

        inter_x2 = min(
            ax2,
            bx2
        )

        inter_y2 = min(
            ay2,
            by2
        )

        ancho_inter = max(
            0,
            inter_x2 - inter_x1
        )

        alto_inter = max(
            0,
            inter_y2 - inter_y1
        )

        area_inter = (
            ancho_inter
            * alto_inter
        )

        area_a = (
            bbox_a["ancho"]
            * bbox_a["alto"]
        )

        area_b = (
            bbox_b["ancho"]
            * bbox_b["alto"]
        )

        union = (
            area_a
            + area_b
            - area_inter
        )

        if union <= 0:
            return 0.0

        return (
            area_inter
            / union
        )