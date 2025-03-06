# app/config.py
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    """Configuration manager for the application using environment variables only."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value from environment variables.
        
        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        env_var_name = f"{section.upper()}_{key.upper()}"
        env_value = os.environ.get(env_var_name)
        
        if env_value is None:
            self.logger.debug(f"Environment variable {env_var_name} not found, using default: {default}")
            return default
            
        # Type conversion based on default value type
        if default is not None:
            if isinstance(default, bool):
                return env_value.lower() in ('true', 'yes', '1', 'y')
            elif isinstance(default, int):
                try:
                    return int(env_value)
                except ValueError:
                    self.logger.warning(f"Could not convert {env_var_name}={env_value} to int, using default: {default}")
                    return default
            elif isinstance(default, float):
                try:
                    return float(env_value)
                except ValueError:
                    self.logger.warning(f"Could not convert {env_var_name}={env_value} to float, using default: {default}")
                    return default
        
        return env_value
    
    @property
    def database_path(self) -> str:
        """Get the database path from configuration."""
        return self.get('database', 'path', 'data/cars.db')
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get the LLM configuration."""
        return {
            'provider': self.get('llm', 'provider', 'deepseek'),
            'api_key': self.get('llm', 'api_key', ''),
            'model': self.get('llm', 'model', 'deepseek-ai/DeepSeek-V3')
        }
    
    @property
    def web_ui_enabled(self) -> bool:
        """Check if web UI is enabled."""
        return self.get('web_ui', 'enabled', True)
    
    @property
    def web_ui_host(self) -> str:
        """Get web UI host address."""
        return self.get('web_ui', 'host', '127.0.0.1')
    
    @property
    def web_ui_port(self) -> int:
        """Get web UI port number."""
        return self.get('web_ui', 'port', 5000)