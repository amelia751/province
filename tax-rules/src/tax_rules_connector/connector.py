"""Direct IRS Tax Rules connector - no Fivetran dependencies."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import json

from .streams import (
    NewsroomReleasesStream,
    RevProcItemsStream,
    IRBBulletinsStream,
    DraftFormsStream,
    MeFSummariesStream
)
from .http_client import IRSHttpClient

logger = logging.getLogger(__name__)


class TaxRulesConnector:
    """Direct connector for IRS tax rules and regulations."""
    
    def __init__(self):
        self.http_client: Optional[IRSHttpClient] = None
        self.streams = {}
        self.configuration = {}
    
    def configure(self, configuration: Dict[str, Any]) -> None:
        """Configure the connector with user settings."""
        self.configuration = configuration
        
        # Initialize HTTP client
        self.http_client = IRSHttpClient(
            timeout=configuration.get('request_timeout', 30),
            max_retries=configuration.get('max_retries', 3)
        )
        
        # Initialize enabled streams
        enabled_streams = configuration.get('enabled_streams', [
            'newsroom_releases', 'revproc_items', 'irb_bulletins', 
            'draft_forms', 'mef_summaries'
        ])
        
        base_urls = configuration.get('base_urls', {})
        jurisdiction_level = configuration.get('jurisdiction_level', 'federal')
        jurisdiction_code = configuration.get('jurisdiction_code', 'US')
        
        self.streams = {}
        
        if 'newsroom_releases' in enabled_streams:
            self.streams['newsroom_releases'] = NewsroomReleasesStream(
                self.http_client, 
                base_urls.get('newsroom', 'https://www.irs.gov/newsroom'),
                jurisdiction_level,
                jurisdiction_code
            )
        
        if 'revproc_items' in enabled_streams:
            self.streams['revproc_items'] = RevProcItemsStream(
                self.http_client,
                jurisdiction_level,
                jurisdiction_code
            )
        
        if 'irb_bulletins' in enabled_streams:
            self.streams['irb_bulletins'] = IRBBulletinsStream(
                self.http_client,
                base_urls.get('irb', 'https://www.irs.gov/irb'),
                jurisdiction_level,
                jurisdiction_code
            )
        
        if 'draft_forms' in enabled_streams:
            self.streams['draft_forms'] = DraftFormsStream(
                self.http_client,
                base_urls.get('draft_forms', 'https://www.irs.gov/forms-pubs/draft-tax-forms'),
                jurisdiction_level,
                jurisdiction_code
            )
        
        if 'mef_summaries' in enabled_streams:
            self.streams['mef_summaries'] = MeFSummariesStream(
                self.http_client,
                base_urls.get('mef', 'https://www.irs.gov/modernized-e-file-mf-business-rules-and-schemas'),
                jurisdiction_level,
                jurisdiction_code
            )
        
        logger.info(f"Configured connector with {len(self.streams)} streams for {jurisdiction_level} {jurisdiction_code}")
    
    def test(self, configuration: Dict[str, Any]) -> bool:
        """Test the connector configuration."""
        try:
            self.configure(configuration)
            
            logger.info("Testing connector configuration...")
            
            # Test HTTP client
            if not self.http_client:
                raise Exception("HTTP client not initialized")
            
            # Test each enabled stream
            for stream_name, stream in self.streams.items():
                logger.info(f"Testing stream: {stream_name}")
                result = stream.test_connection()
                if not result:
                    raise Exception(f"Stream {stream_name} connection test returned False")
                logger.info(f"✅ Stream {stream_name} test passed")
            
            logger.info("✅ All tests passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False
    
    def extract_data(self, configuration: Dict[str, Any], limit_per_stream: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Extract data from all enabled streams."""
        self.configure(configuration)
        
        logger.info("Starting data extraction...")
        
        all_data = {}
        
        for stream_name, stream in self.streams.items():
            logger.info(f"Extracting from stream: {stream_name}")
            
            try:
                # Extract data from stream
                data = []
                count = 0
                
                for record in stream.read_records():
                    data.append(record)
                    count += 1
                    if count >= limit_per_stream:
                        break
                
                all_data[stream_name] = data
                logger.info(f"✅ Extracted {len(data)} records from {stream_name}")
                
            except Exception as e:
                logger.error(f"❌ Error extracting from stream {stream_name}: {e}")
                all_data[stream_name] = []
        
        logger.info(f"✅ Data extraction completed. Total streams: {len(all_data)}")
        return all_data


def get_default_configuration() -> Dict[str, Any]:
    """Get default configuration for the connector."""
    return {
        'jurisdiction_level': 'federal',
        'jurisdiction_code': 'US',
        'enabled_streams': ['newsroom_releases', 'irb_bulletins'],  # Start with working streams
        'base_urls': {
            'newsroom': 'https://www.irs.gov/newsroom',
            'irb': 'https://www.irs.gov/irb',
            'draft_forms': 'https://www.irs.gov/forms-pubs/draft-tax-forms',
            'mef': 'https://www.irs.gov/modernized-e-file-mf-business-rules-and-schemas'
        },
        'request_timeout': 30,
        'max_retries': 3
    }


def main():
    """Main entry point for testing the connector."""
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the connector
    connector = TaxRulesConnector()
    config = get_default_configuration()
    
    # Test connection
    if connector.test(config):
        print("🎉 Connector test successful!")
        
        # Extract sample data
        data = connector.extract_data(config, limit_per_stream=5)
        
        print(f"\n📊 Sample data extracted:")
        for stream_name, records in data.items():
            print(f"  {stream_name}: {len(records)} records")
            if records:
                print(f"    Sample: {list(records[0].keys())}")
    else:
        print("❌ Connector test failed!")


if __name__ == "__main__":
    main()