import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
import tempfile
import os
import shutil
from .report_common import ComunReportes
from ..reports.pdf_generator import generate_daily_summary_report, generate_daily_summary_excel_report # To be created
from .pdf_viewer import PDFViewer
from .print_utils import imprimir_pdf

class DailySummaryReportWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Resumen Diario General")
        self.controlador = ComunReportes()
        self.crear_interfaz()
        self.center_window(500, 200)

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def crear_interfaz(self):
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        date_frame = tk.Frame(main_frame)
        date_frame.pack(fill=tk.X, pady=10)

        tk.Label(date_frame, text="Seleccionar Fecha:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.cal_fecha = DateEntry(date_frame, date_pattern='dd/mm/yyyy', font=("Arial", 12), width=12, locale='es_ES')
        self.cal_fecha.pack(side=tk.LEFT, padx=5)

        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=20)

        tk.Button(btn_frame, text="Generar Reporte", font=("Arial", 12), command=self.generate_report, bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Salir", font=("Arial", 12), command=self.destroy, bg="#F44336", fg="white", width=15).pack(side=tk.LEFT, padx=10)

    def generate_report(self):
        fecha = self.cal_fecha.get_date().strftime("%Y-%m-%d")

        datos = self.controlador.obtener_asistencia_general_por_dia(fecha)
        if not datos:
            messagebox.showinfo("Información", "No se encontraron datos de asistencia para la fecha seleccionada.")
            return

        self.show_preview(fecha, datos)

    def show_preview(self, date, summary_data):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = temp_file.name

        if not generate_daily_summary_report(temp_path, date, summary_data):
            os.unlink(temp_path)
            messagebox.showerror("Error", "No se pudo generar el reporte en PDF.")
            return

        preview_window = tk.Toplevel(self)
        preview_window.title(f"Previsualización - Resumen Diario")
        try:
            preview_window.state('zoomed')
        except tk.TclError:
            preview_window.geometry("1000x800")

        main_frame = tk.Frame(preview_window, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        action_frame = tk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=5)

        def save_pdf():
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Archivos PDF", "*.pdf")],
                initialfile=f"Resumen_Diario_{date}.pdf"
            )
            if filename:
                shutil.copy(temp_path, filename)
                messagebox.showinfo("Éxito", f"Reporte guardado en:\n{filename}")

        def print_report():
            if imprimir_pdf(temp_path):
                messagebox.showinfo("Éxito", "Reporte enviado a la impresora.")
            else:
                messagebox.showerror("Error", "No se pudo enviar el reporte a la impresora.")

        def export_excel():
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Archivos Excel", "*.xlsx")],
                title="Exportar a Excel",
                initialfile=f"Resumen_Diario_{date}.xlsx"
            )
            if filename:
                if generate_daily_summary_excel_report(filename, date, summary_data):
                    messagebox.showinfo("Éxito", f"Reporte exportado a Excel:\n{filename}")
                else:
                    messagebox.showerror("Error", "No se pudo generar el archivo Excel")

        tk.Button(action_frame, text="Guardar PDF", command=save_pdf, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Imprimir", command=print_report, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Exportar a Excel", command=export_excel, bg="#FFC107", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Cerrar", command=preview_window.destroy, bg="#F44336", fg="white").pack(side=tk.RIGHT, padx=5)

        pdf_frame = tk.Frame(main_frame)
        pdf_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        try:
            pdf_viewer = PDFViewer(pdf_frame)
            pdf_viewer.pack(fill=tk.BOTH, expand=True)
            pdf_viewer.show_pdf(temp_path)
        except Exception as e:
            tk.Label(pdf_frame, text=f"Error al mostrar PDF: {e}").pack()

        def on_close():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            finally:
                preview_window.destroy()

        preview_window.protocol("WM_DELETE_WINDOW", on_close)
