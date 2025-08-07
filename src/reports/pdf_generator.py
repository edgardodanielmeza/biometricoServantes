from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image as ReportLabImage, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime, timedelta
import calendar
import os

# Configuración de constantes
DIAS_ESPANOL = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
}
MESES_ESPANOL = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

def _draw_employee_report_page(story, styles, employee_name, start_date, end_date, attendance_data, horario_referencia, title_text):
    """Función auxiliar para dibujar el contenido del reporte de un empleado."""
    # Logo
    logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logo.jpg')
    if os.path.exists(logo_path):
        try:
            logo = ReportLabImage(logo_path, width=60*mm, height=25*mm, kind='proportional')
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 2*mm))
        except Exception as e:
            print(f"Error al cargar el logo: {e}")

    # Título
    title = Paragraph(title_text, styles['Title'])
    story.append(title)
    story.append(Spacer(1, 2*mm))

    # Calcular resumen de estados
    counters = {'Normal': 0, 'Falta': 0, 'Tardanza': 0, 'Salida temprana': 0}
    for dia in attendance_data:
        estado = dia['estado']
        if "Tardanza" in estado:
            counters['Tardanza'] += 1
        if "Salida temprana" in estado:
            counters['Salida temprana'] += 1
        if estado == "Normal":
            counters['Normal'] += 1
        elif estado == "Falta":
            counters['Falta'] += 1

    resumen_text = (
        f"Resumen: Normales {counters['Normal']} | "
        f"Faltas {counters['Falta']} | "
        f"Tardanzas {counters['Tardanza']} | "
        f"Salidas Tempranas {counters['Salida temprana']}"
    )

    # Información del empleado y período
    fecha_inicio_fmt = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    fecha_fin_fmt = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m/%Y")

    info_text = f"""
    <b>Empleado:</b> {employee_name}&nbsp;&nbsp;&nbsp;&nbsp;<b>Período:</b> {fecha_inicio_fmt} al {fecha_fin_fmt}<br/>
    <b>{resumen_text}</b>
    """
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 5*mm))

    # Tabla de datos
    header = ['Fecha', 'Día', 'Horario', 'Entrada', 'Salida', 'Horas', 'Estado']
    datos_tabla = [header]
    total_horas = timedelta()

    for dia in attendance_data:
        horario_dia = f"{dia['hora_entrada_esperada']} - {dia['hora_salida_esperada']}"
        datos_tabla.append([
            datetime.strptime(dia['fecha'], "%Y-%m-%d").strftime('%d/%m/%Y'),
            dia['dia_semana'],
            horario_dia,
            dia['primera_entrada'] or '--',
            dia['ultima_salida'] or '--',
            dia['horas_trabajadas'],
            dia['estado']
        ])
        if dia['primera_entrada'] and dia['ultima_salida']:
            try:
                h, m, s = map(int, dia['horas_trabajadas'].split(':'))
                total_horas += timedelta(hours=h, minutes=m, seconds=s)
            except (ValueError, TypeError):
                pass

    total_segundos = total_horas.total_seconds()
    h, m = divmod(total_segundos / 60, 60)
    total_horas_str = f"{int(h):02d}:{int(m):02d}:00"

    # Envolver texto con formato HTML en objetos Paragraph
    total_label = Paragraph('<b>TOTAL</b>', styles['Normal'])
    total_value = Paragraph(f'<b>{total_horas_str}</b>', styles['Normal'])
    datos_tabla.append(['', '', '', '', total_label, total_value, ''])

    table = Table(datos_tabla, colWidths=[20*mm, 20*mm, 25*mm, 20*mm, 20*mm, 20*mm, 50*mm], repeatRows=1)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])

    for i, row in enumerate(datos_tabla[1:-1], start=1):
        estado = row[6]
        if estado == "Falta":
            style.add('TEXTCOLOR', (6, i), (6, i), colors.red)
        elif "Tardanza" in estado or "Salida temprana" in estado:
            style.add('TEXTCOLOR', (6, i), (6, i), colors.orange)

    table.setStyle(style)
    story.append(table)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Italic']))

def generate_daily_report(file_path, employee_name, start_date, end_date, attendance_data, horario_referencia):
    """Genera un reporte diario de asistencia en PDF."""
    doc = SimpleDocTemplate(file_path, pagesize=A4, leftMargin=10*mm, rightMargin=10*mm, topMargin=5*mm, bottomMargin=10*mm)
    styles = getSampleStyleSheet()
    story = []
    _draw_employee_report_page(story, styles, employee_name, start_date, end_date, attendance_data, horario_referencia, "Reporte Diario de Asistencia")
    doc.build(story)
    return True

