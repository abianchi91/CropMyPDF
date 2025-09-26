# CropMyPDF

**CropMyPDF** is a simple graphical tool that helps you remove unnecessary margins from PDF files, making them easier to read on devices like **Kindle**, **Kobo**, **reMarkable** and other e-ink readers.

## ✨ Features

- 🖼️ Shows a preview of the pages to help you choose the right crop area.
- 🖱️ Select the area to keep using your mouse.
- 📄 Keeps the first page (usually the cover) untouched.
- 💾 Saves a new cropped PDF next to the original file.

## 📦 Requirements

- Python 3.8 or higher
- tkinter (usually comes with Python)
- PyMuPDF (`fitz`)
- Pillow
- NumPy

## 🔧 Installation

```bash
git clone https://github.com/abianchi91/CropMyPDF.git
cd CropMyPDF
pip install -r requirements.txt
```

## 🚀 USAGE
```bash
# run as module
python -m cropmypdf

# or run directly
python cropmypdf/pdf_crop.py
```