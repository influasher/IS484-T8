import unittest
import os
import tempfile
import sys
from unittest.mock import patch, MagicMock, mock_open

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, backend_dir)

from tests.test_config import BaseTestCase

try:
    from services.document_service import DocumentService
    from models.document import Document
    from extensions import db
except ImportError:
    DocumentService = None
    Document = None
    db = None

class DocumentServiceTestCase(BaseTestCase):
    """Test cases for document service."""
    
    def setUp(self):
        super().setUp()
        if not DocumentService:
            self.skipTest("DocumentService not available")
        self.service = DocumentService()
        self.user = self.create_test_user()
    
    def test_validate_file_type_valid(self):
        """Test file type validation for valid files."""
        valid_files = ['document.pdf', 'text.txt', 'word.docx']
        
        for filename in valid_files:
            result = self.service.validate_file_type(filename)
            self.assertTrue(result)
    
    def test_validate_file_type_invalid(self):
        """Test file type validation for invalid files."""
        invalid_files = ['script.exe', 'image.jpg', 'music.mp3']
        
        for filename in invalid_files:
            result = self.service.validate_file_type(filename)
            self.assertFalse(result)
    
    @patch('services.document_service.secure_filename')
    @patch('os.makedirs')
    def test_save_uploaded_file(self, mock_makedirs, mock_secure_filename):
        """Test saving uploaded file to filesystem."""
        mock_secure_filename.return_value = 'safe_filename.pdf'
        
        mock_file = MagicMock()
        mock_file.filename = 'test document.pdf'
        
        with patch('builtins.open', mock_open()) as mock_file_open:
            result = self.service.save_uploaded_file(mock_file, self.user.id)
            
            self.assertIsNotNone(result)
            self.assertIn('filename', result)
            self.assertIn('file_path', result)
            self.assertIn('file_size', result)
            mock_file.save.assert_called_once()
    
    @patch('PyPDF2.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader):
        """Test PDF text extraction."""
        # Mock PDF reader and pages
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader
        
        with patch('builtins.open', mock_open()):
            result = self.service.extract_text_from_pdf('/fake/path/test.pdf')
            
            expected_text = "Page 1 content\nPage 2 content"
            self.assertEqual(result, expected_text)
    
    def test_extract_text_from_txt(self):
        """Test text extraction from TXT file."""
        file_content = "This is a sample text file content."
        
        with patch('builtins.open', mock_open(read_data=file_content)):
            result = self.service.extract_text_from_txt('/fake/path/test.txt')
            self.assertEqual(result, file_content)
    
    @patch('docx.Document')
    def test_extract_text_from_docx(self, mock_docx):
        """Test text extraction from DOCX file."""
        # Mock document with paragraphs
        mock_paragraph1 = MagicMock()
        mock_paragraph1.text = "First paragraph"
        mock_paragraph2 = MagicMock()
        mock_paragraph2.text = "Second paragraph"
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
        mock_docx.return_value = mock_doc
        
        result = self.service.extract_text_from_docx('/fake/path/test.docx')
        
        expected_text = "First paragraph\nSecond paragraph"
        self.assertEqual(result, expected_text)
    
    def test_create_document_record(self):
        """Test creating document database record."""
        document_data = {
            'title': 'Test Document',
            'filename': 'test.pdf',
            'file_path': '/path/to/test.pdf',
            'file_size': 1024,
            'content': 'Sample document content'
        }
        
        result = self.service.create_document_record(self.user.id, document_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.title, 'Test Document')
        self.assertEqual(result.user_id, self.user.id)
        
        # Verify document was saved to database
        doc = Document.query.filter_by(title='Test Document').first()
        self.assertIsNotNone(doc)
    
    @patch('services.document_service.DocumentService.extract_text_from_pdf')
    @patch('services.document_service.DocumentService.save_uploaded_file')
    def test_process_document_pdf(self, mock_save, mock_extract):
        """Test complete PDF document processing."""
        mock_save.return_value = {
            'filename': 'test.pdf',
            'file_path': '/path/to/test.pdf',
            'file_size': 1024
        }
        mock_extract.return_value = "Extracted PDF content"
        
        mock_file = MagicMock()
        mock_file.filename = 'test.pdf'
        
        result = self.service.process_document(mock_file, self.user.id, 'Test PDF')
        
        self.assertIsNotNone(result)
        self.assertIn('document_id', result)
        mock_save.assert_called_once()
        mock_extract.assert_called_once()
    
    def test_get_user_documents(self):
        """Test retrieving user's documents."""
        # Create test documents
        doc1 = self.create_test_document(self.user.id, 'Document 1')
        doc2 = self.create_test_document(self.user.id, 'Document 2')
        
        # Create document for different user
        other_user = self.create_test_user('other@example.com', 'other_user')  # Fixed spelling
        doc3 = self.create_test_document(other_user.id, 'Other Document')
        
        result = self.service.get_user_documents(self.user.id)
        
        self.assertEqual(len(result), 2)
        document_titles = [doc.title for doc in result]
        self.assertIn('Document 1', document_titles)
        self.assertIn('Document 2', document_titles)
        self.assertNotIn('Other Document', document_titles)
    
    def test_delete_document_file(self):
        """Test deleting document file from filesystem."""
        with patch('os.path.exists', return_value=True):
            with patch('os.remove') as mock_remove:
                result = self.service.delete_document_file('/path/to/test.pdf')
                
                self.assertTrue(result)
                mock_remove.assert_called_once_with('/path/to/test.pdf')
    
    def test_get_document_stats(self):
        """Test getting document statistics."""
        # Create test documents
        doc1 = self.create_test_document(self.user.id, 'Document 1')
        doc2 = self.create_test_document(self.user.id, 'Document 2')
        
        stats = self.service.get_document_stats(self.user.id)
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_documents', stats)
        self.assertIn('total_size', stats)
        self.assertEqual(stats['total_documents'], 2)

if __name__ == '__main__':
    unittest.main()
