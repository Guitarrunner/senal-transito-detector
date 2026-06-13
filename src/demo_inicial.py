from src.processing.procesador_imagen import ProcesadorImagen
from src.detection.detector_senales import DetectorSenales
from src.visualization.visualizador_resultados import VisualizadorResultados
from src.storage.gestor_almacenamiento import GestorAlmacenamiento


def main():
    imagen_id = "img_001"
    ruta_imagen = "data/input/test.jpg"

    procesador = ProcesadorImagen()
    detector = DetectorSenales(confianza_minima=0.3)
    visualizador = VisualizadorResultados()
    almacenamiento = GestorAlmacenamiento()

    resultado = procesador.procesar_imagen(
        ruta=ruta_imagen,
        imagen_id=imagen_id
    )

    imagen = resultado["imagen"]
    ruta_procesada = resultado["ruta_procesada"]

    detecciones, etiquetas = detector.detectar(
        ruta_imagen=ruta_procesada,
        imagen_id=imagen.id
    )

    ruta_evidencia = visualizador.dibujar_detecciones(
        ruta_imagen=ruta_procesada,
        detecciones=detecciones,
        etiquetas=etiquetas,
        nombre_salida=f"{imagen.id}_evidencia.png"
    )

    imagen_guardada = almacenamiento.guardar_imagen(imagen)
    detecciones_guardadas = almacenamiento.guardar_detecciones(detecciones)
    etiquetas_guardadas = almacenamiento.guardar_etiquetas(etiquetas)

    print("Proceso completado")
    print(f"Imagen procesada: {ruta_procesada}")
    print(f"Evidencia visual: {ruta_evidencia}")
    print(f"Detecciones encontradas: {len(detecciones)}")
    print(f"Imagen nueva guardada: {imagen_guardada}")
    print(f"Detecciones nuevas guardadas: {detecciones_guardadas}")
    print(f"Etiquetas nuevas guardadas: {etiquetas_guardadas}")
    print(f"Total de imágenes almacenadas: {almacenamiento.contar_imagenes()}")
    print(f"Total de detecciones almacenadas: {almacenamiento.contar_detecciones()}")
    print(f"Distribución por tipo de señal: {almacenamiento.distribucion_por_tipo_senal()}")


if __name__ == "__main__":
    main()