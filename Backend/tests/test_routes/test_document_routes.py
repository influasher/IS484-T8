import unittest
import json
import io
import sys
import os
from unittest.mock import patch, MagicMock

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, backend_dir)

from tests.test_config import BaseTestCase

try:
    from models.document import Document
except ImportError:
    Document = None

class DocumentRoutesTestCase(BaseTestCase):
    """Test cases for document routes."""
    
    def setUp(self):
        super().setUp()
        if not Document:
            self.skipTest("Document model not available")
        self.user = self.create_test_user()
        self.auth_headers = self.get_auth_headers()
    
    @patch('services.document_service.DocumentService.process_document')
    def test_upload_document_success(self, mock_process):
        """Test successful document upload."""
        mock_process.return_value = {'document_id': 1, 'message': 'Document uploaded successfully'}
        
        data = {
            'file': (io.BytesIO(b"fake pdf content"), 'test.pdf'),
            'title': 'Test Document'
        }
        
        response = self.client.post('/api/documents/upload',
                                  data=data,
                                  headers=self.auth_headers,
                                  content_type='multipart/form-data')
        
        self.assertResponseSuccess(response)
        response_data = self.get_json_response(response)
        self.assertIn('document_id', response_data)
    
    def test_upload_document_no_file(self):
        """Test document upload without file."""
        response = self.client.post('/api/documents/upload',
                                  data={'title': 'Test Document'},
                                  headers=self.auth_headers,
                                  content_type='multipart/form-data')
        
        self.assertResponseError(response, 400)
    
    def test_upload_document_invalid_file_type(self):
        """Test document upload with invalid file type."""
        data = {
            'file': (io.BytesIO(b"fake content"), 'test.exe'),
            'title': 'Test Document'
        }
        
        response = self.client.post('/api/documents/upload',
                                  data=data,
                                  headers=self.auth_headers,
                                  content_type='multipart/form-data')
        
        self.assertResponseError(response, 400)
    
    def test_get_user_documents(self):
        """Test retrieving user documents."""
        # Create test documents
        doc1 = self.create_test_document(self.user.id, "Document 1")
        doc2 = self.create_test_document(self.user.id, "Document 2")
        
        response = self.client.get('/api/documents', headers=self.auth_headers)
        
        self.assertResponseSuccess(response)
        data = self.get_json_response(response)
        self.assertIn('documents', data)
        self.assertEqual(len(data['documents']), 2)
    
    def test_get_document_by_id(self):
        """Test retrieving specific document."""
        document = self.create_test_document(self.user.id)
        
        response = self.client.get(f'/api/documents/{document.id}', 
                                 headers=self.auth_headers)
        
        self.assertResponseSuccess(response)
        data = self.get_json_response(response)
        self.assertEqual(data['id'], document.id)
        self.assertEqual(data['title'], document.title)
    
    def test_get_nonexistent_document(self):
        """Test retrieving non-existent document."""
        response = self.client.get('/api/documents/99999', 
                                 headers=self.auth_headers)
        
        self.assertResponseError(response, 404)
    
    def test_update_document(self):
        """Test updating document."""
        document = self.create_test_document(self.user.id)
        
        response = self.client.put(f'/api/documents/{document.id}',
                                 json={'title': 'Updated Document Title'},
                                 headers=self.auth_headers)
        
        self.assertResponseSuccess(response)
        
        # Verify update in database
        updated_doc = Document.query.get(document.id)
        self.assertEqual(updated_doc.title, 'Updated Document Title')
    
    def test_delete_document(self):
        """Test deleting document."""
        document = self.create_test_document(self.user.id)
        
        response = self.client.delete(f'/api/documents/{document.id}',
                                    headers=self.auth_headers)
        
        self.assertResponseSuccess(response)
        
        # Verify deletion in database
        deleted_doc = Document.query.get(document.id)
        self.assertIsNone(deleted_doc)
    
    def test_access_other_user_document(self):
        """Test accessing another user's document."""
        other_user = self.create_test_user('other@example.com', 'other_user')  # Fixed spelling
        document = self.create_test_document(other_user.id)
        
        response = self.client.get(f'/api/documents/{document.id}',
                                 headers=self.auth_headers)
        
        self.assertResponseError(response, 403)

if __name__ == '__main__':
    unittest.main()