def generate_monthly_report(file_path, year, month, attendance_data):
    """Genera un reporte mensual de asistencia en PDF para múltiples empleados."""
    doc = SimpleDocTemplate(file_path, pagesize=A4, leftMargin=10*mm, rightMargin=10*mm, topMargin=5*mm, bottomMargin=10*mm)
    styles = getSampleStyleSheet()
    story = []

    num_dias = calendar.monthrange(year, month)[1]
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{num_dias}"
    month_name = MESES_ESPANOL.get(month, "")

    for i, emp_info in enumerate(attendance_data):
        if i > 0:
            story.append(PageBreak())

        employee_name = emp_info['nombre']
        horario_referencia = emp_info['horario']
        employee_attendance_data = emp_info['datos']

        title_text = f"Reporte Mensual de Asistencia - {month_name} {year}"
        _draw_employee_report_page(story, styles, employee_name, start_date, end_date, employee_attendance_data, horario_referencia, title_text)

    doc.build(story)
    return True

def generate_excel_report(file_path, employee_name, start_date, end_date, attendance_data):
    """Genera reporte diario en Excel"""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Asistencia Diaria"

        ws.merge_cells('A1:G1')
        ws['A1'] = f"Reporte de Asistencia - {employee_name}"
        ws['A1'].font = Font(bold=True, size=14)
        ws['A1'].alignment = Alignment(horizontal='center')

        ws['A3'] = "Período:"
        ws['B3'] = f"{start_date} a {end_date}"

        encabezados = ['Fecha', 'Día', 'Horario', 'Entrada', 'Salida', 'Horas', 'Estado']
        for col, encabezado in enumerate(encabezados, 1):
            ws.cell(row=5, column=col, value=encabezado).font = Font(bold=True)

        row = 6
        for dia in attendance_data:
            ws.cell(row=row, column=1, value=dia['fecha'])
            ws.cell(row=row, column=2, value=dia['dia_semana'])
            ws.cell(row=row, column=3, value=f"{dia['hora_entrada_esperada']}-{dia['hora_salida_esperada']}")
            ws.cell(row=row, column=4, value=dia['primera_entrada'] or "--")
            ws.cell(row=row, column=5, value=dia['ultima_salida'] or "--")
            ws.cell(row=row, column=6, value=dia['horas_trabajadas'])
            ws.cell(row=row, column=7, value=dia['estado'])
            row += 1

        for col in range(1, 8):
            ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15

        wb.save(file_path)
        return True
    except Exception as e:
        print(f"Error al generar Excel: {e}")
        return False

def generate_monthly_excel_report(file_path, year, month, attendance_data):
    """Genera reporte mensual en Excel"""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment

        wb = openpyxl.Workbook()
        ws = wb.active
        month_name = MESES_ESPANOL.get(month, f"Mes {month}")
        ws.title = f"{month_name} {year}"

        ws.merge_cells('A1:G1')
        ws['A1'] = f"Reporte Mensual - {month_name} {year}"
        ws['A1'].font = Font(bold=True, size=14)
        ws['A1'].alignment = Alignment(horizontal='center')

        row = 3
        for emp in attendance_data:
            ws.cell(row=row, column=1, value="Empleado:").font = Font(bold=True)
            ws.cell(row=row, column=2, value=emp['nombre'])
            row += 1

            ws.cell(row=row, column=1, value="Horario:").font = Font(bold=True)
            ws.cell(row=row, column=2, value=f"{emp['horario'][0]}-{emp['horario'][1]}")
            row += 2

            encabezados = ['Fecha', 'Día', 'Entrada', 'Salida', 'Horas', 'Estado']
            for col, encabezado in enumerate(encabezados, 1):
                ws.cell(row=row, column=col, value=encabezado).font = Font(bold=True)
            row += 1

            for dia in emp['datos']:
                ws.cell(row=row, column=1, value=dia['fecha'])
                ws.cell(row=row, column=2, value=dia['dia'])
                ws.cell(row=row, column=3, value=dia['entrada'] or "--")
                ws.cell(row=row, column=4, value=dia['salida'] or "--")
                ws.cell(row=row, column=5, value=dia['horas'])
                ws.cell(row=row, column=6, value=dia['estado'])
                row += 1

            ws.cell(row=row, column=4, value="Total:").font = Font(bold=True)
            ws.cell(row=row, column=5, value=emp['total_horas']).font = Font(bold=True)
            row += 2

        for col in range(1, 7):
            ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15

        wb.save(file_path)
        return True
    except Exception as e:
        print(f"Error al generar Excel mensual: {e}")
        return False

