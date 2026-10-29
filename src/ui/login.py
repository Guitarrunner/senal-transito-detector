import tkinter as tk
from tkinter import messagebox

from src.security.control_acceso import ControlAcceso
from src.ui.interfaz_visualizacion import InterfazVisualizacion


class Login:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Inicio de sesión")

        self.centrar_ventana(850, 620)

        self.ventana.bind("<Return>", lambda event: self.validar_login())

        self.control_acceso = ControlAcceso()

        self._crear_componentes()

    def _crear_componentes(self):
        titulo = tk.Label(
            self.ventana,
            text="Acceso al Sistema",
            font=("Arial", 16, "bold")
        )
        titulo.pack(pady=15)

        self.usuario_entry = tk.Entry(self.ventana)
        self.usuario_entry.pack(pady=5)
        self.usuario_entry.focus_set()

        self.password_entry = tk.Entry(
            self.ventana,
            show="*"
        )
        self.password_entry.pack(pady=5)

        boton = tk.Button(
            self.ventana,
            text="Ingresar",
            command=self.validar_login
        )
        boton.pack(pady=15)

    def centrar_ventana(self, ancho=400, alto=300):
        self.ventana.update_idletasks()

        ancho_pantalla = self.ventana.winfo_screenwidth()
        alto_pantalla = self.ventana.winfo_screenheight()

        x = (ancho_pantalla // 2) - (ancho // 2)
        y = (alto_pantalla // 2) - (alto // 2)

        self.ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.ventana.lift()
        self.ventana.attributes("-topmost", True)
        self.ventana.after(500, lambda: self.ventana.attributes("-topmost", False))
        self.ventana.focus_force()

    def validar_login(self):
        usuario = self.usuario_entry.get()
        password = self.password_entry.get()

        if self.control_acceso.validar_acceso(usuario, password):
            rol = self.control_acceso.obtener_rol(usuario)

            self.ventana.destroy()

            match rol:
                case "CAMPO":

                    app = InterfazVisualizacion(rol)
                    app.label_estado.config(
                        text=f"Sesión iniciada como: {rol}"
                    )
                    app.ejecutar()
                case "OPERADOR":
                
                    app = InterfazVisualizacion(rol)
                    app.label_estado.config(
                        text=f"Sesión iniciada como: {rol}"
                    )
                    app.ejecutar()
                case "ADMINISTRADOR":
                
                    app = InterfazVisualizacion(rol)
                    app.label_estado.config(
                        text=f"Sesión iniciada como: {rol}"
                    )
                    app.ejecutar()
                


        else:
            messagebox.showerror(
                "Acceso denegado",
                "Usuario o contraseña incorrectos."
            )
            self.usuario_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)

    def ejecutar(self):
        self.ventana.mainloop()