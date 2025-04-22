import io
from collections import defaultdict

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from werkzeug.datastructures import FileStorage


class QuestionAnalyzer:
    import fitz  # PyMuPDF
    import io
    from collections import defaultdict

    def splitPDF(self, pdf_file, lines):
        PDF_RENDERED_WIDTH = 900  # Same as your frontend canvas width
        print(lines)

        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        result_files = []

        # Sort lines by page and position
        sorted_lines = sorted(lines, key=lambda x: (x['page'], x['y']))

        # Convert frontend coordinates to PDF coordinates
        pdf_lines = []
        for line in sorted_lines:
            page_number = line['page'] - 1  # 0-based index
            frontend_y = line['y']

            page = doc[page_number]
            page_width = page.rect.width

            # Calculate scale ratio
            scale_ratio = page_width / PDF_RENDERED_WIDTH

            # Convert y coordinate
            pdf_y = frontend_y * scale_ratio
            pdf_lines.append({
                'page': page_number,
                'y': pdf_y
            })

        # Process each pair of lines as a question boundary
        for i in range(len(pdf_lines) - 1):
            start_line = pdf_lines[i]
            end_line = pdf_lines[i + 1]

            start_page = start_line['page']
            start_y = start_line['y']

            # Create a new document for this question
            new_doc = fitz.open()

            if end_line['page'] > start_page:
                # This question extends to the next page or is the last question
                # First, add content from the start page
                page = doc[start_page]
                page_width = page.rect.width
                page_height = page.rect.height

                # From start_y to bottom of page
                clip = fitz.Rect(0, start_y, page_width, page_height)
                new_page = new_doc.new_page(width=page_width, height=page_height - start_y)
                new_page.show_pdf_page(new_page.rect, doc, start_page, clip=clip)

                # If there's an end line and it's on a different page
                if end_line and end_line['page'] > start_page:
                    # Add any middle pages completely
                    for page_num in range(start_page + 1, end_line['page']):
                        mid_page = doc[page_num]
                        mid_width = mid_page.rect.width
                        mid_height = mid_page.rect.height
                        new_mid_page = new_doc.new_page(width=mid_width, height=mid_height)
                        new_mid_page.show_pdf_page(new_mid_page.rect, doc, page_num)

                    # Add the end page from top to end_y
                    end_page = doc[end_line['page']]
                    end_width = end_page.rect.width
                    end_y = end_line['y']
                    clip = fitz.Rect(0, 0, end_width, end_y)
                    new_end_page = new_doc.new_page(width=end_width, height=end_y)
                    new_end_page.show_pdf_page(new_end_page.rect, doc, end_line['page'], clip=clip)
            else:
                # Question is contained within the same page
                page = doc[start_page]
                page_width = page.rect.width
                end_y = end_line['y']

                clip = fitz.Rect(0, start_y, page_width, end_y)
                new_page = new_doc.new_page(width=page_width, height=end_y - start_y)
                new_page.show_pdf_page(new_page.rect, doc, start_page, clip=clip)

            # Save the new document
            pdf_bytes = new_doc.write()
            pdf_io = io.BytesIO(pdf_bytes)
            file_storage = FileStorage(pdf_io, filename=f"question_{i + 1}.pdf")
            result_files.append(file_storage)

            new_doc.close()

        doc.close()
        return result_files


    # def splitPDF(self, pdf_file, lines):
    #     PDF_RENDERED_WIDTH = 900  # Same as your frontend canvas width
    #     print(lines)
    #
    #     doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    #     result_files = []
    #
    #     # Group lines by page
    #     page_lines = defaultdict(list)
    #     for line in lines:
    #         page_number = line['page'] - 1  # 0-based index
    #         frontend_y = line['y']  # y in 900px canvas
    #
    #         page = doc[page_number]
    #         page_width = page.rect.width
    #         # page_height = page.rect.height
    #
    #         # Calculate scale ratio based on frontend render width
    #         scale_ratio = page_width / PDF_RENDERED_WIDTH
    #
    #         # Convert frontend y to PDF coordinate system
    #         pdf_y = frontend_y * scale_ratio
    #         page_lines[page_number].append(pdf_y)
    #
    #     for page_number, crop_list in page_lines.items():
    #         if not crop_list:
    #             continue
    #
    #         crop_list.sort()
    #         page = doc[page_number]
    #         page_height = page.rect.height
    #         page_width = page.rect.width
    #
    #         for i, start_y in enumerate(crop_list):
    #             end_y = crop_list[i + 1] if i + 1 < len(crop_list) else page_height
    #             print("start_y", start_y)
    #             print("end_y", end_y)
    #             print("page_height", page_height)
    #
    #             if start_y >= end_y:
    #                 continue
    #
    #             # Define crop rectangle (x0, y0, x1, y1)
    #             clip = fitz.Rect(0, start_y, page_width, end_y)
    #
    #             # Create new PDF with cropped content
    #             new_doc = fitz.open()
    #             new_page = new_doc.new_page(width=clip.width, height=clip.height)
    #             new_page.show_pdf_page(new_page.rect, doc, page_number, clip=clip)
    #
    #             # Save to memory
    #             pdf_bytes = new_doc.write()
    #
    #             # Convert the byte data to FileStorage object
    #             pdf_io = io.BytesIO(pdf_bytes)
    #             file_storage = FileStorage(pdf_io, filename="cropped_question.pdf")
    #             result_files.append(file_storage)
    #
    #             new_doc.close()
    #
    #     doc.close()
    #     return result_files

    def extract_text_from_pdf_file(self,file_obj):
        try:
            # Open the PDF from the file-like object
            document = fitz.open(stream=file_obj.read(), filetype="pdf")
            text = ""
            for page in document:
                text += page.get_text()
            document.close()
            return text
        except Exception as e:
            return f"An error occurred: {e}"

    def extract_text_from_image(self,  image_file):
        """
        Extracts text from an image using Tesseract OCR for Hebrew and English.

        :param image_path: Path to the image file
        :return: Extracted text as a string
        """
        try:
            # Open the image
            image = Image.open(image_file)

            # Perform OCR using Tesseract with Hebrew and English
            text = pytesseract.image_to_string(image, lang="heb+eng")
            # print(text)
            return text

        except Exception as e:
            print(f"Error occurred: {e}")
            return None





# if __name__ == "__main__":
#     image_path = "../../../photo2.jpg"  # Replace with your image path
#     extracted_text = extract_text_from_image(image_path)
#     print("Extracted Text:\n" , extracted_text)