import fitz  # PyMuPDF

class QuestionAnalyzer:

    def extract_text_from_pdf_file(self ,file_obj):
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