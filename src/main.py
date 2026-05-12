from src.processing.procesador_imagen import ProcesadorImagen
from src.detection.detector_senales import DetectorSenales
from src.visualization.visualizador_resultados import VisualizadorResultados


def main():
    imagen_id = "img_001"
    ruta_imagen = "data/input/test.jpg"

    procesador = ProcesadorImagen()
    detector = DetectorSenales(confianza_minima=0.3)
    visualizador = VisualizadorResultados()

    resultado = procesador.procesar_imagen(
        ruta=ruta_imagen,
        imagen_id=imagen_id
    )

    ruta_procesada = resultado["ruta_procesada"]

    detecciones, etiquetas = detector.detectar(
        ruta_imagen=ruta_procesada,
        imagen_id=imagen_id
    )

    ruta_evidencia = visualizador.dibujar_detecciones(
        ruta_imagen=ruta_procesada,
        detecciones=detecciones,
        etiquetas=etiquetas,
        nombre_salida=f"{imagen_id}_evidencia.png"
    )

    print("Detección completada")
    print(f"Imagen procesada: {ruta_procesada}")
    print(f"Detecciones encontradas: {len(detecciones)}")
    print(f"Etiquetas generadas: {len(etiquetas)}")
    print(f"Evidencia visual generada: {ruta_evidencia}")


if __name__ == "__main__":
    main()