from pathlib import Path
from PIL import Image, ImageOps

folders = [
    "dataset/images/train",
    "dataset/images/val",
    "dataset/images/test",
]

valid_extensions = [".jpg", ".jpeg", ".png"]

for folder in folders:
    folder_path = Path(folder)

    if not folder_path.exists():
        continue

    for image_path in folder_path.iterdir():
        if image_path.suffix.lower() not in valid_extensions:
            continue

        try:
            with Image.open(image_path) as img:
                fixed = ImageOps.exif_transpose(img)
                fixed.save(image_path)

            print(f"Corregida: {image_path}")

        except Exception as e:
            print(f"Error con {image_path}: {e}")
