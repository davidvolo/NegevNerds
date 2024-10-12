from tika import parser
from collections import Counter
import re

def extract_pdf_info(pdf_file_path):
    # Parse the PDF file
    parsed = parser.from_file(pdf_file_path)
    
    # Extract metadata
    metadata = parsed.get('metadata', {})
    
    # Extract text
    text = parsed.get('content', '')
    
    return metadata, text

def count_words(text):
    # Normalize the text to lower case and remove punctuation
    words = re.findall(r'\b\w+\b', text.lower())
    # Count occurrences of each word
    word_count = Counter(words)
    return dict(sorted(word_count.items()))  # Sort dictionary by key (word)

def extract_exam_details(text):
    # Regular expressions to find course, year, semester, and Moed
    course_match = re.search(r'שם הקורס:\s*(.+)', text)
    year_match = re.search(r'שנה:\s*(\d{4})', text)
    semester_match = re.search(r'סמסטר:\s*([AB])', text)
    moed_match = re.search(r'מועד:\s*([abc])', text)
    
    # Extract details if matches found, otherwise use None
    course = course_match.group(1).strip() if course_match else None
    year = year_match.group(1).strip() if year_match else None
    semester = semester_match.group(1).strip() if semester_match else None
    moed = moed_match.group(1).strip() if moed_match else None
    
    return (course, year, semester, moed)

def main():
    pdf_file_path = "/Users/davidvolodarsky/Desktop/NegevNerds/os_2022_B_moedA.pdf"  # Replace with your PDF file path
    
    metadata, text = extract_pdf_info(pdf_file_path)
    
    print("Metadata:")
    for key, value in metadata.items():
        print(f"{key}: {value}")
    
    print("\nExtracted Text:")
    print(text)
    
    # Count and sort words
    word_count = count_words(text)
    print("\nWord Count (Sorted):")
    for word, count in word_count.items():
        print(f"{word}: {count}")

    # Extract exam details
    exam_details = extract_exam_details(text)
    print("\nExam Details (Course, Year, Semester, Moed):")
    print(exam_details)

if __name__ == "__main__":
    main()
