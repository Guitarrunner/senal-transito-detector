from src.processing.procesador_imagen import ProcesadorImagen


def main():
    procesador = ProcesadorImagen()

    resultado = procesador.procesar_imagen(
        ruta="data/input/test.jpg",
        imagen_id="img_001"
    )

    print("Imagen procesada correctamente")
    print("ID:", resultado["imagen"].id)
    print("Resolución:", resultado["imagen"].resolucion)
    print("Ruta procesada:", resultado["ruta_procesada"])


if __name__ == "__main__":
    main()