def generate_punch_log_report(file_path, employee_name, start_date, end_date, punch_data):
    """Genera un reporte con el listado de todas las marcaciones."""
    try:
        doc = SimpleDocTemplate(file_path, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=10*mm, bottomMargin=10*mm)
        styles = getSampleStyleSheet()
        story = []

        logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logo.jpg')
        if os.path.exists(logo_path):
            try:
                logo = ReportLabImage(logo_path, width=60*mm, height=25*mm, kind='proportional')
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 2*mm))
            except Exception as e:
                print(f"Error al cargar el logo: {e}")

        title = Paragraph("Registro de Marcaciones", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 5*mm))

        fecha_inicio_fmt = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        fecha_fin_fmt = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m/%Y")

        info_text = f"<b>Empleado:</b> {employee_name}&nbsp;&nbsp;&nbsp;&nbsp;<b>Período:</b> {fecha_inicio_fmt} al {fecha_fin_fmt}"
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 5*mm))

        header = ['Fecha', 'Marcaciones del Día']
        table_data = [header]
        for fecha, marcaciones in punch_data:
            table_data.append([datetime.strptime(fecha, "%Y-%m-%d").strftime('%d/%m/%Y'), marcaciones])

        table = Table(table_data, colWidths=[40*mm, 120*mm], repeatRows=1)

        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'), # Alinea a la izquierda las marcaciones
        ])

        table.setStyle(style)
        story.append(table)
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Italic']))

        doc.build(story)
        return True
    except Exception as e:
        print(f"Error al generar el PDF de registro de marcaciones: {e}")
        return False

# Placeholder for the Excel version
def generate_punch_log_excel_report(file_path, employee_name, start_date, end_date, punch_data):
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Registro de Marcaciones"

        ws.merge_cells('A1:B1')
        cell = ws['A1']
        cell.value = "Registro de Marcaciones"
        cell.font = Font(bold=True, size=16)
        cell.alignment = Alignment(horizontal='center')

        ws['A3'] = "Empleado:"
        ws['B3'] = employee_name
        ws['A4'] = "Período:"
        ws['B4'] = f"{start_date} a {end_date}"

        ws['A6'] = "Fecha"
        ws['B6'] = "Marcaciones"
        ws['A6'].font = Font(bold=True)
        ws['B6'].font = Font(bold=True)

        row = 7
        for fecha, marcaciones in punch_data:
            ws.cell(row=row, column=1, value=fecha)
            ws.cell(row=row, column=2, value=marcaciones)
            row += 1

        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 80

        wb.save(file_path)
        return True
    except Exception as e:
        print(f"Error al generar el Excel de registro de marcaciones: {e}")
        return False

def generate_incidents_report(file_path, report_date, incidents_data):
    """Genera un reporte en PDF con las incidencias de un día."""
    try:
        doc = SimpleDocTemplate(file_path, pagesize=A4, leftMargin=10*mm, rightMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
        styles = getSampleStyleSheet()
        story = []

        logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logo.jpg')
        if os.path.exists(logo_path):
            logo = ReportLabImage(logo_path, width=60*mm, height=25*mm, kind='proportional')
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 2*mm))

        report_date_fmt = datetime.strptime(report_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        title = Paragraph(f"Reporte de Incidencias - {report_date_fmt}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 8*mm))

        header = ['Empleado', 'Incidencia', 'Horario', 'Primera Marcación', 'Última Marcación']
        table_data = [header]

        for incident in incidents_data:
            detalle = incident['detalle']
            horario = f"{detalle['hora_entrada_esperada']} - {detalle['hora_salida_esperada']}"
            table_data.append([
                incident['nombre'],
                detalle['estado'],
                horario,
                detalle['primera_entrada'] or '--',
                detalle['ultima_salida'] or '--'
            ])

        table = Table(table_data, colWidths=[60*mm, 40*mm, 30*mm, 30*mm, 30*mm], repeatRows=1)

        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C00000')), # Red header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9), # Set font size for all cells
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Align names to the left
        ])

        table.setStyle(style)
        story.append(table)
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Italic']))

        doc.build(story)
        return True
    except Exception as e:
        print(f"Error al generar el PDF de incidencias: {e}")
        return False

def generate_incidents_excel_report(file_path, report_date, incidents_data):
    """Genera un reporte en Excel con las incidencias de un día."""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte de Incidencias"

        report_date_fmt = datetime.strptime(report_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        ws.merge_cells('A1:E1')
        cell = ws['A1']
        cell.value = f"Reporte de Incidencias - {report_date_fmt}"
        cell.font = Font(bold=True, size=16)
        cell.alignment = Alignment(horizontal='center')

        header = ['Empleado', 'Incidencia', 'Horario', 'Primera Marcación', 'Última Marcación']
        for col_num, col_title in enumerate(header, 1):
            cell = ws.cell(row=3, column=col_num, value=col_title)
            cell.font = Font(bold=True)

        row = 4
        for incident in incidents_data:
            detalle = incident['detalle']
            horario = f"{detalle['hora_entrada_esperada']} - {detalle['hora_salida_esperada']}"
            ws.cell(row=row, column=1, value=incident['nombre'])
            ws.cell(row=row, column=2, value=detalle['estado'])
            ws.cell(row=row, column=3, value=horario)
            ws.cell(row=row, column=4, value=detalle['primera_entrada'] or '--')
            ws.cell(row=row, column=5, value=detalle['ultima_salida'] or '--')
            row += 1

        for col_letter in ['A', 'B', 'C', 'D', 'E']:
            ws.column_dimensions[col_letter].width = 25

        wb.save(file_path)
        return True
    except Exception as e:
        print(f"Error al generar el Excel de incidencias: {e}")
        return False
