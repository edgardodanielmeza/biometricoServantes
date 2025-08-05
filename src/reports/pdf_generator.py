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
    'Monday': 'Lunes',
    'Tuesday': 'Martes',
    'Wednesday': 'Miércoles',
    'Thursday': 'Jueves',
    'Friday': 'Viernes',
    'Saturday': 'Sábado',
    'Sunday': 'Domingo'
}

MESES_ESPANOL = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo',
    4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre',
    10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

def generate_daily_report(file_path, employee_name, start_date, end_date, attendance_data, horario_referencia):
    """Genera reporte diario de asistencia en PDF"""
    try:
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            leftMargin=10*mm,
            rightMargin=10*mm,
            topMargin=5*mm,
            bottomMargin=10*mm
        )

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

        title = Paragraph("Reporte Diario de Asistencia", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 2*mm))

        fecha_inicio = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        fecha_fin = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m/%Y")

        info_text = f"""
        <b>Empleado:</b> {employee_name}<br/>
        <b>Período:</b> {fecha_inicio} al {fecha_fin}<br/>
        <b>Horario Referencia:</b> {horario_referencia[0]} - {horario_referencia[1]}
        """
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 5*mm))

        datos_tabla = [['Fecha', 'Día', 'Horario', 'Entrada', 'Salida', 'Horas', 'Estado']]
        total_horas = timedelta()

        for dia in attendance_data:
            fecha_dt = datetime.strptime(dia['fecha'], "%Y-%m-%d")
            fecha_formateada = fecha_dt.strftime('%d/%m/%Y')

            horario_dia = f"{dia['hora_entrada_esperada']} - {dia['hora_salida_esperada']}"

            datos_tabla.append([
                fecha_formateada,
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
                except:
                    pass

        total_segundos = total_horas.total_seconds()
        horas = int(total_segundos // 3600)
        minutos = int((total_segundos % 3600) // 60)
        total_horas_str = f"{horas:02d}:{minutos:02d}:00"
        datos_tabla.append(['TOTALES', '', '', '', '', total_horas_str, ''])

        table = Table(
            datos_tabla,
            colWidths=[20*mm, 20*mm, 25*mm, 20*mm, 20*mm, 20*mm, 50*mm],
            repeatRows=1
        )

        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#70AD47')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ])

        for i in range(1, len(datos_tabla)-1):
            estado = datos_tabla[i][6]
            if estado == "Falta":
                style.add('TEXTCOLOR', (6, i), (6, i), colors.red)
            elif "Tardanza" in estado or "Salida temprana" in estado:
                style.add('TEXTCOLOR', (6, i), (6, i), colors.orange)
            style.add('FONTNAME', (6, i), (6, i), 'Helvetica-Bold')

        table.setStyle(style)
        story.append(table)
        story.append(Spacer(1, 3*mm))

        footer = Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Italic'])
        story.append(footer)

        doc.build(story)
        return True
    except Exception as e:
        print(f"Error al generar PDF diario: {e}")
        return False

def generate_monthly_report(file_path, year, month, attendance_data):
    """Genera un reporte mensual de asistencia en PDF, detallado por empleado."""
    try:
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            leftMargin=10*mm, rightMargin=10*mm,
            topMargin=10*mm, bottomMargin=10*mm
        )
        styles = getSampleStyleSheet()
        story = []
        month_name = MESES_ESPANOL.get(month, f"Mes {month}")
        logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logo.jpg')

        for i, emp_data in enumerate(attendance_data):
            if i > 0:
                story.append(PageBreak())

            if os.path.exists(logo_path):
                try:
                    logo = ReportLabImage(logo_path, width=60*mm, height=25*mm, kind='proportional')
                    logo.hAlign = 'CENTER'
                    story.append(logo)
                    story.append(Spacer(1, 2*mm))
                except Exception as e:
                    print(f"Error al cargar el logo: {e}")

            title = Paragraph(f"Reporte Mensual de Asistencia - {month_name} {year}", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 4*mm))

            emp_name = emp_data['nombre']
            counters = emp_data['contadores']
            total_horas = emp_data['total_horas']

            info_text = f"""
            <b>Empleado:</b> {emp_name}<br/>
            <b>Resumen del Mes:</b><br/>
            - Total Horas Trabajadas: <b>{total_horas}</b><br/>
            - Faltas: <font color='red'>{counters.get('faltas', 0)}</font><br/>
            - Tardanzas: <font color='orange'>{counters.get('tardanzas', 0)}</font><br/>
            - Salidas Tempranas: <font color='orange'>{counters.get('salidas_tempranas', 0)}</font>
            """
            story.append(Paragraph(info_text, styles['Normal']))
            story.append(Spacer(1, 5*mm))

            header = ['Fecha', 'Día', 'Horario', 'Entrada', 'Salida', 'Horas', 'Estado']
            datos_tabla = [header]

            for dia in emp_data['datos']:
                fecha_formateada = datetime.strptime(dia['fecha'], "%Y-%m-%d").strftime('%d/%m/%Y')
                horario_dia = f"{dia['hora_entrada_esperada']} - {dia['hora_salida_esperada']}"

                datos_tabla.append([
                    fecha_formateada,
                    dia['dia_semana'],
                    horario_dia,
                    dia.get('primera_entrada') or '--',
                    dia.get('ultima_salida') or '--',
                    dia.get('horas_trabajadas') or '00:00:00',
                    dia['estado']
                ])

            total_label = Paragraph('<b>TOTAL</b>', styles['Normal'])
            total_value = Paragraph(f"<b>{total_horas}</b>", styles['Normal'])
            datos_tabla.append(['', '', '', '', total_label, total_value, ''])

            table = Table(
                datos_tabla,
                colWidths=[22*mm, 22*mm, 28*mm, 20*mm, 20*mm, 20*mm, 40*mm],
                repeatRows=1
            )

            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F0F0F0')),
                ('ALIGN', (4, -1), (4, -1), 'RIGHT'),
            ])

            for i, row in enumerate(datos_tabla[1:], start=1):
                estado = row[6]
                if estado == "Falta":
                    style.add('TEXTCOLOR', (0, i), (-1, i), colors.red)
                elif "Tardanza" in estado or "Salida temprana" in estado:
                    style.add('TEXTCOLOR', (0, i), (-1, i), colors.orange)
                elif estado == "No laborable":
                    style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#E0E0E0'))

            table.setStyle(style)
            story.append(table)
            story.append(Spacer(1, 5*mm))

            footer = Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Italic'])
            story.append(footer)

        doc.build(story)
        return True
    except Exception as e:
        print(f"Error al generar PDF mensual: {e}")
        return False

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
    """Genera un reporte mensual de asistencia en Excel, detallado por empleado."""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        from openpyxl.utils import get_column_letter

        wb = openpyxl.Workbook()
        if "Sheet" in wb.sheetnames:
            wb.remove(wb["Sheet"])

        month_name = MESES_ESPANOL.get(month, f"Mes {month}")

        for emp_data in attendance_data:
            emp_name = emp_data['nombre']
            sheet_name = emp_name[:31]  # Excel sheet names have a 31-character limit
            ws = wb.create_sheet(title=sheet_name)

            bold_font = Font(bold=True)
            center_alignment = Alignment(horizontal='center', vertical='center')
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")

            ws.merge_cells('A1:G1')
            cell = ws['A1']
            cell.value = f"Reporte Mensual - {month_name} {year}"
            cell.font = Font(bold=True, size=16)
            cell.alignment = center_alignment

            ws.cell(row=3, column=1, value="Empleado:").font = bold_font
            ws.cell(row=3, column=2, value=emp_name)

            counters = emp_data['contadores']
            total_horas = emp_data['total_horas']

            summary_data = {
                "Total Horas:": total_horas,
                "Faltas:": counters.get('faltas', 0),
                "Tardanzas:": counters.get('tardanzas', 0),
                "Salidas Tempranas:": counters.get('salidas_tempranas', 0)
            }
            row = 4
            for label, value in summary_data.items():
                ws.cell(row=row, column=1, value=label).font = bold_font
                ws.cell(row=row, column=2, value=value)
                row += 1

            header = ['Fecha', 'Día', 'Horario', 'Entrada', 'Salida', 'Horas', 'Estado']
            table_start_row = row + 1
            for col_num, col_title in enumerate(header, 1):
                cell = ws.cell(row=table_start_row, column=col_num, value=col_title)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment

            current_row = table_start_row + 1
            for dia in emp_data['datos']:
                horario_dia = f"{dia['hora_entrada_esperada']} - {dia['hora_salida_esperada']}"
                ws.cell(row=current_row, column=1, value=dia['fecha'])
                ws.cell(row=current_row, column=2, value=dia['dia_semana'])
                ws.cell(row=current_row, column=3, value=horario_dia)
                ws.cell(row=current_row, column=4, value=dia.get('primera_entrada') or '--')
                ws.cell(row=current_row, column=5, value=dia.get('ultima_salida') or '--')
                ws.cell(row=current_row, column=6, value=dia.get('horas_trabajadas') or '00:00:00')
                ws.cell(row=current_row, column=7, value=dia['estado'])
                current_row += 1

            for col_num in range(1, len(header) + 1):
                column_letter = get_column_letter(col_num)
                ws.column_dimensions[column_letter].width = 18

        wb.save(file_path)
        return True
    except ImportError:
        print("Error: La biblioteca 'openpyxl' es necesaria para exportar a Excel.")
        return False
    except Exception as e:
        print(f"Error al generar el reporte de Excel mensual: {e}")
        return False
