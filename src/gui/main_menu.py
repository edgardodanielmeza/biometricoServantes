import tkinter as tk
from tkinter import ttk
from .daily_report import DailyReportWindow
from .monthly_report import MonthlyReportWindow

class MainMenu(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("Sistema de Reportes - Menú Principal")
        self.resizable(False, False)

        self.crear_interfaz()
        self.centrar_ventana(800, 400)

    def crear_interfaz(self):
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(main_frame, text="Menú Principal de Reportes",
                 font=("Arial", 18, "bold")).pack(pady=(0, 30))

        button_frame = tk.Frame(main_frame)
        button_frame.pack(expand=True)

        buttons = [
            ("Reporte de Asistencia Diaria", self.open_daily_report),
            ("Reporte de Asistencia Mensual", self.open_monthly_report),
            ("Salir", self.quit)
        ]

        for text, command in buttons:
            btn = tk.Button(button_frame, text=text, command=command,
                          font=("Arial", 12), bg="#4CAF50", fg="white",
                          width=30, height=2)
            btn.pack(pady=10)

    def centrar_ventana(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def open_daily_report(self):
        DailyReportWindow(self)

    def open_monthly_report(self):
        MonthlyReportWindow(self)
