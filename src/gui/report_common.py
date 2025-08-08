import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime, timedelta
import calendar
import os
import platform

# Configuración de la base de datos
DB_PATH = r'C:\Program Files (x86)\ZKTimeNet3.0\ZKTimeNet.db'

DIAS_ESPANOL = {
    'Monday': 'Lunes',
    'Tuesday': 'Martes',
    'Wednesday': 'Miércoles',
    'Thursday': 'Jueves',
    'Friday': 'Viernes',
    'Saturday': 'Sábado',
    'Sunday': 'Domingo'
}

MESES_ESPANOL = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

class ComunReportes:
    def obtener_empleados_activos(self, incluir_admin=False):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            if incluir_admin:
                cursor.execute("""
                    SELECT id, emp_firstname, emp_lastname
                    FROM hr_employee
                    WHERE emp_active = 1
                    ORDER BY emp_lastname, emp_firstname
                """)
            else:
                cursor.execute("""
                    SELECT id, emp_firstname, emp_lastname
                    FROM hr_employee
                    WHERE emp_active = 1 AND emp_lastname != 'admin'
                    ORDER BY emp_lastname, emp_firstname
                """)
            return cursor.fetchall()

    def obtener_horario_empleado_por_dia(self, employee_id, fecha):
        """Obtiene el horario del empleado para un día específico de la semana"""
        fecha_str = fecha.strftime('%Y-%m-%d')
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    time(t.timetable_start) AS hora_inicio,
                    time(t.timetable_end) AS hora_fin
                FROM
                    hr_employee e
                JOIN
                    att_employee_shift es ON e.id = es.employee_id
                JOIN
                    att_shift s ON es.shift_id = s.id
                JOIN
                    att_shift_details sd ON s.id = sd.shift_id
                JOIN
                    att_timetable t ON sd.timetable_id = t.id
                WHERE
                    e.id = ?
                    AND ? BETWEEN es.startDate AND es.endDate
                    AND CAST(strftime('%w', ?) AS INTEGER) = CAST(strftime('%w', sd.shift_date) AS INTEGER)
                ORDER BY
                    t.timetable_start
                LIMIT 1
            """, (employee_id, fecha_str, fecha_str))
            resultado = cursor.fetchone()
            # Si no se encuentra horario, se considera día libre
            return (resultado[0][:5], resultado[1][:5]) if resultado else ("Libre", "")

    def calcular_asistencia_diaria(self, employee_id, fecha_inicio, fecha_fin):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    strftime('%Y-%m-%d', punch_time) as fecha,
                    min(strftime('%H:%M:%S', punch_time)),
                    max(strftime('%H:%M:%S', punch_time))
                FROM att_punches
                WHERE employee_id = ?
                AND date(punch_time) BETWEEN ? AND ?
                GROUP BY fecha
                ORDER BY fecha
            """, (employee_id, fecha_inicio, fecha_fin))
            registros = cursor.fetchall()

            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            delta = fecha_fin_dt - fecha_inicio_dt

            registros_dict = {registro[0]: (registro[1], registro[2]) for registro in registros}
            resultados = []

            for i in range(delta.days + 1):
                fecha_actual = fecha_inicio_dt + timedelta(days=i)
                fecha_str = fecha_actual.strftime("%Y-%m-%d")
                dia_semana_ingles = calendar.day_name[fecha_actual.weekday()]
                dia_semana = DIAS_ESPANOL.get(dia_semana_ingles, dia_semana_ingles)

                hora_entrada_esperada, hora_salida_esperada = self.obtener_horario_empleado_por_dia(employee_id, fecha_actual)

                entrada, salida = registros_dict.get(fecha_str, (None, None))

                estado = "Normal"
                if hora_entrada_esperada == "Libre":
                    estado = "Día Libre"
                elif hora_entrada_esperada == "00:00" and hora_salida_esperada == "00:00":
                    estado = "No laborable"
                elif entrada is None and salida is None:
                    estado = "Falta"
                else:
                    if entrada and hora_entrada_esperada and hora_entrada_esperada not in ["Libre", "00:00"]:
                        entrada_dt = datetime.strptime(entrada, "%H:%M:%S")
                        entrada_esperada_dt = datetime.strptime(hora_entrada_esperada, "%H:%M")
                        if entrada_dt > entrada_esperada_dt:
                            estado = "Tardanza"

                    if salida and hora_salida_esperada and hora_salida_esperada not in ["", "00:00"]:
                        salida_dt = datetime.strptime(salida, "%H:%M:%S")
                        salida_esperada_dt = datetime.strptime(hora_salida_esperada, "%H:%M")
                        if salida_dt < salida_esperada_dt:
                            estado = "Salida temprana" if estado == "Normal" else f"{estado}/Salida temprana"

                horas_trabajadas = "00:00:00"
                if entrada and salida:
                    try:
                        entrada_dt = datetime.strptime(entrada, "%H:%M:%S")
                        salida_dt = datetime.strptime(salida, "%H:%M:%S")
                        diferencia = salida_dt - entrada_dt
                        horas_trabajadas = str(diferencia)
                    except ValueError:
                        horas_trabajadas = "Error"

                resultados.append({
                    'fecha': fecha_str,
                    'dia_semana': dia_semana,
                    'primera_entrada': entrada,
                    'ultima_salida': salida,
                    'horas_trabajadas': horas_trabajadas,
                    'estado': estado,
                    'hora_entrada_esperada': hora_entrada_esperada,
                    'hora_salida_esperada': hora_salida_esperada
                })
            return resultados

    def calcular_asistencia_mensual(self, employee_id, mes, anio):
        """
        Calcula la asistencia para un mes completo llamando a la función de asistencia diaria.
        """
        try:
            num_dias = calendar.monthrange(anio, mes)[1]
            fecha_inicio = f"{anio}-{mes:02d}-01"
            fecha_fin = f"{anio}-{mes:02d}-{num_dias}"

            datos_diarios = self.calcular_asistencia_diaria(employee_id, fecha_inicio, fecha_fin)

            # La GUI mensual espera una tupla de (datos, total_horas, contadores).
            # Devolvemos los datos diarios y valores placeholder para los otros dos.
            return datos_diarios, "00:00", {}
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al calcular la asistencia mensual:\n{e}")
            return [], "00:00", {}

    def obtener_horario_empleado(self, employee_id, fecha_referencia_str):
        """
        Obtiene el horario de referencia para un empleado en una fecha dada.
        """
        try:
            fecha_obj = datetime.strptime(fecha_referencia_str, '%Y-%m-%d').date()
            return self.obtener_horario_empleado_por_dia(employee_id, fecha_obj)
        except Exception as e:
            print(f"Error al obtener horario para {fecha_referencia_str}: {e}")
            return ("Libre", "") # Devuelve Libre si hay error

    def obtener_marcaciones_por_rango(self, employee_id, fecha_inicio, fecha_fin):
        """Obtiene todas las marcaciones de un empleado en un rango de fechas."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    strftime('%Y-%m-%d', punch_time) as fecha,
                    GROUP_CONCAT(strftime('%H:%M:%S', punch_time), ', ')
                FROM att_punches
                WHERE employee_id = ?
                AND date(punch_time) BETWEEN ? AND ?
                GROUP BY fecha
                ORDER BY fecha
            """, (employee_id, fecha_inicio, fecha_fin))
            return cursor.fetchall()

    def obtener_incidencias_por_dia(self, fecha):
        """
        Obtiene una lista de todos los empleados con incidencias (faltas, tardanzas, etc.)
        en un día específico.
        """
        incidents = []
        employees = self.obtener_empleados_activos()

        for emp_id, first_name, last_name in employees:
            # calcular_asistencia_diaria devuelve una lista, tomamos el primer elemento
            daily_data = self.calcular_asistencia_diaria(emp_id, fecha, fecha)
            if not daily_data:
                continue

            asistencia_dia = daily_data[0]
            estado = asistencia_dia['estado']

            # Definir qué estados se consideran una incidencia
            estados_incidencia = ["Falta", "Tardanza", "Salida temprana"]

            if any(inc in estado for inc in estados_incidencia):
                incidents.append({
                    'nombre': f"{first_name} {last_name}",
                    'id': emp_id,
                    'detalle': asistencia_dia
                })
        return incidents

    def obtener_asistencia_general_por_dia(self, fecha):
        """
        Obtiene el estado de asistencia de todos los empleados para un día específico.
        """
        summary = []
        employees = self.obtener_empleados_activos()

        for emp_id, first_name, last_name in employees:
            daily_data = self.calcular_asistencia_diaria(emp_id, fecha, fecha)
            if not daily_data:
                continue

            asistencia_dia = daily_data[0]
            summary.append({
                'nombre': f"{first_name} {last_name}",
                'id': emp_id,
                'detalle': asistencia_dia
            })
        return summary
