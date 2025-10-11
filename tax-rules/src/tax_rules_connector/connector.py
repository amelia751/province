"""Main connector implementation for IRS Tax Rules."""

import logging
from typing import Dict, Any, Iterator, Optional
from datetime import datetime, date

from fivetran_connector_sdk import Connector, Operations

from .streams import (
    NewsroomReleasesStream,
    RevProcItemsStream,
    IRBBulletinsStream,
    DraftFormsStream,
    MeFSummariesStream
)
from .http_client import IRSHttpClient

logger = logging.getLogger(__name__)


class TaxRulesConnector(Connector):
    """Fivetran connector for IRS tax rules and regulations."""
    
    def __init__(self):
        # Fivetran SDK requires an update function
        super().__init__(update=self._update)
        self.http_client: Optional[IRSHttpClient] = None
        self.streams = {}
    
    def _update(self, configuration: Dict[str, Any], state: Dict[str, Any]) -> Iterator[Operations]:
        """Update method required by Fivetran SDK - delegates to sync."""
        return self.sync(configuration, state)
    
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
    
    def schema(self, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Return the schema for all streams."""
        self.configure(configuration)
        
        schema = {
            "streams": {}
        }
        
        for stream_name, stream in self.streams.items():
            schema["streams"][stream_name] = stream.get_schema()
        
        return schema
    
    def test(self, configuration: Dict[str, Any]) -> None:
        """Test the connector configuration."""
        self.configure(configuration)
        
        logger.info("Testing connector configuration...")
        
        # Test HTTP client
        if not self.http_client:
            raise Exception("HTTP client not initialized")
        
        # Test each enabled stream
        for stream_name, stream in self.streams.items():
            try:
                logger.info(f"Testing stream: {stream_name}")
                result = stream.test_connection()
                if not result:
                    raise Exception(f"Stream {stream_name} connection test returned False")
                logger.info(f"Stream {stream_name} test passed")
            except Exception as e:
                logger.error(f"Stream {stream_name} test failed: {e}")
                raise Exception(f"Stream {stream_name} test failed: {e}")
        
        logger.info("All tests passed")
    
    def sync(self, configuration: Dict[str, Any], state: Dict[str, Any]) -> Iterator[Operations]:
        """Sync data from all enabled streams."""
        self.configure(configuration)
        
        logger.info("Starting sync operation...")
        
        for stream_name, stream in self.streams.items():
            logger.info(f"Syncing stream: {stream_name}")
            
            try:
                # Get cursor from state
                stream_state = state.get(stream_name, {})
                cursor = stream_state.get('cursor')
                
                # Sync the stream
                for operation in stream.sync(cursor):
                    yield operation
                
                # Update state with new cursor
                new_cursor = stream.get_cursor()
                if new_cursor:
                    state[stream_name] = {'cursor': new_cursor}
                    yield Operations.checkpoint(state)
                
                logger.info(f"Completed sync for stream: {stream_name}")
                
            except Exception as e:
                logger.error(f"Error syncing stream {stream_name}: {e}")
                raise
        
        logger.info("Sync operation completed")


def main():
    """Main entry point for the connector."""
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    connector = TaxRulesConnector()
    connector.main()


if __name__ == "__main__":
    main()
