import tkinter as tk
from tkinter import messagebox
from .main_menu import MainMenu
from datetime import datetime, timedelta

class LoginWindow(tk.Tk):
    MAX_INTENTOS = 3
    TIEMPO_BLOQUEO = 300  # 5 minutos en segundos

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("Sistema Biométrico - Colegio Cervantes")
        self.resizable(False, False)
        self.intentos = 0
        self.tiempo_bloqueo = None

        # Configuración de estilo
        self.color_fondo = "#f0f0f0"
        self.color_boton = "#4CAF50"
        self.configure(bg=self.color_fondo)

        self.crear_interfaz()
        self.centrar_ventana(600, 300)

    def crear_interfaz(self):
        """Crea los elementos de la interfaz gráfica"""
        marco = tk.Frame(self, padx=20, pady=20, bg=self.color_fondo)
        marco.pack(expand=True)

        # Título
        tk.Label(
            marco,
            text="Inicio de Sesión",
            font=("Arial", 16, "bold"),
            bg=self.color_fondo
        ).grid(row=0, columnspan=2, pady=(0, 20))

        # Campos de usuario y contraseña
        tk.Label(
            marco,
            text="Usuario:",
            font=("Arial", 12),
            bg=self.color_fondo
        ).grid(row=1, column=0, sticky="e", pady=5)

        self.entrada_usuario = tk.Entry(marco, font=("Arial", 12), width=25)
        self.entrada_usuario.grid(row=1, column=1, pady=5, padx=10)
        self.entrada_usuario.focus_set()

        tk.Label(
            marco,
            text="Contraseña:",
            font=("Arial", 12),
            bg=self.color_fondo
        ).grid(row=2, column=0, sticky="e", pady=5)

        self.entrada_contrasena = tk.Entry(
            marco,
            show="*",
            font=("Arial", 12),
            width=25
        )
        self.entrada_contrasena.grid(row=2, column=1, pady=5, padx=10)

        # Marco para botones
        marco_botones = tk.Frame(marco, bg=self.color_fondo)
        marco_botones.grid(row=3, columnspan=2, pady=(20, 0))

        self.boton_login = tk.Button(
            marco_botones,
            text="Iniciar Sesión",
            command=self.iniciar_sesion,
            font=("Arial", 12),
            bg=self.color_boton,
            fg="white",
            width=12
        )
        self.boton_login.pack(side=tk.LEFT, padx=10)

        tk.Button(
            marco_botones,
            text="Salir",
            font=("Arial", 12),
            command=self.quit,
            bg="#f44336",
            fg="white",
            width=12
        ).pack(side=tk.LEFT, padx=10)

        # Configurar evento Enter para iniciar sesión
        self.entrada_contrasena.bind('<Return>', lambda event: self.iniciar_sesion())

        # Etiqueta de estado
        self.etiqueta_estado = tk.Label(
            marco,
            text="",
            fg="red",
            bg=self.color_fondo,
            font=("Arial", 10)
        )
        self.etiqueta_estado.grid(row=4, columnspan=2, pady=(10, 0))

    def centrar_ventana(self, ancho, alto):
        """Centra la ventana en la pantalla"""
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        x = (ancho_pantalla // 2) - (ancho // 2)
        y = (alto_pantalla // 2) - (alto // 2)
        self.geometry(f'{ancho}x{alto}+{x}+{y}')

    def verificar_bloqueo(self):
        """Verifica si la cuenta está temporalmente bloqueada"""
        if self.tiempo_bloqueo and datetime.now() < self.tiempo_bloqueo:
            tiempo_restante = (self.tiempo_bloqueo - datetime.now()).seconds
            minutos, segundos = divmod(tiempo_restante, 60)
            return f"Cuenta bloqueada. Intente nuevamente en {minutos:02d}:{segundos:02d}"
        elif self.tiempo_bloqueo:
            self.tiempo_bloqueo = None
            self.intentos = 0
        return None

    def iniciar_sesion(self):
        """Maneja el proceso de inicio de sesión"""
        # Verificar bloqueo
        estado_bloqueo = self.verificar_bloqueo()
        if estado_bloqueo:
            self.etiqueta_estado.config(text=estado_bloqueo)
            return

        usuario = self.entrada_usuario.get().strip()
        contrasena = self.entrada_contrasena.get().strip()

        # Validación básica
        if not usuario or not contrasena:
            messagebox.showwarning(
                "Advertencia",
                "Por favor complete todos los campos"
            )
            return

        # Validación de caracteres (prevención básica de SQL injection)
        caracteres_prohibidos = "'\"\\;"
        if any(c in usuario for c in caracteres_prohibidos) or any(c in contrasena for c in caracteres_prohibidos):
            messagebox.showerror(
                "Error",
                "Caracteres no permitidos en usuario o contraseña"
            )
            return

        try:
            if self.db.check_credentials(usuario, contrasena):
                messagebox.showinfo("Éxito", f"Bienvenido(a), {usuario}!")
                self.destroy()
                main_menu = MainMenu(self.db)
                main_menu.mainloop()
            else:
                self.intentos += 1
                intentos_restantes = self.MAX_INTENTOS - self.intentos

                if intentos_restantes > 0:
                    mensaje = f"Credenciales incorrectas. Intentos restantes: {intentos_restantes}"
                    self.etiqueta_estado.config(text=mensaje)
                else:
                    self.tiempo_bloqueo = datetime.now() + timedelta(seconds=self.TIEMPO_BLOQUEO)
                    estado_bloqueo = self.verificar_bloqueo()
                    self.etiqueta_estado.config(text=estado_bloqueo)
                    self.boton_login.config(state=tk.DISABLED)
                    self.after(
                        self.TIEMPO_BLOQUEO * 1000,
                        self.desbloquear_cuenta
                    )

                self.entrada_contrasena.delete(0, tk.END)
                self.entrada_usuario.focus_set()
        except Exception as error:
            messagebox.showerror("Error", f"Ocurrió un error: {str(error)}")

    def desbloquear_cuenta(self):
        """Desbloquea la cuenta después del tiempo de espera"""
        self.intentos = 0
        self.tiempo_bloqueo = None
        self.etiqueta_estado.config(text="")
        self.boton_login.config(state=tk.NORMAL)
