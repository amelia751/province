"""Configuration validation and management for the Tax Rules Connector."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


class TaxRulesConfig:
    """Configuration validator and manager for the Tax Rules Connector."""
    
    # Valid stream names
    VALID_STREAMS = {
        'newsroom_releases',
        'revproc_items', 
        'irb_bulletins',
        'draft_forms',
        'mef_summaries'
    }
    
    # Valid jurisdiction levels
    VALID_JURISDICTION_LEVELS = {'federal', 'state', 'city'}
    
    # Default configuration
    DEFAULT_CONFIG = {
        'jurisdiction_level': 'federal',
        'jurisdiction_code': 'US',
        'enabled_streams': list(VALID_STREAMS),
        'start_date': '2019-01-01',
        'base_urls': {
            'newsroom': 'https://www.irs.gov/newsroom',
            'irb': 'https://www.irs.gov/irb',
            'draft_forms': 'https://www.irs.gov/forms-pubs/draft-tax-forms',
            'mef': 'https://www.irs.gov/modernized-e-file-mf-business-rules-and-schemas'
        },
        'request_timeout': 30,
        'max_retries': 3,
        'respect_robots': False
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration dictionary."""
        self.raw_config = config
        self.validated_config = self._validate_and_normalize(config)
    
    def _validate_and_normalize(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize configuration."""
        # Start with defaults
        validated = self.DEFAULT_CONFIG.copy()
        
        # Override with provided config
        validated.update(config)
        
        # Validate required fields
        self._validate_required_fields(validated)
        
        # Validate individual fields
        self._validate_jurisdiction_level(validated['jurisdiction_level'])
        self._validate_jurisdiction_code(validated['jurisdiction_code'])
        self._validate_enabled_streams(validated['enabled_streams'])
        self._validate_start_date(validated['start_date'])
        self._validate_base_urls(validated['base_urls'])
        self._validate_numeric_fields(validated)
        
        return validated
    
    def _validate_required_fields(self, config: Dict[str, Any]):
        """Validate that required fields are present."""
        required_fields = ['jurisdiction_level', 'jurisdiction_code']
        
        for field in required_fields:
            if field not in config or config[field] is None:
                raise ConfigurationError(f"Required field '{field}' is missing")
    
    def _validate_jurisdiction_level(self, level: str):
        """Validate jurisdiction level."""
        if not isinstance(level, str):
            raise ConfigurationError("jurisdiction_level must be a string")
        
        if level not in self.VALID_JURISDICTION_LEVELS:
            raise ConfigurationError(
                f"jurisdiction_level must be one of: {', '.join(self.VALID_JURISDICTION_LEVELS)}"
            )
    
    def _validate_jurisdiction_code(self, code: str):
        """Validate jurisdiction code."""
        if not isinstance(code, str):
            raise ConfigurationError("jurisdiction_code must be a string")
        
        if not code.strip():
            raise ConfigurationError("jurisdiction_code cannot be empty")
        
        # Basic validation - should be 2-3 character code
        if len(code) < 2 or len(code) > 3:
            raise ConfigurationError("jurisdiction_code should be 2-3 characters")
        
        # Should be uppercase
        if code != code.upper():
            logger.warning(f"jurisdiction_code '{code}' should be uppercase")
    
    def _validate_enabled_streams(self, streams: List[str]):
        """Validate enabled streams."""
        if not isinstance(streams, list):
            raise ConfigurationError("enabled_streams must be a list")
        
        if not streams:
            raise ConfigurationError("At least one stream must be enabled")
        
        invalid_streams = set(streams) - self.VALID_STREAMS
        if invalid_streams:
            raise ConfigurationError(
                f"Invalid streams: {', '.join(invalid_streams)}. "
                f"Valid streams are: {', '.join(self.VALID_STREAMS)}"
            )
    
    def _validate_start_date(self, start_date: str):
        """Validate start date."""
        if not isinstance(start_date, str):
            raise ConfigurationError("start_date must be a string")
        
        try:
            parsed_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            raise ConfigurationError("start_date must be in YYYY-MM-DD format")
        
        # Reasonable date range validation
        min_date = date(2000, 1, 1)
        max_date = date.today()
        
        if parsed_date < min_date:
            raise ConfigurationError(f"start_date cannot be before {min_date}")
        
        if parsed_date > max_date:
            raise ConfigurationError(f"start_date cannot be in the future")
    
    def _validate_base_urls(self, base_urls: Dict[str, str]):
        """Validate base URLs."""
        if not isinstance(base_urls, dict):
            raise ConfigurationError("base_urls must be a dictionary")
        
        required_urls = {'newsroom', 'irb', 'draft_forms', 'mef'}
        missing_urls = required_urls - set(base_urls.keys())
        
        if missing_urls:
            raise ConfigurationError(f"Missing base URLs: {', '.join(missing_urls)}")
        
        for name, url in base_urls.items():
            if not isinstance(url, str):
                raise ConfigurationError(f"base_urls.{name} must be a string")
            
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    raise ConfigurationError(f"base_urls.{name} is not a valid URL: {url}")
                
                if parsed.scheme not in ('http', 'https'):
                    raise ConfigurationError(f"base_urls.{name} must use http or https: {url}")
                    
            except Exception as e:
                raise ConfigurationError(f"Invalid URL for base_urls.{name}: {e}")
    
    def _validate_numeric_fields(self, config: Dict[str, Any]):
        """Validate numeric configuration fields."""
        numeric_fields = {
            'request_timeout': (5, 300),  # 5 seconds to 5 minutes
            'max_retries': (0, 10)        # 0 to 10 retries
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            value = config.get(field)
            
            if value is not None:
                if not isinstance(value, int):
                    raise ConfigurationError(f"{field} must be an integer")
                
                if value < min_val or value > max_val:
                    raise ConfigurationError(
                        f"{field} must be between {min_val} and {max_val}"
                    )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.validated_config.get(key, default)
    
    def get_stream_config(self, stream_name: str) -> Dict[str, Any]:
        """Get configuration specific to a stream."""
        if stream_name not in self.VALID_STREAMS:
            raise ValueError(f"Invalid stream name: {stream_name}")
        
        base_config = {
            'jurisdiction_level': self.get('jurisdiction_level'),
            'jurisdiction_code': self.get('jurisdiction_code'),
            'request_timeout': self.get('request_timeout'),
            'max_retries': self.get('max_retries'),
            'start_date': self.get('start_date')
        }
        
        # Add stream-specific base URL
        base_urls = self.get('base_urls', {})
        
        if stream_name == 'newsroom_releases':
            base_config['base_url'] = base_urls.get('newsroom')
        elif stream_name == 'irb_bulletins':
            base_config['base_url'] = base_urls.get('irb')
        elif stream_name == 'draft_forms':
            base_config['base_url'] = base_urls.get('draft_forms')
        elif stream_name == 'mef_summaries':
            base_config['base_url'] = base_urls.get('mef')
        elif stream_name == 'revproc_items':
            # RevProc items don't have a single base URL
            base_config['base_url'] = None
        
        return base_config
    
    def is_stream_enabled(self, stream_name: str) -> bool:
        """Check if a stream is enabled."""
        enabled_streams = self.get('enabled_streams', [])
        return stream_name in enabled_streams
    
    def get_enabled_streams(self) -> List[str]:
        """Get list of enabled streams."""
        return self.get('enabled_streams', [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Return validated configuration as dictionary."""
        return self.validated_config.copy()
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return (
            f"TaxRulesConfig("
            f"jurisdiction={self.get('jurisdiction_level')}/{self.get('jurisdiction_code')}, "
            f"streams={len(self.get_enabled_streams())}, "
            f"start_date={self.get('start_date')}"
            f")"
        )


def validate_configuration(config: Dict[str, Any]) -> TaxRulesConfig:
    """Validate configuration and return TaxRulesConfig instance."""
    try:
        return TaxRulesConfig(config)
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise ConfigurationError(f"Invalid configuration: {e}")


def get_default_configuration() -> Dict[str, Any]:
    """Get default configuration."""
    return TaxRulesConfig.DEFAULT_CONFIG.copy()


def merge_configurations(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries."""
    merged = base.copy()
    
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Deep merge for nested dictionaries
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    
    return merged


# Configuration presets for different use cases
CONFIGURATION_PRESETS = {
    'federal_full': {
        'jurisdiction_level': 'federal',
        'jurisdiction_code': 'US',
        'enabled_streams': list(TaxRulesConfig.VALID_STREAMS),
        'start_date': '2019-01-01'
    },
    
    'federal_inflation_only': {
        'jurisdiction_level': 'federal',
        'jurisdiction_code': 'US',
        'enabled_streams': ['newsroom_releases', 'revproc_items'],
        'start_date': '2020-01-01'
    },
    
    'federal_forms_only': {
        'jurisdiction_level': 'federal',
        'jurisdiction_code': 'US',
        'enabled_streams': ['draft_forms', 'mef_summaries'],
        'start_date': '2021-01-01'
    },
    
    'development': {
        'jurisdiction_level': 'federal',
        'jurisdiction_code': 'US',
        'enabled_streams': ['newsroom_releases'],  # Single stream for testing
        'start_date': '2024-01-01',
        'request_timeout': 10,
        'max_retries': 1
    }
}


def get_preset_configuration(preset_name: str) -> Dict[str, Any]:
    """Get a preset configuration."""
    if preset_name not in CONFIGURATION_PRESETS:
        available = ', '.join(CONFIGURATION_PRESETS.keys())
        raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")
    
    base_config = get_default_configuration()
    preset_config = CONFIGURATION_PRESETS[preset_name]
    
    return merge_configurations(base_config, preset_config)
