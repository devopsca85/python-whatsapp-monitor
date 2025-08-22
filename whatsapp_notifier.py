#!/usr/bin/env python3
"""
WhatsApp Notifier - Handles sending WhatsApp notifications
using various methods including WhatsApp Business API and alternative services.

Author: AI Assistant
Date: 2024
"""

import requests
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime


class WhatsAppNotifier:
    """
    Handles WhatsApp notifications using multiple methods.
    Supports WhatsApp Business API and alternative services.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize WhatsApp notifier.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.whatsapp_config = config.get('whatsapp', {})
        self.logger = logging.getLogger(__name__)
        
        # Initialize notification method
        self.method = self.whatsapp_config.get('method', 'twilio')
        self.api_key = self.whatsapp_config.get('api_key', '')
        self.phone_number = self.whatsapp_config.get('phone_number', '')
        self.account_sid = self.whatsapp_config.get('account_sid', '')
        self.auth_token = self.whatsapp_config.get('auth_token', '')
        
        self.logger.info(f"WhatsApp notifier initialized with method: {self.method}")
    
    def send_message(self, message: str) -> bool:
        """
        Send WhatsApp message using the configured method.
        
        Args:
            message (str): Message to send
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            if self.method == 'twilio':
                return self._send_via_twilio(message)
            elif self.method == 'whatsapp_business_api':
                return self._send_via_whatsapp_business_api(message)
            elif self.method == 'ultramsg':
                return self._send_via_ultramsg(message)
            elif self.method == 'callmebot':
                return self._send_via_callmebot(message)
            else:
                self.logger.error(f"Unsupported WhatsApp method: {self.method}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending WhatsApp message: {e}")
            return False
    
    def _send_via_twilio(self, message: str) -> bool:
        """
        Send message via Twilio WhatsApp API.
        
        Args:
            message (str): Message to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not all([self.account_sid, self.auth_token, self.phone_number]):
                self.logger.error("Missing Twilio credentials")
                return False
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            
            data = {
                'From': 'whatsapp:+14155238886',  # Twilio WhatsApp number
                'To': f'whatsapp:{self.phone_number}',
                'Body': message
            }
            
            response = requests.post(
                url,
                data=data,
                auth=(self.account_sid, self.auth_token),
                timeout=30
            )
            
            if response.status_code == 201:
                self.logger.info("Message sent successfully via Twilio")
                return True
            else:
                self.logger.error(f"Twilio API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending via Twilio: {e}")
            return False
    
    def _send_via_whatsapp_business_api(self, message: str) -> bool:
        """
        Send message via WhatsApp Business API.
        
        Args:
            message (str): Message to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not all([self.api_key, self.phone_number]):
                self.logger.error("Missing WhatsApp Business API credentials")
                return False
            
            url = "https://graph.facebook.com/v17.0/YOUR_PHONE_NUMBER_ID/messages"
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'to': self.phone_number,
                'type': 'text',
                'text': {'body': message}
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                self.logger.info("Message sent successfully via WhatsApp Business API")
                return True
            else:
                self.logger.error(f"WhatsApp Business API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending via WhatsApp Business API: {e}")
            return False
    
    def _send_via_ultramsg(self, message: str) -> bool:
        """
        Send message via UltraMsg service.
        
        Args:
            message (str): Message to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not all([self.api_key, self.phone_number]):
                self.logger.error("Missing UltraMsg credentials")
                return False
            
            url = "https://api.ultramsg.com/YOUR_INSTANCE_ID/messages/chat"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            data = {
                'token': self.api_key,
                'to': self.phone_number,
                'body': message
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('sent'):
                    self.logger.info("Message sent successfully via UltraMsg")
                    return True
                else:
                    self.logger.error(f"UltraMsg error: {result}")
                    return False
            else:
                self.logger.error(f"UltraMsg API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending via UltraMsg: {e}")
            return False
    
    def _send_via_callmebot(self, message: str) -> bool:
        """
        Send message via CallMeBot service (free alternative).
        
        Args:
            message (str): Message to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.api_key:
                self.logger.error("Missing CallMeBot API key")
                return False
            
            # URL encode the message
            import urllib.parse
            encoded_message = urllib.parse.quote(message)
            
            url = f"https://api.callmebot.com/whatsapp.php?phone={self.phone_number}&text={encoded_message}&apikey={self.api_key}"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                self.logger.info("Message sent successfully via CallMeBot")
                return True
            else:
                self.logger.error(f"CallMeBot API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending via CallMeBot: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test the WhatsApp connection by sending a test message.
        
        Returns:
            bool: True if test successful, False otherwise
        """
        test_message = f"🧪 Test message from Server Monitor\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nThis is a test message to verify WhatsApp integration."
        
        self.logger.info("Testing WhatsApp connection...")
        return self.send_message(test_message)


def main():
    """Test function for WhatsApp notifier."""
    import json
    
    # Load test configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found. Please create it first.")
        return 1
    
    # Test WhatsApp notifier
    notifier = WhatsAppNotifier(config)
    
    print("🧪 Testing WhatsApp integration...")
    success = notifier.test_connection()
    
    if success:
        print("✅ WhatsApp test successful!")
    else:
        print("❌ WhatsApp test failed!")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

