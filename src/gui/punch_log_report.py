import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
import tempfile
import os
import shutil
from .report_common import ComunReportes
from ..reports.pdf_generator import generate_punch_log_report, generate_punch_log_excel_report
from .pdf_viewer import PDFViewer
from .print_utils import imprimir_pdf

class PunchLogReportWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Registro de Marcaciones")
        self.controlador = ComunReportes()
        self.all_employees = []
        self.crear_interfaz()
        self.center_window(900, 500)
        self.load_employees()

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def crear_interfaz(self):
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        search_frame = tk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=5)

        tk.Label(search_frame, text="Buscar Empleado:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 12), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.filter_employees)

        list_frame = tk.Frame(main_frame, height=150)
        list_frame.pack_propagate(False)
        list_frame.pack(fill=tk.X, pady=10)

        self.empleados_listbox = tk.Listbox(list_frame, font=("Arial", 12), height=4, selectmode=tk.SINGLE)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.empleados_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.empleados_listbox.config(yscrollcommand=scrollbar.set)
        self.empleados_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        date_frame = tk.Frame(main_frame)
        date_frame.pack(fill=tk.X, pady=10)

        tk.Label(date_frame, text="Fecha Inicio:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.cal_inicio = DateEntry(date_frame, date_pattern='dd/mm/yyyy', font=("Arial", 12), width=12, locale='es_ES')
        self.cal_inicio.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        tk.Label(date_frame, text="Fecha Fin:", font=("Arial", 12)).grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.cal_fin = DateEntry(date_frame, date_pattern='dd/mm/yyyy', font=("Arial", 12), width=12, locale='es_ES')
        self.cal_fin.grid(row=0, column=3, padx=5, pady=5, sticky='w')

        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="Generar Reporte", font=("Arial", 12), command=self.generate_report, bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Salir", font=("Arial", 12), command=self.destroy, bg="#F44336", fg="white", width=15).pack(side=tk.LEFT, padx=10)

    def load_employees(self):
        self.all_employees = self.controlador.obtener_empleados_activos()
        self.filter_employees()

    def filter_employees(self, event=None):
        search_term = self.search_var.get().lower()
        self.empleados_listbox.delete(0, tk.END)

        for emp_id, first_name, last_name in self.all_employees:
            nombre_completo = f"{first_name} {last_name} (ID: {emp_id})"
            if search_term in nombre_completo.lower():
                self.empleados_listbox.insert(tk.END, nombre_completo)

    def generate_report(self):
        seleccionados = self.empleados_listbox.curselection()
        if not seleccionados:
            messagebox.showwarning("Advertencia", "Seleccione un empleado")
            return

        empleado_sel = self.empleados_listbox.get(seleccionados[0])
        try:
            employee_id = int(empleado_sel.split("(ID: ")[1].replace(")", ""))
        except:
            messagebox.showerror("Error", "Error al obtener ID del empleado")
            return

        fecha_inicio = self.cal_inicio.get_date().strftime("%Y-%m-%d")
        fecha_fin = self.cal_fin.get_date().strftime("%Y-%m-%d")

        if fecha_inicio > fecha_fin:
            messagebox.showwarning("Advertencia", "La fecha de inicio no puede ser posterior a la fecha de fin")
            return

        # This will be the new method in report_common
        datos = self.controlador.obtener_marcaciones_por_rango(employee_id, fecha_inicio, fecha_fin)
        if not datos:
            messagebox.showinfo("Información", "No se encontraron marcaciones para el período seleccionado")
            return

        self.show_preview(empleado_sel.split(" (ID:")[0], fecha_inicio, fecha_fin, datos)

    def show_preview(self, employee_name, start_date, end_date, punch_data):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = temp_file.name

        # This will be the new function in pdf_generator
        if not generate_punch_log_report(temp_path, employee_name, start_date, end_date, punch_data):
            os.unlink(temp_path)
            messagebox.showerror("Error", "No se pudo generar el reporte en PDF.")
            return

        preview_window = tk.Toplevel(self)
        preview_window.title(f"Previsualización - Registro de Marcaciones")
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
                initialfile=f"Registro_Marcaciones_{employee_name.replace(' ', '_')}.pdf"
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
                initialfile=f"Registro_Marcaciones_{employee_name.replace(' ', '_')}.xlsx"
            )
            if filename:
                if generate_punch_log_excel_report(filename, employee_name, start_date, end_date, punch_data):
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
