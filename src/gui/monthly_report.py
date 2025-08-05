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
        self._setup_ui()
        self._center_window(1000, 700)
        self._load_employees()

    def _center_window(self, width, height):
        """Centra la ventana en la pantalla"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame de controles
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)

        # Frame de periodo
        period_frame = tk.Frame(control_frame)
        period_frame.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        tk.Label(period_frame, text="Mes:", font=("Arial", 12)).grid(row=0, column=0, padx=5, sticky='e')

        self.month_combo = ttk.Combobox(
            period_frame,
            values=[MESES_ESPANOL[i] for i in range(1, 13)],
            font=("Arial", 12),
            state="readonly"
        )
        self.month_combo.grid(row=0, column=1, padx=5, sticky='w')
        self.month_combo.current(datetime.now().month - 1)

        tk.Label(period_frame, text="Año:", font=("Arial", 12)).grid(row=0, column=2, padx=5, sticky='e')

        self.year_spin = tk.Spinbox(
            period_frame,
            from_=2020,
            to=2100,
            font=("Arial", 12),
            width=5
        )
        self.year_spin.delete(0, "end")
        self.year_spin.insert(0, datetime.now().year)
        self.year_spin.grid(row=0, column=3, padx=5, sticky='w')

        # Frame de empleados
        employee_frame = tk.Frame(control_frame)
        employee_frame.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        tk.Label(employee_frame, text="Empleados:", font=("Arial", 12)).grid(row=0, column=0, padx=5, sticky='e')

        self.employee_listbox = tk.Listbox(
            employee_frame,
            selectmode=tk.MULTIPLE,
            font=("Arial", 11),
            width=30,
            height=10
        )
        scroll_employees = tk.Scrollbar(employee_frame, orient=tk.VERTICAL, command=self.employee_listbox.yview)
        self.employee_listbox.config(yscrollcommand=scroll_employees.set)

        self.employee_listbox.grid(row=0, column=1, rowspan=2, padx=5, sticky='nsew')
        scroll_employees.grid(row=0, column=2, rowspan=2, padx=0, sticky='ns')

        # Botones de selección
        select_buttons_frame = tk.Frame(employee_frame)
        select_buttons_frame.grid(row=0, column=3, rowspan=2, padx=5, sticky='n')

        tk.Button(select_buttons_frame, text="Todos", command=self._select_all, width=10).pack(pady=2)
        tk.Button(select_buttons_frame, text="Ninguno", command=self._deselect_all, width=10).pack(pady=2)

        # Frame de acciones
        action_frame = tk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=20)

        tk.Button(
            action_frame,
            text="Generar Reporte",
            command=self._generate_report,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            width=15
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            action_frame,
            text="Salir",
            command=self.destroy,
            font=("Arial", 12),
            bg="#F44336",
            fg="white",
            width=15
        ).pack(side=tk.LEFT, padx=10)

    def _load_employees(self):
        """Carga los empleados activos"""
        try:
            employees = self.controlador.obtener_empleados_activos()
            for emp in employees:
                self.employee_listbox.insert(tk.END, f"{emp[1]} {emp[2]} (ID: {emp[0]})")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los empleados:\n{str(e)}")

    def _select_all(self):
        """Selecciona todos los empleados"""
        self.employee_listbox.selection_set(0, tk.END)

    def _deselect_all(self):
        """Deselecciona todos los empleados"""
        self.employee_listbox.selection_clear(0, tk.END)

    def _generate_report(self):
        """Genera el reporte mensual"""
        try:
            month = self.month_combo.current() + 1
            year = int(self.year_spin.get())
        except:
            messagebox.showerror("Error", "Seleccione un mes y año válidos")
            return

        selected_indices = self.employee_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Advertencia", "Seleccione al menos un empleado")
            return

        employee_data = []
        error_messages = []

        for idx in selected_indices:
            employee = self.employee_listbox.get(idx)
            try:
                employee_id = int(employee.split("(ID: ")[1].replace(")", ""))
                employee_name = employee.split(" (ID:")[0]

                # Obtener datos mensuales
                data, total_hours, counters = self.controlador.calcular_asistencia_mensual(employee_id, month, year)

                if not data:
                    error_messages.append(f"No hay datos para {employee_name}")
                    continue

                # Obtener horario de referencia
                reference_date = f"{year}-{month:02d}-01"
                schedule = self.controlador.obtener_horario_empleado(employee_id, reference_date)

                employee_data.append({
                    'id': employee_id,
                    'nombre': employee_name,
                    'datos': data,
                    'horario': schedule,
                    'total_horas': total_hours,
                    'contadores': counters
                })

            except Exception as e:
                error_messages.append(f"Error procesando {employee}: {str(e)}")
                continue

        if error_messages:
            messagebox.showwarning(
                "Advertencia",
                "Se encontraron algunos errores:\n\n" + "\n".join(error_messages)
            )

        if employee_data:
            self._show_preview(employee_data, month, year)
        else:
            messagebox.showinfo("Información", "No hay datos para generar el reporte")

    def _show_preview(self, employee_data, month, year):
        """Muestra la previsualización del reporte"""
        preview = tk.Toplevel(self)
        preview.title(f"Previsualización - {MESES_ESPANOL[month]} {year}")
        preview.geometry("1100x800")

        # Crear archivo temporal
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_path = temp_file.name
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear archivo temporal:\n{str(e)}")
            return

        # Generar PDF
        if not generate_monthly_report(temp_path, year, month, employee_data):
            os.unlink(temp_path)
            messagebox.showerror("Error", "No se pudo generar el PDF")
            return

        # Frame principal
        main_frame = tk.Frame(preview, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Información del reporte
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)

        month_name = MESES_ESPANOL[month]

        # Calcular totales
        total_absences = sum(emp['contadores'].get('faltas', 0) for emp in employee_data)
        total_delays = sum(emp['contadores'].get('tardanzas', 0) for emp in employee_data)
        total_early_departures = sum(emp['contadores'].get('salidas_tempranas', 0) for emp in employee_data)

        tk.Label(
            info_frame,
            text=f"Reporte Mensual - {month_name} {year}",
            font=("Arial", 14, "bold")
        ).pack(anchor="w")

        tk.Label(
            info_frame,
            text=f"Empleados: {len(employee_data)} | Faltas: {total_absences} | Tardanzas: {total_delays} | Salidas tempranas: {total_early_departures}",
            font=("Arial", 12)
        ).pack(anchor="w")

        # Botones de acción
        action_frame = tk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)

        def save_pdf():
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Archivos PDF", "*.pdf")],
                title="Guardar reporte como",
                initialfile=f"Reporte_Mensual_{month_name}_{year}.pdf"
            )
            if filename:
                try:
                    shutil.copy(temp_path, filename)
                    messagebox.showinfo("Éxito", f"Reporte guardado en:\n{filename}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{str(e)}")

        def print_pdf():
            if imprimir_pdf(temp_path):
                messagebox.showinfo("Éxito", "Reporte enviado a la impresora")
            else:
                messagebox.showerror("Error", "No se pudo enviar a imprimir")

        def open_external():
            try:
                if platform.system() == 'Windows':
                    os.startfile(temp_path)
                elif platform.system() == 'Darwin':  # macOS
                    os.system(f'open "{temp_path}"')
                else:  # linux
                    os.system(f'xdg-open "{temp_path}"')
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el visor PDF:\n{str(e)}")

        def export_excel():
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Archivos Excel", "*.xlsx")],
                title="Exportar a Excel",
                initialfile=f"Reporte_Mensual_{month_name}_{year}.xlsx"
            )
            if filename:
                if generate_monthly_excel_report(filename, year, month, employee_data):
                    messagebox.showinfo("Éxito", f"Reporte exportado a Excel:\n{filename}")
                else:
                    messagebox.showerror("Error", "No se pudo generar el archivo Excel")

        buttons = [
            ("Guardar PDF", "#4CAF50", save_pdf),
            ("Imprimir", "#2196F3", print_pdf),
            ("Abrir en Visor", "#FF9800", open_external),
            ("Exportar a Excel", "#FFC107", export_excel),
            ("Cerrar", "#F44336", preview.destroy)
        ]

        for text, color, command in buttons:
            tk.Button(
                action_frame,
                text=text,
                bg=color,
                fg="white",
                width=15,
                command=command
            ).pack(side=tk.LEFT, padx=5)

        # Visor PDF
        pdf_frame = tk.Frame(main_frame)
        pdf_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        try:
            pdf_viewer = PDFViewer(pdf_frame)
            pdf_viewer.pack(fill=tk.BOTH, expand=True)
            pdf_viewer.show_pdf(temp_path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el visor PDF:\n{str(e)}")
            tk.Label(
                pdf_frame,
                text="Vista previa no disponible. Use los botones para guardar o imprimir.",
                font=("Arial", 12)
            ).pack(expand=True)

        # Limpieza al cerrar
        def on_close():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
            preview.destroy()

        preview.protocol("WM_DELETE_WINDOW", on_close)
