import platform
import os
import tempfile
from tkinter import messagebox

def imprimir_pdf(pdf_path):
    """Imprime el PDF usando el método más confiable para Windows"""
    try:
        if platform.system() == "Windows":
            import win32api
            import win32print

            try:
                win32api.ShellExecute(
                    0,
                    "print",
                    pdf_path,
                    '/d:"%s"' % win32print.GetDefaultPrinter(),
                    ".",
                    0
                )
                return True
            except:
                try:
                    win32api.ShellExecute(
                        0,
                        "printto",
                        pdf_path,
                        '"%s"' % win32print.GetDefaultPrinter(),
                        ".",
                        0
                    )
                    return True
                except:
                    printer_name = win32print.GetDefaultPrinter()
                    if os.path.exists(pdf_path):
                        with open(pdf_path, 'rb') as f:
                            raw_data = f.read()

                        hPrinter = win32print.OpenPrinter(printer_name)
                        try:
                            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Reporte de Asistencia", None, "RAW"))
                            try:
                                win32print.StartPagePrinter(hPrinter)
                                win32print.WritePrinter(hPrinter, raw_data)
                                win32print.EndPagePrinter(hPrinter)
                            finally:
                                win32print.EndDocPrinter(hPrinter)
                        finally:
                            win32print.ClosePrinter(hPrinter)
                        return True
        return False
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo imprimir: {e}")
        return False
