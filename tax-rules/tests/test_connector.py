"""Tests for the main connector."""

import pytest
from unittest.mock import Mock, patch
from datetime import date

from tax_rules_connector.connector import TaxRulesConnector


class TestTaxRulesConnector:
    """Test cases for TaxRulesConnector."""
    
    def test_connector_initialization(self):
        """Test connector can be initialized."""
        connector = TaxRulesConnector()
        assert connector is not None
        assert connector.http_client is None
        assert connector.streams == {}
    
    def test_configure_federal(self):
        """Test connector configuration for federal jurisdiction."""
        connector = TaxRulesConnector()
        
        config = {
            'jurisdiction_level': 'federal',
            'jurisdiction_code': 'US',
            'enabled_streams': ['newsroom_releases', 'irb_bulletins'],
            'request_timeout': 30,
            'max_retries': 3
        }
        
        connector.configure(config)
        
        assert connector.configuration == config
        assert connector.http_client is not None
        assert 'newsroom_releases' in connector.streams
        assert 'irb_bulletins' in connector.streams
        assert len(connector.streams) == 2
    
    def test_configure_with_defaults(self):
        """Test connector configuration with default values."""
        connector = TaxRulesConnector()
        
        config = {
            'jurisdiction_level': 'federal',
            'jurisdiction_code': 'US'
        }
        
        connector.configure(config)
        
        # Should have all default streams
        assert len(connector.streams) == 5
        assert 'newsroom_releases' in connector.streams
        assert 'revproc_items' in connector.streams
        assert 'irb_bulletins' in connector.streams
        assert 'draft_forms' in connector.streams
        assert 'mef_summaries' in connector.streams
    
    def test_schema_generation(self):
        """Test schema generation."""
        connector = TaxRulesConnector()
        
        config = {
            'jurisdiction_level': 'federal',
            'jurisdiction_code': 'US',
            'enabled_streams': ['newsroom_releases']
        }
        
        schema = connector.schema(config)
        
        assert 'streams' in schema
        assert 'newsroom_releases' in schema['streams']
        assert 'columns' in schema['streams']['newsroom_releases']
        assert 'primary_key' in schema['streams']['newsroom_releases']
    
    @patch('tax_rules_connector.http_client.IRSHttpClient.test_connection')
    def test_connection_test(self, mock_test):
        """Test connection testing."""
        mock_test.return_value = True
        
        connector = TaxRulesConnector()
        
        config = {
            'jurisdiction_level': 'federal',
            'jurisdiction_code': 'US',
            'enabled_streams': ['newsroom_releases']
        }
        
        # Should not raise exception
        connector.test(config)
        
        # Test failure case
        mock_test.return_value = False
        
        with pytest.raises(Exception):
            connector.test(config)
    
    def test_sync_with_state(self):
        """Test sync operation with state."""
        connector = TaxRulesConnector()
        
        config = {
            'jurisdiction_level': 'federal',
            'jurisdiction_code': 'US',
            'enabled_streams': ['newsroom_releases']
        }
        
        state = {
            'newsroom_releases': {
                'cursor': '2024-01-01'
            }
        }
        
        # Mock the stream sync method
        with patch.object(connector, 'configure'):
            with patch.object(connector, 'streams', {'newsroom_releases': Mock()}):
                mock_stream = connector.streams['newsroom_releases']
                mock_stream.sync.return_value = iter([])
                mock_stream.get_cursor.return_value = '2024-01-02'
                
                operations = list(connector.sync(config, state))
                
                # Should call sync with cursor
                mock_stream.sync.assert_called_once_with('2024-01-01')
                mock_stream.get_cursor.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])
