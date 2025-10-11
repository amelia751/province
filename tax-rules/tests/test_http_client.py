"""Tests for HTTP client."""

import pytest
from unittest.mock import Mock, patch
import requests

from tax_rules_connector.http_client import IRSHttpClient


class TestIRSHttpClient:
    """Test cases for IRSHttpClient."""
    
    def test_client_initialization(self):
        """Test client can be initialized."""
        client = IRSHttpClient()
        assert client.timeout == 30
        assert client.max_retries == 3
        assert client.session is not None
    
    def test_client_custom_config(self):
        """Test client with custom configuration."""
        client = IRSHttpClient(timeout=60, max_retries=5)
        assert client.timeout == 60
        assert client.max_retries == 5
    
    @patch('requests.Session.get')
    def test_successful_get_request(self, mock_get):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html>Test</html>'
        mock_get.return_value = mock_response
        
        client = IRSHttpClient()
        response = client.get('https://www.irs.gov/test')
        
        assert response == mock_response
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_failed_get_request(self, mock_get):
        """Test failed GET request."""
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        client = IRSHttpClient()
        
        with pytest.raises(requests.RequestException):
            client.get('https://www.irs.gov/test')
    
    @patch('requests.Session.get')
    def test_get_soup(self, mock_get):
        """Test getting BeautifulSoup object."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><title>Test</title></html>'
        mock_get.return_value = mock_response
        
        client = IRSHttpClient()
        soup = client.get_soup('https://www.irs.gov/test')
        
        assert soup.title.string == 'Test'
    
    @patch('requests.Session.head')
    def test_get_pdf_metadata(self, mock_head):
        """Test getting PDF metadata."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'content-type': 'application/pdf',
            'content-length': '12345',
            'last-modified': 'Wed, 01 Jan 2024 12:00:00 GMT'
        }
        mock_head.return_value = mock_response
        
        client = IRSHttpClient()
        metadata = client.get_pdf_metadata('https://www.irs.gov/test.pdf')
        
        assert metadata['content_type'] == 'application/pdf'
        assert metadata['content_length'] == '12345'
        assert metadata['last_modified'] == 'Wed, 01 Jan 2024 12:00:00 GMT'
    
    def test_is_valid_irs_url(self):
        """Test IRS URL validation."""
        client = IRSHttpClient()
        
        assert client.is_valid_irs_url('https://www.irs.gov/newsroom')
        assert client.is_valid_irs_url('https://irs.gov/forms')
        assert not client.is_valid_irs_url('https://www.example.com')
        assert not client.is_valid_irs_url('https://fake-irs.gov')
    
    def test_resolve_relative_url(self):
        """Test relative URL resolution."""
        client = IRSHttpClient()
        
        base = 'https://www.irs.gov/newsroom'
        relative = '/forms/form-1040'
        
        resolved = client.resolve_relative_url(base, relative)
        assert resolved == 'https://www.irs.gov/forms/form-1040'
    
    def test_calculate_content_hash(self):
        """Test content hash calculation."""
        client = IRSHttpClient()
        
        content = b'test content'
        hash_value = client.calculate_content_hash(content)
        
        # Should be consistent
        assert hash_value == client.calculate_content_hash(content)
        assert len(hash_value) == 64  # SHA256 hex length
    
    @patch('requests.Session.get')
    def test_connection_test(self, mock_get):
        """Test connection testing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = IRSHttpClient()
        assert client.test_connection('https://www.irs.gov')
        
        # Test failure
        mock_get.side_effect = requests.RequestException("Failed")
        assert not client.test_connection('https://www.irs.gov')


if __name__ == '__main__':
    pytest.main([__file__])
