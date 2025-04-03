import tkinter as tk
from tkinter import filedialog, messagebox
from pdf2image import convert_from_path
from PIL import Image, ImageTk, ImageDraw
import fitz  # PyMuPDF
import os

class EaxmSpliter:
    def __init__(self):
        self.doc = None

    def open_pdf(self, pdf_path):
        """ Opens the PDF and converts it to images. """
        self.doc = fitz.open(pdf_path)
        images = convert_from_path(pdf_path, dpi=150)
        return images

    def save_cropped_pdfs(self, crop_points, output_dir):
        """ Saves cropped sections as separate PDFs. """
        if not crop_points:
            raise ValueError("No crop points selected!")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for page_number, crop_list in crop_points.items():
            if not crop_list:
                continue

            page = self.doc[page_number]
            crop_list.sort()

            for i, start_y_percent in enumerate(crop_list):
                end_y_percent = crop_list[i + 1] if i + 1 < len(crop_list) else 1.0

                # Convert relative Y positions to absolute coordinates
                page_height = page.rect.height
                start_y = start_y_percent * page_height
                end_y = end_y_percent * page_height

                cropped_page = page.cropbox
                cropped_page.y0 = start_y
                cropped_page.y1 = end_y

                new_doc = fitz.open()
                new_page = new_doc.new_page(width=cropped_page.width, height=cropped_page.height)
                new_page.show_pdf_page(new_page.rect, self.doc, page_number, clip=cropped_page)

                output_file = os.path.join(output_dir, f"Page_{page_number+1}_Crop_{i+1}.pdf")
                new_doc.save(output_file)
                new_doc.close()

        return "Cropped PDFs saved successfully!Success", "Cropped PDFs saved!")