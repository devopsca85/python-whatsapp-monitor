#!/usr/bin/env python3
"""
WhatsApp Notifier - Handles sending WhatsApp notifications
using multiple methods including Twilio, WhatsApp Business API, UltraMsg, and CallMeBot.

Author: AI Assistant
Date: 2025
"""

import requests
import logging
import time
import urllib.parse
from typing import Dict, Any
from datetime import datetime
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class WhatsAppNotifier:
    """Handles WhatsApp notifications using multiple methods."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.whatsapp_config = config.get("whatsapp", {})
        self.logger = logging.getLogger("WhatsAppNotifier")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

        # Config fields
        self.method = os.getenv("WHATSAPP_METHOD", self.whatsapp_config.get("method", "twilio")).lower()
        self.api_key = os.getenv("WHATSAPP_API_KEY", self.whatsapp_config.get("api_key", ""))
        self.from_number = os.getenv("WHATSAPP_FROM_NUMBER", self.whatsapp_config.get("from_number", ""))
        env_to_numbers = os.getenv("WHATSAPP_TO_NUMBERS")
        self.to_numbers = [n.strip() for n in env_to_numbers.split(",")] if env_to_numbers else self.whatsapp_config.get("to_numbers", [])
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", self.whatsapp_config.get("account_sid", ""))
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", self.whatsapp_config.get("auth_token", ""))
        self.phone_number_id = os.getenv("WABA_PHONE_NUMBER_ID", self.whatsapp_config.get("phone_number_id", ""))
        self.instance_id = os.getenv("ULTRAMSG_INSTANCE_ID", self.whatsapp_config.get("instance_id", ""))  # ✅ for UltraMsg

        self.logger.info(f"WhatsApp notifier initialized with method: {self.method}")

    def send_message(self, message: str, retries: int = 3, backoff: int = 5) -> bool:
        """Send message with retries and backoff"""
        for attempt in range(1, retries + 1):
            try:
                if self.method == "twilio":
                    return self._send_via_twilio(message)
                elif self.method == "whatsapp_business_api":
                    return self._send_via_whatsapp_business_api(message)
                elif self.method == "ultramsg":
                    return self._send_via_ultramsg(message)
                elif self.method == "callmebot":
                    return self._send_via_callmebot(message)
                else:
                    self.logger.error(f"Unsupported WhatsApp method: {self.method}")
                    return False
            except Exception as e:
                self.logger.error(f"Attempt {attempt}: Error sending message: {e}")
                if attempt < retries:
                    time.sleep(backoff * attempt)
        return False

    def _send_via_twilio(self, message: str) -> bool:
        """Send message via Twilio WhatsApp API to multiple recipients."""
        if not all([self.account_sid, self.auth_token, self.from_number, self.to_numbers]):
            self.logger.error("Missing Twilio configuration values")
            return False

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        success_all = True

        for to in self.to_numbers:
            data = {"From": self.from_number, "To": to, "Body": message}
            response = requests.post(url, data=data, auth=(self.account_sid, self.auth_token), timeout=30)

            if response.status_code == 201:
                self.logger.info(f"✅ Twilio: Message sent to {to}")
            else:
                self.logger.error(f"❌ Twilio error for {to}: {response.status_code} - {response.text}")
                success_all = False

        return success_all

    def _send_via_whatsapp_business_api(self, message: str) -> bool:
        """Send message via WhatsApp Business API (Meta)"""
        if not all([self.api_key, self.phone_number_id, self.to_numbers]):
            self.logger.error("Missing WhatsApp Business API configuration values")
            return False

        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        success_all = True
        for to in self.to_numbers:
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message}
            }
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                self.logger.info(f"✅ WABA: Message sent to {to}")
            else:
                self.logger.error(f"❌ WABA error for {to}: {response.status_code} - {response.text}")
                success_all = False

        return success_all

    def _send_via_ultramsg(self, message: str) -> bool:
        """Send message via UltraMsg API"""
        if not all([self.api_key, self.instance_id, self.to_numbers]):
            self.logger.error("Missing UltraMsg credentials")
            return False

        url = f"https://api.ultramsg.com/{self.instance_id}/messages/chat"
        headers = {"Content-Type": "application/json"}

        success_all = True
        for to in self.to_numbers:
            data = {"token": self.api_key, "to": to, "body": message}
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if result.get("sent"):
                    self.logger.info(f"✅ UltraMsg: Message sent to {to}")
                else:
                    self.logger.error(f"❌ UltraMsg failed for {to}: {result}")
                    success_all = False
            else:
                self.logger.error(f"❌ UltraMsg API error for {to}: {response.status_code} - {response.text}")
                success_all = False

        return success_all

    def _send_via_callmebot(self, message: str) -> bool:
        """Send message via CallMeBot service"""
        if not all([self.api_key, self.to_numbers]):
            self.logger.error("Missing CallMeBot credentials")
            return False

        success_all = True
        for to in self.to_numbers:
            encoded_message = urllib.parse.quote(message)
            url = f"https://api.callmebot.com/whatsapp.php?phone={to}&text={encoded_message}&apikey={self.api_key}"
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                self.logger.info(f"✅ CallMeBot: Message sent to {to}")
            else:
                self.logger.error(f"❌ CallMeBot error for {to}: {response.status_code} - {response.text}")
                success_all = False

        return success_all

    def test_connection(self) -> bool:
        """Send a test message to verify setup"""
        test_message = (
            f"🧪 Test message from Server Monitor\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"This is a test message."
        )
        self.logger.info("Testing WhatsApp connection...")
        return self.send_message(test_message)


def main():
    """Run a standalone test"""
    import json
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found. Please create it first.")
        return 1

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
