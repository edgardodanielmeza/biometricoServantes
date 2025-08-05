import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import fitz  # PyMuPDF

class PDFViewer(tk.Frame):
    """Widget para visualizar PDFs con scroll y zoom"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg='white')

        # Contenedor principal
        self.canvas = tk.Canvas(self, bg='white')
        self.scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        # Frame interno para imágenes
        self.inner_frame = tk.Frame(self.canvas, bg='white')
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        # Layout
        self.scroll_x.pack(side="bottom", fill="x")
        self.scroll_y.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Eventos
        self.inner_frame.bind("<Configure>", self._update_scrollregion)
        self.canvas.bind("<Configure>", self._resize_images)

        # Variables
        self.images = []
        self.original_images = []

    def _update_scrollregion(self, event=None):
        """Actualiza la región de scroll"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_images(self, event=None):
        """Redimensiona imágenes al cambiar tamaño del canvas"""
        canvas_width = self.canvas.winfo_width() - 20
        if canvas_width < 1:
            return

        for img_label, (original_img, original_size) in zip(
            self.inner_frame.winfo_children(), self.original_images
        ):
            ratio = canvas_width / original_size[0]
            new_height = int(original_size[1] * ratio)
            resized_img = original_img.resize((canvas_width, new_height), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(resized_img)

            img_label.config(image=tk_img)
            img_label.image = tk_img

    def show_pdf(self, pdf_path):
        """Muestra el PDF en el widget"""
        # Limpiar contenido anterior
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.images = []
        self.original_images = []

        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                # Renderizar página a imagen (300 DPI para mejor calidad)
                pix = page.get_pixmap(dpi=150)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Guardar original para redimensionamiento
                self.original_images.append((img, (pix.width, pix.height)))

                # Crear imagen inicial
                canvas_width = self.canvas.winfo_width() - 20 if self.canvas.winfo_width() > 20 else 800
                ratio = canvas_width / pix.width
                new_height = int(pix.height * ratio)
                resized_img = img.resize((canvas_width, new_height), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(resized_img)

                # Mostrar en label
                label = tk.Label(self.inner_frame, image=tk_img, bg='white')
                label.image = tk_img
                label.pack(pady=5, padx=5)

                self.images.append(tk_img)

            doc.close()
            self._update_scrollregion()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el PDF:\n{str(e)}")
