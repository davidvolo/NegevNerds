import os
import unittest
from  Backend.BusinessLayer.PDFAnalyzer.FileManager import FileManager

class TestFileManager(unittest.TestCase):
    def setUp(self):
        """
        Setup for the tests. Create a temporary folder for uploads.
        """
        self.upload_folder = "test_uploads"
        self.file_manager = FileManager(upload_folder=self.upload_folder)
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

    def tearDown(self):
        """
        Cleanup after tests. Remove the temporary upload folder.
        """
        for root, dirs, files in os.walk(self.upload_folder, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        if os.path.exists(self.upload_folder):
            os.rmdir(self.upload_folder)

    def test_save_file_success(self):
        """
        Test saving a file successfully.
        """
        file_content = b"Sample content for the file"
        filename = "example.pdf"
        file_path = self.file_manager.save_file(file_content, filename)

        # Verify the file was saved
        self.assertTrue(os.path.exists(file_path))

        # Verify the content
        with open(file_path, 'rb') as f:
            self.assertEqual(f.read(), file_content)

    def test_save_file_with_invalid_name(self):
        """
        Test saving a file with an invalid name.
        """
        file_content = b"Sample content for the file"
        filename = "invalid/filename.pdf"
        file_path = self.file_manager.save_file(file_content, filename)

        # Verify the file was saved with a sanitized name
        self.assertTrue(os.path.exists(file_path))
        self.assertIn("filename.pdf", file_path)

    def test_save_duplicate_file(self):
        """
        Test saving a duplicate file.
        """
        file_content = b"First file content"
        duplicate_content = b"Duplicate file content"
        filename = "duplicate.pdf"

        # Save the first file
        self.file_manager.save_file(file_content, filename)

        # Save the second file with the same name
        file_path = self.file_manager.save_file(duplicate_content, filename)

        # Verify the content was overwritten
        with open(file_path, 'rb') as f:
            self.assertEqual(f.read(), duplicate_content)

if __name__ == "__main__":
    unittest.main()
