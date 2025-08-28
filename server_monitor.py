#!/usr/bin/env python3
"""
Server Monitor - Monitors multiple services (by URL) and sends WhatsApp notifications
when a service goes down or recovers.
Author: AI Assistant
Date: 2025
"""
import time
import json
import logging
import requests
import socket
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from twilio.rest import Client
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
# ================== Load Config ==================
with open("config.json", "r") as f:
    config = json.load(f)
services = config["services"]
monitoring = config["monitoring"]
whatsapp_cfg = config["whatsapp"]
# Override sensitive WhatsApp/Twilio values from environment variables if present
whatsapp_cfg["account_sid"] = os.getenv("TWILIO_ACCOUNT_SID", whatsapp_cfg.get("account_sid", ""))
whatsapp_cfg["auth_token"] = os.getenv("TWILIO_AUTH_TOKEN", whatsapp_cfg.get("auth_token", ""))
whatsapp_cfg["from_number"] = os.getenv("WHATSAPP_FROM_NUMBER", whatsapp_cfg.get("from_number", ""))
# Support comma-separated list for recipients
env_to_numbers = os.getenv("WHATSAPP_TO_NUMBERS")
if env_to_numbers:
    whatsapp_cfg["to_numbers"] = [n.strip() for n in env_to_numbers.split(",") if n.strip()]
logging_cfg = config["logging"]
notifications_cfg = config["notifications"]
# ================== Logging Setup ==================
handler = RotatingFileHandler(
    logging_cfg["file"],
    maxBytes=int(logging_cfg["max_size"].replace("MB", "")) * 1024 * 1024,
    backupCount=logging_cfg["backup_count"]
)
logging.basicConfig(
    level=getattr(logging, logging_cfg["level"]),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler, logging.StreamHandler()]
)
logger = logging.getLogger()
# ================== Twilio Client ==================
client = Client(whatsapp_cfg["account_sid"], whatsapp_cfg["auth_token"])
def send_whatsapp(message):
    """Send WhatsApp message to all numbers"""
    for number in whatsapp_cfg["to_numbers"]:
        try:
            client.messages.create(
                from_=whatsapp_cfg["from_number"],
                body=message,
                to=number
            )
            logger.info(f"📩 WhatsApp sent to {number}: {message}")
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp to {number}: {e}")
# ================== Service Checker ==================
def get_server_ip(url):
    """Get server IP from URL"""
    hostname = url.split("//")[-1].split("/")[0].split(":")[0]
    try:
        return socket.gethostbyname(hostname)
    except Exception as e:
        logger.error(f"Failed to get IP for {hostname}: {e}")
        return "Unknown"
def check_service(service):
    """Check a service and return status info"""
    status_info = {
        "name": service["name"],
        "url": service["url"],
        "server_ip": get_server_ip(service["url"]),
        "status_code": None,
        "message": ""
    }
   
    try:
        response = requests.get(service["url"], timeout=service.get("timeout", 5))
        status_info["status_code"] = response.status_code
        if 200 <= response.status_code < 300:
            status_info["message"] = f"✅ {service['name']} is UP (Status {response.status_code})"
            return True, status_info
        else:
            status_info["message"] = f"❌ {service['name']} is DOWN (Status {response.status_code})"
            return False, status_info
    except Exception as e:
        status_info["message"] = f"❌ {service['name']} check failed: {e}"
        return False, status_info
# ================== Main Monitor Loop ==================
def monitor_services():
    status = {srv["name"]: True for srv in services} # assume healthy initially
    last_alert_time = {srv["name"]: 0 for srv in services}
    logger.info("🚀 Starting Server Monitor...")
    print("🚀 Starting Server Monitor...")
    print("Press Ctrl+C to stop monitoring")
    print("-" * 50)
    # 🔹 Send startup WhatsApp notification
    send_whatsapp(f"🚀 Server Monitor started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    while True:
        for service in services:
            name = service["name"]
            is_up, info = check_service(service)
            msg = (
                f"{info['message']}\n"
                f"🌐 Domain: {info['url']}\n"
                f"🖥️ Server IP: {info['server_ip']}\n"
                f"⏰ Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            if is_up and not status[name]:
                # Recovery
                status[name] = True
                if notifications_cfg["send_on_recovery"]:
                    send_whatsapp(msg)
            elif not is_up and status[name]:
                # Downtime
                status[name] = False
                now = time.time()
                if notifications_cfg["send_on_downtime"] and (now - last_alert_time[name]) > notifications_cfg["cooldown_period"]:
                    send_whatsapp(msg)
                    last_alert_time[name] = now
        time.sleep(monitoring["check_interval"])
if __name__ == "__main__":
    try:
        monitor_services()
    except KeyboardInterrupt:
        logger.info("🛑 Server Monitor stopped by user")
        print("\n🛑 Server Monitor stopped by user")
