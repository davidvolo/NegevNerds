from PyPDF2 import PdfReader
import re
import os

class Course_syllabus:
    def __init__(self):
        pass

    def extract_syllabus_topic_total(self, pdf_path):
        """
        Extract syllabus topics from the PDF using multiple patterns and strategies.
        """
        # Check if the file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The file at {pdf_path} does not exist.")

        # Check if the file is a valid PDF
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError(f"The file at {pdf_path} is not a valid PDF.")
        
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
        table_patterns = [
            r"נושאי השיעור",  # Hebrew pattern for "Course Topics"
            r"סילבוס",        # Hebrew pattern for "Syllabus"
            r"Topics",         # English pattern for "Topics"
            r"Outline",        # English pattern for "Outline"
        ]

        topics = set()

        # Attempt to extract using multiple strategies
        topics = self.extract_syllabus_topics4(pdf_path, topic_patterns)

        if not topics:
            topics = self.extract_syllabus_topics4(pdf_path, topic_patterns1)

        # if not topics:
        #     topics = self.extract_syllabus_topic9(self.pdf_path)
        cleaned_topics = {topic.lstrip("• ").strip() for topic in topics}

        return cleaned_topics

    @staticmethod
    def extract_syllabus_topics4(file_path, topic_patterns):
        """
        Extracts syllabus topics from a course PDF file and returns them as a set.
        Handles diverse formats such as tables, bullet points, numbered sections, and headers.

        :param file_path: Path to the PDF file
        :param topic_patterns: List of regex patterns to identify syllabus-related sections
        :return: A set of topics from the syllabus
        """
        reader = PdfReader(file_path)
        syllabus_topics = set()

        for page in reader.pages:
            text = page.extract_text()

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

        return syllabus_topics

    @staticmethod
    def extract_syllabus_topic9(file_path):
        """
        Fallback method to extract syllabus topics from a PDF when other methods fail.
        """
        reader = PdfReader(file_path)
        syllabus_topics = set()

        for page in reader.pages:
            text = page.extract_text()
            lines = text.split("\n")
            for line in lines:
                if any(keyword in line for keyword in ["סילבוס", "נושאי השיעור", "Topics", "Outline"]):
                    syllabus_topics.add(line.strip())

        return syllabus_topics
