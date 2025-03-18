import os
import yaml
from typing import Dict
from datetime import datetime
from copy import deepcopy

class Config:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        # Determine environment
        env = os.getenv('ENVIRONMENT', 'dev').lower()
        
        # Load base config
        base_config = self._load_yaml_file('config/config.yml')
        base_config = self._process_date_placeholders(base_config)
        
        # Load environment-specific config
        env_config = self._load_yaml_file(f'config/{env}.config.yml')
        env_config = self._process_date_placeholders(env_config)
        
        # Merge configurations with base config taking precedence
        self._config = self._deep_merge(base_config.get('default', {}), env_config)

    def _process_date_placeholders(self, config: Dict) -> Dict:
        """Replace date placeholders in configuration strings"""
        processed = {}
        today = datetime.now()
        date_formats = {
            '{DATE}': today.strftime('%Y_%m_%d'),
            '{DATE_TIME}': today.strftime('%Y_%m_%d_%H:%M:%S'),
            '{YEAR}': today.strftime('%Y'),
            '{MONTH}': today.strftime('%m'),
            '{DAY}': today.strftime('%d'),
        }
        
        def process_value(value):
            if isinstance(value, str):
                result = value
                for placeholder, date_str in date_formats.items():
                    result = result.replace(placeholder, date_str)
                return result
            elif isinstance(value, dict):
                return self._process_date_placeholders(value)
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            return value
        
        for key, value in config.items():
            processed[key] = process_value(value)
            
        return processed

    @staticmethod
    def _load_yaml_file(file_path: str) -> Dict:
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Warning: Configuration file {file_path} not found")
            return {}

    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        """
        Deep merge two dictionaries with override values taking precedence over base
        for existing keys at the same level
        """
        merged = deepcopy(base)

        for key, value in override.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = Config._deep_merge(merged[key], value)
            else:
                merged[key] = deepcopy(value)
            
        return merged

    def get_config(self) -> Dict:
        """Get the complete configuration"""
        return self._config

    def get(self, key: str, default=None):
        """Get a specific configuration value"""
        return self._config.get(key, default)

# Create a singleton instance
config = Config().get_config()
