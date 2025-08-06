import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
import tempfile
import os
from .report_common import ComunReportes
from ..reports.pdf_generator import generate_daily_report, generate_excel_report
from .pdf_viewer import PDFViewer

class DailyReportWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Reporte Diario de Asistencia")
        self.controlador = ComunReportes()
        self.crear_interfaz()
        self.center_window(900, 500)
        self.cargar_empleados()

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def crear_interfaz(self):
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Búsqueda
        search_frame = tk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=5)

        tk.Label(search_frame, text="Buscar Empleado:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 12), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.filtrar_empleados)

        # Lista empleados
        list_frame = tk.Frame(main_frame, height=150)
        list_frame.pack_propagate(False)
        list_frame.pack(fill=tk.X, pady=10)

        self.empleados_listbox = tk.Listbox(
            list_frame,
            font=("Arial", 12),
            height=4,
            selectmode=tk.SINGLE
        )

        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.config(command=self.empleados_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.empleados_listbox.config(yscrollcommand=scrollbar.set)
        self.empleados_listbox.place(x=0, y=0, relwidth=1, height=150)

        # Fechas
        date_frame = tk.Frame(main_frame)
        date_frame.pack(fill=tk.X, pady=10)

        tk.Label(date_frame, text="Fecha Inicio:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.cal_inicio = DateEntry(date_frame, date_pattern='dd/mm/yyyy', font=("Arial", 12), width=12)
        self.cal_inicio.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        tk.Label(date_frame, text="Fecha Fin:", font=("Arial", 12)).grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.cal_fin = DateEntry(date_frame, date_pattern='dd/mm/yyyy', font=("Arial", 12), width=12)
        self.cal_fin.grid(row=0, column=3, padx=5, pady=5, sticky='w')

        # Botones
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(
            btn_frame,
            text="Generar Reporte",
            font=("Arial", 12),
            command=self.generar_reporte,
            bg="#4CAF50",
            fg="white",
            width=15
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="Salir",
            font=("Arial", 12),
            command=self.destroy,
            bg="#F44336",
            fg="white",
            width=15
        ).pack(side=tk.LEFT, padx=10)

    def cargar_empleados(self):
        self.all_empleados = self.controlador.obtener_empleados_activos()
        self.filtrar_empleados()

    def filtrar_empleados(self, event=None):
        search_term = self.search_var.get().lower()
        self.empleados_listbox.delete(0, tk.END)

        for emp in self.all_empleados:
            nombre_completo = f"{emp[1]} {emp[2]} (ID: {emp[0]})"
            if search_term in nombre_completo.lower():
                self.empleados_listbox.insert(tk.END, nombre_completo)

    def generar_reporte(self):
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

        datos = self.controlador.calcular_asistencia_diaria(employee_id, fecha_inicio, fecha_fin)
        if not datos:
            messagebox.showinfo("Información", "No se encontraron datos para el período seleccionado")
            return

        horario_referencia = (
            datos[0]['hora_entrada_esperada'],
            datos[0]['hora_salida_esperada']
        )

        self.previsualizar_reporte(
            empleado_sel.split(" (ID:")[0],
            fecha_inicio,
            fecha_fin,
            datos,
            horario_referencia
        )

    def previsualizar_reporte(self, empleado, fecha_inicio, fecha_fin, datos, horario):
        previsualizacion = tk.Toplevel(self)
        previsualizacion.title(f"Previsualización - {empleado}")
        try:
            previsualizacion.state('zoomed')
        except tk.TclError:
            previsualizacion.geometry("1000x800") # Fallback for non-Windows/Mac

        main_frame = tk.Frame(previsualizacion, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = temp_file.name

        if not generate_daily_report(temp_path, empleado, fecha_inicio, fecha_fin, datos, horario):
            os.unlink(temp_path)
            messagebox.showerror("Error", "No se pudo generar el PDF")
            return

        # Información
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)

        tk.Label(info_frame, text=f"Empleado: {empleado}", font=("Arial", 12, "bold")).pack(anchor="w")

        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
        tk.Label(
            info_frame,
            text=f"Periodo: {fecha_inicio_dt.strftime('%d/%m/%Y')} al {fecha_fin_dt.strftime('%d/%m/%Y')}",
            font=("Arial", 12)
        ).pack(anchor="w")

        # Botones
        action_frame = tk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)

        def guardar_como():
            archivo = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Archivos PDF", "*.pdf")],
                title="Guardar reporte como",
                initialfile=f"Reporte_Asistencia_{empleado.replace(' ', '_')}_{fecha_inicio}_{fecha_fin}.pdf"
            )
            if archivo:
                import shutil
                try:
                    shutil.copy(temp_path, archivo)
                    messagebox.showinfo("Éxito", f"Reporte guardado en:\n{archivo}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")

        def imprimir_reporte():
            from .print_utils import imprimir_pdf
            if imprimir_pdf(temp_path):
                messagebox.showinfo("Éxito", "Reporte enviado a la impresora")
            else:
                messagebox.showerror("Error", "No se pudo enviar el reporte a la impresora")

        def exportar_excel():
            archivo = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Archivos de Excel", "*.xlsx")],
                title="Exportar a Excel",
                initialfile=f"Reporte_Excel_{empleado.replace(' ', '_')}_{fecha_inicio}_{fecha_fin}.xlsx"
            )
            if archivo:
                if generate_excel_report(archivo, empleado, fecha_inicio, fecha_fin, datos):
                    messagebox.showinfo("Éxito", f"Reporte exportado a Excel en:\n{archivo}")

        botones = [
            ("Guardar PDF", "#4CAF50", guardar_como),
            ("Imprimir", "#2196F3", imprimir_reporte),
            ("Exportar a Excel", "#FFC107", exportar_excel),
            ("Salir", "#F44336", previsualizacion.destroy)
        ]

        for texto, color, comando in botones:
            tk.Button(
                action_frame,
                text=texto,
                bg=color,
                fg="white",
                width=15,
                command=comando
            ).pack(side=tk.LEFT, padx=5)

        # Visor PDF
        pdf_frame = tk.Frame(main_frame)
        pdf_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        pdf_viewer = PDFViewer(pdf_frame)
        pdf_viewer.pack(fill=tk.BOTH, expand=True)
        pdf_viewer.show_pdf(temp_path)

        # Limpieza
        def limpiar_y_cerrar():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
            previsualizacion.destroy()

        previsualizacion.protocol("WM_DELETE_WINDOW", limpiar_y_cerrar)
