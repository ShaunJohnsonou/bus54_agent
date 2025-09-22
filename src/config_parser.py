import configparser
import os
from typing import Dict, Any, Union


class ConfigParser:
    """
    A configuration parser for handling .ini configuration files.
    """
    
    def __init__(self, config_file: str = "config.ini"):
        """
        Initialize the config parser.
        
        Args:
            config_file (str): Path to the configuration file
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self) -> None:
        """
        Load configuration from the .ini file.
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file '{self.config_file}' not found.")
        
        self.config.read(self.config_file)
    
    def get_section(self, section_name: str) -> Dict[str, str]:
        """
        Get all key-value pairs from a specific section.
        
        Args:
            section_name (str): Name of the section
            
        Returns:
            Dict[str, str]: Dictionary containing all key-value pairs from the section
        """
        if section_name not in self.config.sections():
            raise ValueError(f"Section '{section_name}' not found in configuration file.")
        
        return dict(self.config[section_name])
    
    def get_value(self, section: str, key: str, fallback: Any = None) -> str:
        """
        Get a specific value from the configuration.
        
        Args:
            section (str): Section name
            key (str): Key name
            fallback (Any): Default value if key is not found
            
        Returns:
            str: The configuration value
        """
        return self.config.get(section, key, fallback=fallback)
    
    def get_boolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """
        Get a boolean value from the configuration.
        
        Args:
            section (str): Section name
            key (str): Key name
            fallback (bool): Default value if key is not found
            
        Returns:
            bool: The boolean configuration value
        """
        return self.config.getboolean(section, key, fallback=fallback)
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """
        Get an integer value from the configuration.
        
        Args:
            section (str): Section name
            key (str): Key name
            fallback (int): Default value if key is not found
            
        Returns:
            int: The integer configuration value
        """
        return self.config.getint(section, key, fallback=fallback)
    
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """
        Get a float value from the configuration.
        
        Args:
            section (str): Section name
            key (str): Key name
            fallback (float): Default value if key is not found
            
        Returns:
            float: The float configuration value
        """
        return self.config.getfloat(section, key, fallback=fallback)
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """
        Get all Ollama configuration settings with proper data types.
        
        Returns:
            Dict[str, Any]: Dictionary containing Ollama configuration
        """
        if 'ollama' not in self.config.sections():
            raise ValueError("Ollama section not found in configuration file.")
        
        # Use OLLAMA_HOST env var if set, otherwise use config value
        ollama_url = os.environ.get('OLLAMA_HOST', self.get_value('ollama', 'ollama_url', 'http://localhost:11434'))
        return {
            'url': ollama_url,
            'model': self.get_value('ollama', 'ollama_model', 'llama3.2'),
            'temperature': self.get_float('ollama', 'ollama_temperature', 0.5),
            'max_tokens': self.get_int('ollama', 'ollama_max_tokens', 1000),
            'top_p': self.get_float('ollama', 'ollama_top_p', 1.0),
            'frequency_penalty': self.get_float('ollama', 'ollama_frequency_penalty', 0.0),
            'presence_penalty': self.get_float('ollama', 'ollama_presence_penalty', 0.0),
            'stop': self.get_value('ollama', 'ollama_stop', '[]'),
            'stream': self.get_boolean('ollama', 'ollama_stream', False),
            'format': self.get_value('ollama', 'ollama_format', 'json'),
            'device': self.get_value('ollama', 'ollama_device', 'auto')
        }
    
    def get_azure_openai_config(self) -> Dict[str, Any]:
        """
        Get all Azure OpenAI configuration settings with proper data types.
        
        Returns:
            Dict[str, Any]: Dictionary containing Azure OpenAI configuration
        """
        if 'azure_openai' not in self.config.sections():
            raise ValueError("Azure OpenAI section not found in configuration file.")
        
        return {
            'endpoint': self.get_value('azure_openai', 'azure_endpoint', ''),
            'api_key': self.get_value('azure_openai', 'azure_api_key', ''),
            'api_version': self.get_value('azure_openai', 'azure_api_version', '2024-02-15-preview'),
            'deployment_name': self.get_value('azure_openai', 'azure_deployment_name', 'gpt-4'),
            'model': self.get_value('azure_openai', 'azure_model', 'gpt-4'),
            'temperature': self.get_float('azure_openai', 'azure_temperature', 0.5),
            'max_tokens': self.get_int('azure_openai', 'azure_max_tokens', 1000),
            'top_p': self.get_float('azure_openai', 'azure_top_p', 1.0),
            'frequency_penalty': self.get_float('azure_openai', 'azure_frequency_penalty', 0.0),
            'presence_penalty': self.get_float('azure_openai', 'azure_presence_penalty', 0.0)
        }
    
    def is_local_llm_enabled(self) -> bool:
        """
        Check if local LLM is enabled in the general configurations.
        
        Returns:
            bool: True if local LLM is enabled, False otherwise
        """
        return self.get_boolean('GENERAL CONFIGURATIONS', 'local_LLM', False)
    
    def list_sections(self) -> list:
        """
        Get a list of all sections in the configuration file.
        
        Returns:
            list: List of section names
        """
        return self.config.sections()
    
    def list_keys(self, section: str) -> list:
        """
        Get a list of all keys in a specific section.
        
        Args:
            section (str): Section name
            
        Returns:
            list: List of key names in the section
        """
        if section not in self.config.sections():
            raise ValueError(f"Section '{section}' not found in configuration file.")
        
        return list(self.config[section].keys())
    
    def set_value(self, section: str, key: str, value: Any) -> None:
        """
        Set a specific value in the configuration and save to the file.
        
        Args:
            section (str): Section name
            key (str): Key name
            value (Any): Value to set (will be converted to string)
            
        Returns:
            None
        """
        # Create the section if it doesn't exist
        if section not in self.config.sections():
            self.config.add_section(section)
        
        # Convert value to string (configparser expects string values)
        str_value = str(value)
        if isinstance(value, bool):
            str_value = 'true' if value else 'false'
            
        # Set the value
        self.config.set(section, key, str_value)
        
        # Save changes to the config file
        with open(self.config_file, 'w') as f:
            self.config.write(f)


# Convenience function to create a global config instance
def get_config(config_file: str = "config.ini") -> ConfigParser:
    """
    Get a configured ConfigParser instance.
    
    Args:
        config_file (str): Path to the configuration file
        
    Returns:
        ConfigParser: Configured parser instance
    """
    return ConfigParser(config_file) 