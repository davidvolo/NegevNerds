from PyPDF2 import PdfReader
import re
import os
import pdfplumber
from tabula import read_pdf
import pandas as pd

class Course_syllabus:
    def __init__(self):
        pass

    def extract_syllabus_topic_total(self, pdf_path):
        topic_patterns = [
        r'סילבוס[:\n](.*?)\n',  # Hebrew pattern for "Syllabus"
        r'סילבוס באנגלית[:\n](.*?)\n',
        r'סילבוס בעברית[:\n](.*?)\n',
    ]
        topic_patterns1 = [
        r'נושאים[:\n](.*?)\n',  # Hebrew pattern for "Topics"
        r'Course Topics[:\n](.*?)\n',
        r'Outline[:\n](.*?)\n',
    ]
        
        topics_table = ["נושאי השיעור", "נושא השיעור","Topics", "Outline"]  # List of column headers to search for

        topics = set()
        has_table = self.has_valid_table_with_pdfplumber(pdf_path)
        if not has_table:
            topics = self.extract_syllabus_topics_with_pdfplumber(pdf_path,topic_patterns)
            if len(topics)==0:
                topics = self.extract_syllabus_topics_with_pdfplumber(pdf_path,topic_patterns1)
        else:
            topics = self.extract_table_with_topics_final(pdf_path,topics_table )
        cleaned_topics = set()
        for topic in topics:
            # Remove leading numbers (e.g., "1.", "2. ", etc.)
            topic = re.sub(r"^\d+\.\s*", "", topic)
            # Remove leading special characters like "•", "*", etc.
            topic = topic.lstrip("•* ").strip()
            if topic:  # Only keep non-empty topics
                cleaned_topics.add(topic)
        

        return cleaned_topics


    
    def has_valid_table_with_pdfplumber(self, pdf_path, min_rows=2, min_columns=2):
        """
        Checks if a PDF contains at least one valid table using pdfplumber.

        :param pdf_path: Path to the PDF file
        :param min_rows: Minimum number of rows to validate a table
        :param min_columns: Minimum number of columns to validate a table
        :return: True if at least one valid table is found, False otherwise
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()  # Extract tables from the page
                    if tables:
                        for table in tables:
                            # Validate table structure
                            if len(table) >= min_rows and len(table[0]) >= min_columns:
                                return True
            return False
        except Exception as e:

            return False


  

    def extract_syllabus_topics_with_pdfplumber(self, file_path, topic_patterns):
        """
        Extracts syllabus topics from a course PDF file using pdfplumber and returns them as a set.
        Handles diverse formats such as tables, bullet points, numbered sections, and headers.

        :param file_path: Path to the PDF file
        :param topic_patterns: List of regex patterns to identify syllabus-related sections
        :return: A set of topics from the syllabus
        """
        syllabus_topics = set()
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        # Match topics using provided patterns
                        for pattern in topic_patterns:
                            matches = re.findall(pattern, text, re.DOTALL)
                            for match in matches:
                                # Split potential topics by common delimiters and clean up
                                topics = re.split(r',|;|\n|\•|\.', match)
                                syllabus_topics.update([topic.strip() for topic in topics if topic.strip()])

                        # Handle bullet points
                        lines = text.split("\n")
                        for line in lines:
                            if re.match(r'^\•', line):  # Matches lines starting with "•"
                                syllabus_topics.add(line.lstrip("• ").strip())

                        # Handle numbered sections (e.g., "1. Topic", "2. Topic")
                        for line in lines:
                            if re.match(r'^\d+\.\s', line):  # Matches lines starting with "1. ", "2. ", etc.
                                syllabus_topics.add(line.strip())

                        # Handle keywords directly in the text
                        if any(keyword in text for keyword in ["סילבוס", "Topics", "Outline"]):
                            for line in lines:
                                # Add lines containing relevant keywords as potential topics
                                if any(keyword in line for keyword in ["סילבוס", "Topics", "Outline"]):
                                    syllabus_topics.add(line.strip())
        except Exception as e:
            print(f"Error processing PDF with pdfplumber: {e}")

        return syllabus_topics


    
    
    def extract_table_with_topics_final(self,pdf_path, topics, pages="all"):
        """
        Extracts tables from a PDF, matches column titles to a list of topics,
        and returns data under matching columns.

        :param pdf_path: Path to the PDF file
        :param topics: List of column titles to match
        :param pages: Pages to extract tables from (default: "all")
        :return: Set of data under matching columns
        """
        matching_data = set()

        try:
            # Extract tables using Tabula
            tables = read_pdf(pdf_path, pages=pages, multiple_tables=True, pandas_options={"header": None})

            if not tables:
                return matching_data

            for i, table in enumerate(tables):

                # Assume the first row is the header
                df = pd.DataFrame(table)
                headers = df.iloc[0]
                df.columns = headers
                df = df[1:]  # Remove the header row

                # Clean up headers for matching
                df.columns = df.columns.str.strip()


                # Check for matching columns
                for column in df.columns:
                    if any(topic in column for topic in topics):
                        matching_data.update(df[column].dropna().tolist())

        except Exception as e:
            print(f"Error during table extraction: {e}")

        return matching_data