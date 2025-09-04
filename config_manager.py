#!/usr/bin/env python3
"""
Configuration Manager - Handles loading and validating configuration settings
for the server monitoring system.

Author: AI Assistant
Date: 2024
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """
    Manages configuration loading, validation, and default settings.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default configuration.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                # Validate configuration
                self._validate_config(config)
                self.logger.info(f"Configuration loaded from {self.config_path}")
                return config
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in config file: {e}")
                return self._create_default_config()
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                return self._create_default_config()
        else:
            self.logger.warning(f"Config file {self.config_path} not found. Creating default configuration.")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create default configuration.
        
        Returns:
            Dict[str, Any]: Default configuration dictionary
        """
        default_config = {
            "server": {
                "host": "localhost",
                "port": 80,
                "timeout": 5
            },
            "monitoring": {
                "check_interval": 30,
                "retry_attempts": 3,
                "retry_delay": 10
            },
            "whatsapp": {
                "method": "callmebot",
                "api_key": "YOUR_API_KEY_HERE",
                "phone_number": "YOUR_PHONE_NUMBER_HERE",
                "account_sid": "",
                "auth_token": ""
            },
            "logging": {
                "level": "INFO",
                "file": "server_monitor.log",
                "max_size": "10MB",
                "backup_count": 5
            },
            "notifications": {
                "send_on_downtime": True,
                "send_on_recovery": True,
                "cooldown_period": 300
            }
        }
        
        # Save default configuration
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to file.
        
        Args:
            config (Dict[str, Any]): Configuration to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            self.logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure and required fields.
        
        Args:
            config (Dict[str, Any]): Configuration to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_sections = ['server', 'monitoring', 'whatsapp']
        
        for section in required_sections:
            if section not in config:
                self.logger.error(f"Missing required configuration section: {section}")
                return False
        
        # Validate server configuration
        server_config = config['server']
        if not all(key in server_config for key in ['host', 'port']):
            self.logger.error("Server configuration missing required fields: host, port")
            return False
        
        # Validate WhatsApp configuration
        whatsapp_config = config['whatsapp']
        if not all(key in whatsapp_config for key in ['method', 'api_key', 'phone_number']):
            self.logger.error("WhatsApp configuration missing required fields: method, api_key, phone_number")
            return False
        
        # Validate method-specific requirements
        method = whatsapp_config['method']
        if method == 'twilio':
            if not all(key in whatsapp_config for key in ['account_sid', 'auth_token']):
                self.logger.error("Twilio method requires account_sid and auth_token")
                return False
        
        return True
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration with new values.
        
        Args:
            updates (Dict[str, Any]): Configuration updates
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            current_config = self.load_config()
            
            # Recursively update configuration
            self._recursive_update(current_config, updates)
            
            # Validate updated configuration
            if not self._validate_config(current_config):
                return False
            
            # Save updated configuration
            return self.save_config(current_config)
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False
    
    def _recursive_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """
        Recursively update dictionary with new values.
        
        Args:
            base_dict (Dict[str, Any]): Base dictionary to update
            update_dict (Dict[str, Any]): Dictionary with updates
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._recursive_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get_server_config(self) -> Dict[str, Any]:
        """
        Get server configuration.
        
        Returns:
            Dict[str, Any]: Server configuration
        """
        config = self.load_config()
        return config.get('server', {})
    
    def get_whatsapp_config(self) -> Dict[str, Any]:
        """
        Get WhatsApp configuration.
        
        Returns:
            Dict[str, Any]: WhatsApp configuration
        """
        config = self.load_config()
        return config.get('whatsapp', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """
        Get monitoring configuration.
        
        Returns:
            Dict[str, Any]: Monitoring configuration
        """
        config = self.load_config()
        return config.get('monitoring', {})


def main():
    """Test function for configuration manager."""
    print("🔧 Testing Configuration Manager...")
    
    # Create configuration manager
    config_manager = ConfigManager()
    
    # Load configuration
    config = config_manager.load_config()
    
    print("✅ Configuration loaded successfully!")
    print(f"📁 Config file: {config_manager.config_path}")
    print(f"🖥️  Server: {config['server']['host']}:{config['server']['port']}")
    print(f"📱 WhatsApp method: {config['whatsapp']['method']}")
    print(f"⏱️  Check interval: {config['monitoring']['check_interval']} seconds")
    
    return 0


if __name__ == "__main__":
    exit(main())

