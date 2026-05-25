from src.storage.gestor_almacenamiento import GestorAlmacenamiento
from src.dataset.exportador_dataset import ExportadorDataset


def main():
    almacenamiento = GestorAlmacenamiento()
    exportador = ExportadorDataset(almacenamiento)

    exportador.exportar()

    print("Dataset exportado correctamente en exports/yolo_dataset")


if __name__ == "__main__":
    main()