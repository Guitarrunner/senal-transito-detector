from src.processing.procesador_imagen import ProcesadorImagen
from src.detection.detector_senales import DetectorSenales
from src.storage.gestor_almacenamiento import GestorAlmacenamiento


def main():
    imagen_id = "img_001"
    ruta_imagen = "data/input/test.jpg"

    procesador = ProcesadorImagen()
    detector = DetectorSenales()
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

    almacenamiento.guardar_imagen(imagen)
    almacenamiento.guardar_detecciones(detecciones)
    almacenamiento.guardar_etiquetas(etiquetas)

    print("Procesamiento completado")
    print(f"Imagen: {imagen.id}")
    print(f"Detecciones generadas: {len(detecciones)}")
    print(f"Etiquetas generadas: {len(etiquetas)}")


if __name__ == "__main__":
    main()