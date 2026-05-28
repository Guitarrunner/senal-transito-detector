import tkinter as tk
from tkinter import messagebox

from src.security.control_acceso import ControlAcceso
from src.ui.interfaz_visualizacion import InterfazVisualizacion


class Login:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Inicio de sesión")
        self.ventana.geometry("350x220")

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
        self.usuario_entry.insert(0, "admin")

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

    def validar_login(self):
        usuario = self.usuario_entry.get()
        password = self.password_entry.get()

        if self.control_acceso.validar_acceso(usuario, password):
            rol = self.control_acceso.obtener_rol(usuario)

            self.ventana.destroy()

            app = InterfazVisualizacion()
            app.label_estado.config(
                text=f"Sesión iniciada como: {rol}"
            )
            app.ejecutar()

        else:
            messagebox.showerror(
                "Acceso denegado",
                "Usuario o contraseña incorrectos."
            )

    def ejecutar(self):
        self.ventana.mainloop()