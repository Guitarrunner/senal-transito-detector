from src.storage.gestor_almacenamiento import GestorAlmacenamiento
from src.dataset.exportador_dataset import ExportadorDataset


def main():
    almacenamiento = GestorAlmacenamiento()
    exportador = ExportadorDataset(almacenamiento)

    resultado = exportador.exportar()

    print("Dataset exportado correctamente")
    print(f"Imágenes exportadas: {resultado['imagenes_exportadas']}")
    print(f"Etiquetas exportadas: {resultado['etiquetas_exportadas']}")
    print(f"Ruta: {resultado['ruta_exportacion']}")


if __name__ == "__main__":
    main()