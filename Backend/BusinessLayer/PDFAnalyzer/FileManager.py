import os


class FileManager:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        os.makedirs(self.upload_folder, exist_ok=True)

    def save_file_question(self, file_content, course_name, year, semester, moed, question_number):
        """
        Save a file with a custom name based on course details and question number.

        :param file_content: Content of the file to save.
        :param course_name: Name of the course.
        :param year: Year of the exam.
        :param semester: Semester of the exam.
        :param moed: Moed of the exam.
        :param question_number: Question number.
        :return: Path to the saved file.
        """
        filename = f"{course_name}_{year}_{semester}_{moed}_Q{question_number}.pdf"
        filename = filename.replace(" ", "_")

        # Define the full path
        file_path = os.path.join(self.upload_folder, filename)

        # Ensure the upload folder exists
        os.makedirs(self.upload_folder, exist_ok=True)

        # Save the file
        with open(file_path, 'wb') as f:
            f.write(file_content)

        return file_path
