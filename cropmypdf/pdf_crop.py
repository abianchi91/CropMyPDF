import os
import tkinter as tk
from tkinter import filedialog, messagebox

import numpy as np
from PIL import Image, ImageTk
import fitz  # PyMuPDF

DPI = 50
SCALE_FACTOR = 2


class PDFCropTool:
    def __init__(self):
        self.pdf_path = None
        self.doc = None
        self.images = []
        self.overlay_image = None
        self.crop_coords = None
        self.rect_start = None
        self.rect_id = None
        # Nuove variabili per le opzioni
        self.start_page = None
        self.end_page = None


        self.root = tk.Tk()
        self.root.title("Crop My PDF")

        self.canvas = tk.Canvas(self.root, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.include_cover = tk.BooleanVar(value=True)

        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        file_menu = tk.Menu(self.menu, tearoff=False)
        file_menu.add_command(label="Open PDF", command=self.load_pdf)
        file_menu.add_command(label="Save cropped PDF", command=self.save_cropped_pdf)
        self.menu.add_cascade(label="File", menu=file_menu)

        # Nuovo menu Opzioni
        options_menu = tk.Menu(self.menu, tearoff=False)
        options_menu.add_command(label="Set Start/End Page", command=self.set_page_range)
        options_menu.add_checkbutton(label="Include Cover", variable=self.include_cover)
        self.menu.add_cascade(label="Options", menu=options_menu)

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.root.mainloop()

    def load_pdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not filepath:
            return

        self.pdf_path = filepath
        self.images.clear()

        doc = fitz.open(filepath)
        pages_to_process = len(doc)

        # Determina intervallo pagine
        start = self.start_page if self.start_page is not None else 0
        end = self.end_page if self.end_page is not None else pages_to_process - 1

        page_indices = list(range(start, end + 1))

        min_width, min_height = float("inf"), float("inf")

        for i in page_indices:
            pix = doc[i].get_pixmap(dpi=DPI, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self.images.append(img)
            min_width = min(min_width, img.width)
            min_height = min(min_height, img.height)

        resized = [img.resize((min_width, min_height), Image.LANCZOS) for img in self.images]

        np_images = [np.array(img).astype(np.float32) for img in resized]
        avg_array = np.mean(np.stack(np_images), axis=0).astype(np.uint8)
        avg_image = Image.fromarray(avg_array)

        big_image = avg_image.resize((min_width * SCALE_FACTOR, min_height * SCALE_FACTOR), Image.LANCZOS)

        self.overlay_image = big_image
        self.scale_factor = SCALE_FACTOR
        self.tk_image = ImageTk.PhotoImage(big_image)
        self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

    def on_mouse_down(self, event):
        self.rect_start = (event.x, event.y)
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

    def on_mouse_drag(self, event):
        if not self.rect_start:
            return
        x0, y0 = self.rect_start
        x1, y1 = event.x, event.y
        if self.rect_id:
            self.canvas.coords(self.rect_id, x0, y0, x1, y1)
        else:
            self.rect_id = self.canvas.create_rectangle(x0, y0, x1, y1, outline="red")

    def on_mouse_up(self, event):
        if not self.rect_start:
            return
        x0, y0 = self.rect_start
        x1, y1 = event.x, event.y
        self.crop_coords = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        print("Selected area (preview):", self.crop_coords)

    def set_page_range(self):
        # Finestra popup per impostare start_page ed end_page
        popup = tk.Toplevel(self.root)
        popup.title("Set Page Range")
        tk.Label(popup, text="Start Page (1-based, blank=all)").pack()
        start_entry = tk.Entry(popup)
        start_entry.pack()
        tk.Label(popup, text="End Page (1-based, blank=all)").pack()
        end_entry = tk.Entry(popup)
        end_entry.pack()

        def set_values():
            start = start_entry.get()
            end = end_entry.get()
            self.start_page = int(start) - 1 if start else None
            self.end_page = int(end) - 1 if end else None
            popup.destroy()

        tk.Button(popup, text="OK", command=set_values).pack()

    def save_cropped_pdf(self):
        if not self.crop_coords or not self.pdf_path:
            messagebox.showerror("Error", "No area selected or PDF not loaded.")
            return

        base, ext = os.path.splitext(self.pdf_path)
        save_path = f"{base}_cropped.pdf"

        doc = fitz.open(self.pdf_path)

        preview_width = self.overlay_image.width / self.scale_factor
        preview_height = self.overlay_image.height / self.scale_factor

        x0, y0, x1, y1 = self.crop_coords
        x0 /= self.scale_factor
        y0 /= self.scale_factor
        x1 /= self.scale_factor
        y1 /= self.scale_factor

        new_pdf = fitz.open()
        for page in doc:
            if page.number == 0 and self.include_cover.get(): # cover page
                new_pdf.insert_pdf(doc, from_page=0, to_page=0)
                continue

            if self.start_page is not None and page.number < self.start_page:
                continue
            if self.end_page is not None and page.number > self.end_page:
                continue

            pw, ph = page.rect.width, page.rect.height
            sx = pw / preview_width
            sy = ph / preview_height
            local_crop = fitz.Rect(x0 * sx, y0 * sy, x1 * sx, y1 * sy)

            page.set_cropbox(local_crop)
            new_pdf.insert_pdf(doc, from_page=page.number, to_page=page.number)

        new_pdf.save(save_path)
        new_pdf.close()
        messagebox.showinfo("Success", f"PDF saved in:\n{save_path}")


# run as script
def main():
    PDFCropTool()


if __name__ == "__main__":
    main()
