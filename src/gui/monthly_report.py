import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import tempfile
import os
import platform
import shutil
from .report_common import ComunReportes, MESES_ESPANOL
from ..reports.pdf_generator import generate_monthly_report, generate_monthly_excel_report
from .pdf_viewer import PDFViewer
from .print_utils import imprimir_pdf

class MonthlyReportWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Reporte Mensual de Asistencia")
        self.controlador = ComunReportes()

        # Almacenar todos los empleados para el filtrado
        self.all_employees = []

        self.crear_interfaz()
        self.center_window(900, 600)
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

        # Frame de período (Mes y Año)
        period_frame = tk.Frame(main_frame)
        period_frame.pack(fill=tk.X, pady=5)

        tk.Label(period_frame, text="Mes:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(0, 5))
        self.month_combo = ttk.Combobox(
            period_frame,
            values=[MESES_ESPANOL[i] for i in range(1, 13)],
            font=("Arial", 12),
            state="readonly",
            width=15
        )
        self.month_combo.pack(side=tk.LEFT, padx=5)
        self.month_combo.current(datetime.now().month - 1)

        tk.Label(period_frame, text="Año:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(20, 5))
        self.year_spin = tk.Spinbox(
            period_frame,
            from_=2020,
            to=2100,
            font=("Arial", 12),
            width=6
        )
        self.year_spin.delete(0, "end")
        self.year_spin.insert(0, datetime.now().year)
        self.year_spin.pack(side=tk.LEFT, padx=5)

        # Frame de búsqueda
        search_frame = tk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(10, 5))

        tk.Label(search_frame, text="Buscar Empleado:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 12), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.filter_employees)

        # Frame de lista de empleados
        list_frame = tk.Frame(main_frame, height=200)
        list_frame.pack(fill=tk.X, pady=10)
        list_frame.pack_propagate(False)

        self.employee_listbox = tk.Listbox(list_frame, font=("Arial", 12), selectmode=tk.MULTIPLE)

        scrollbar_y = tk.Scrollbar(list_frame, orient="vertical", command=self.employee_listbox.yview)
        self.employee_listbox.config(yscrollcommand=scrollbar_y.set)

        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.employee_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame para botones de selección
        selection_frame = tk.Frame(main_frame)
        selection_frame.pack(fill=tk.X, pady=5)

        tk.Button(selection_frame, text="Seleccionar Todos", command=self.select_all).pack(side=tk.LEFT, padx=5)
        tk.Button(selection_frame, text="Deseleccionar Todos", command=self.deselect_all).pack(side=tk.LEFT, padx=5)

        # Frame de acciones
        action_frame = tk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(20, 0))

        tk.Button(action_frame, text="Generar Reporte", command=self.generate_report, font=("Arial", 12), bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(action_frame, text="Salir", command=self.destroy, font=("Arial", 12), bg="#F44336", fg="white", width=15).pack(side=tk.LEFT, padx=10)

    def load_employees(self):
        """Carga la lista inicial de empleados."""
        try:
            self.all_employees = self.controlador.obtener_empleados_activos()
            self.filter_employees()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los empleados:\n{str(e)}")

    def filter_employees(self, event=None):
        """Filtra la lista de empleados según el término de búsqueda."""
        search_term = self.search_var.get().lower()

        # Guardar selecciones actuales
        selected_items = {self.employee_listbox.get(i) for i in self.employee_listbox.curselection()}

        self.employee_listbox.delete(0, tk.END)

        for emp_id, first_name, last_name in self.all_employees:
            full_name = f"{first_name} {last_name} (ID: {emp_id})"
            if search_term in full_name.lower():
                self.employee_listbox.insert(tk.END, full_name)
                # Restaurar selección si el item estaba seleccionado
                if full_name in selected_items:
                    self.employee_listbox.selection_set(tk.END)

    def select_all(self):
        self.employee_listbox.selection_set(0, tk.END)

    def deselect_all(self):
        self.employee_listbox.selection_clear(0, tk.END)

    def generate_report(self):
        """Genera el reporte para los empleados seleccionados."""
        selected_indices = self.employee_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Advertencia", "Seleccione al menos un empleado.")
            return

        try:
            month = self.month_combo.current() + 1
            year = int(self.year_spin.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("Error", "Por favor, ingrese un año válido.")
            return

        employee_data = []
        for index in selected_indices:
            emp_string = self.employee_listbox.get(index)
            try:
                emp_id = int(emp_string.split("(ID: ")[1].replace(")", ""))
                emp_name = emp_string.split(" (ID:")[0]

                # Obtener datos y horario
                report_data, total_horas, counters = self.controlador.calcular_asistencia_mensual(emp_id, month, year)

                if not report_data:
                    messagebox.showwarning("Sin Datos", f"No se encontraron datos para {emp_name} en el período seleccionado.")
                    continue

                ref_date = f"{year}-{month:02d}-01"
                schedule = self.controlador.obtener_horario_empleado(emp_id, ref_date)

                employee_data.append({
                    'nombre': emp_name,
                    'datos': report_data,
                    'horario': schedule,
                    'total_horas': total_horas,
                    'contadores': counters
                })
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo procesar a {emp_name}:\n{e}")

        if employee_data:
            self.show_preview(employee_data, year, month)

    def show_preview(self, employee_data, year, month):
        """Muestra la ventana de previsualización del PDF."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = temp_file.name

        if not generate_monthly_report(temp_path, year, month, employee_data):
            os.unlink(temp_path)
            messagebox.showerror("Error", "No se pudo generar el reporte en PDF.")
            return

        preview_window = tk.Toplevel(self)
        preview_window.title(f"Previsualización - Reporte Mensual")
        try:
            preview_window.state('zoomed')
        except tk.TclError:
            preview_window.geometry("1000x800") # Fallback for non-Windows/Mac

        main_frame = tk.Frame(preview_window, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Botones de acción
        action_frame = tk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=5)

        def save_pdf():
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Archivos PDF", "*.pdf")],
                initialfile=f"Reporte_Mensual_{MESES_ESPANOL[month]}_{year}.pdf"
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
                initialfile=f"Reporte_Mensual_{MESES_ESPANOL[month]}_{year}.xlsx"
            )
            if filename:
                if generate_monthly_excel_report(filename, year, month, employee_data):
                    messagebox.showinfo("Éxito", f"Reporte exportado a Excel:\n{filename}")
                else:
                    messagebox.showerror("Error", "No se pudo generar el archivo Excel")

        tk.Button(action_frame, text="Guardar PDF", command=save_pdf, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Imprimir", command=print_report, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Exportar a Excel", command=export_excel, bg="#FFC107", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Cerrar", command=preview_window.destroy, bg="#F44336", fg="white").pack(side=tk.RIGHT, padx=5)

        # Visor de PDF
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
