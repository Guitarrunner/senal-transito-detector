import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


class InterfazVisualizacion:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Sistema de Reconocimiento de Señales de Tránsito")
        self.ventana.geometry("900x650")

        self.imagen_tk = None

        self._crear_componentes()

    def _crear_componentes(self):
        titulo = tk.Label(
            self.ventana,
            text="Visualización de Resultados",
            font=("Arial", 18, "bold")
        )
        titulo.pack(pady=10)

        boton_cargar = tk.Button(
            self.ventana,
            text="Cargar imagen",
            command=self.cargar_imagen
        )
        boton_cargar.pack(pady=5)

        self.label_ruta = tk.Label(
            self.ventana,
            text="No se ha cargado ninguna imagen",
            font=("Arial", 10)
        )
        self.label_ruta.pack(pady=5)

        self.canvas = tk.Label(self.ventana)
        self.canvas.pack(pady=10)

    def cargar_imagen(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png"),
                ("Todos los archivos", "*.*")
            ]
        )

        if not ruta:
            return

        try:
            imagen = Image.open(ruta)
            imagen.thumbnail((800, 500))

            self.imagen_tk = ImageTk.PhotoImage(imagen)
            self.canvas.configure(image=self.imagen_tk)
            self.label_ruta.configure(text=f"Imagen cargada: {ruta}")

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No se pudo cargar la imagen.\n{error}"
            )

    def ejecutar(self):
        self.ventana.mainloop()