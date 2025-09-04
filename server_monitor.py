#!/usr/bin/env python3
"""
Server Monitor - Multi-server monitoring with per-server SSH credentials and ports.
Checks only `.com` sites and sends WhatsApp alerts if a site is UP or DOWN at startup.
Author: AI Assistant
Date: 2025
"""
import json
import logging
import requests
import socket
import os
import paramiko
from datetime import datetime
from logging.handlers import RotatingFileHandler
from twilio.rest import Client
from dotenv import load_dotenv

# ================== Load Environment Variables ==================
load_dotenv()
SERVERS = os.getenv("SERVERS", "").split(",")

# ================== Load Config ==================
with open("config.json", "r") as f:
    config = json.load(f)
monitoring = config["monitoring"]
whatsapp_cfg = config["whatsapp"]
logging_cfg = config["logging"]

# Override WhatsApp/Twilio values
whatsapp_cfg["account_sid"] = os.getenv("TWILIO_ACCOUNT_SID", whatsapp_cfg.get("account_sid", ""))
whatsapp_cfg["auth_token"] = os.getenv("TWILIO_AUTH_TOKEN", whatsapp_cfg.get("auth_token", ""))
whatsapp_cfg["from_number"] = os.getenv("WHATSAPP_FROM_NUMBER", whatsapp_cfg.get("from_number", ""))
env_to_numbers = os.getenv("WHATSAPP_TO_NUMBERS")
if env_to_numbers:
    whatsapp_cfg["to_numbers"] = [n.strip() for n in env_to_numbers.split(",") if n.strip()]

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

# ================== SSH Helpers ==================
def get_server_credentials(ip):
    """Fetch SSH username, key, and port for a given IP from environment"""
    env_ip = ip.replace(".", "_")
    username = os.getenv(f"SSH_USERNAME_{env_ip}")
    key_path = os.getenv(f"SSH_KEY_PATH_{env_ip}")
    port = int(os.getenv(f"SSH_PORT_{env_ip}", 22))
    return username, key_path, port

def connect_ssh(ip):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        username, key_path, port = get_server_credentials(ip)

        if not username or not key_path:
            logger.error(f"❌ Missing SSH config for {ip}, skipping...")
            return None

        private_key = paramiko.RSAKey.from_private_key_file(key_path)
        ssh.connect(ip, port=port, username=username, pkey=private_key)

        logger.info(f"✅ Connected to {ip}:{port} as {username}")
        return ssh
    except Exception as e:
        logger.error(f"❌ Error connecting to {ip}: {e}")
        return None

def get_website_folders(ssh, ip):
    """Get only `.com` website folders under /var/www/"""
    try:
        stdin, stdout, stderr = ssh.exec_command("ls -d /var/www/*/ 2>/dev/null")
        folders = stdout.read().decode().strip().split("\n")
        valid = [os.path.basename(f.rstrip("/")) for f in folders if f.endswith(".com/")]
        logger.info(f"🌐 {ip} - Found .com sites: {valid}")
        return valid
    except Exception as e:
        logger.error(f"❌ Error listing website folders on {ip}: {e}")
        return []

# ================== Service Checker ==================
def get_server_ip(url):
    hostname = url.split("//")[-1].split("/")[0].split(":")[0]
    try:
        return socket.gethostbyname(hostname)
    except Exception as e:
        logger.error(f"❌ Failed to resolve {hostname}: {e}")
        return "Unknown"

def check_service(service, timeout=5):
    status_info = {
        "name": service["name"],
        "url": service["url"],
        "server_ip": get_server_ip(service["url"]),
        "status_code": None
    }
    try:
        response = requests.get(service["url"], timeout=timeout, verify=True)
        status_info["status_code"] = response.status_code
        return (200 <= response.status_code < 300), status_info
    except requests.RequestException:
        return False, status_info

# ================== Message Formatter ==================
def format_message(service, is_up, info):
    if is_up:
        return (
            f"✅ SERVER UP ✅\n\n"
            f"Domain: {service['url']}\n"
            f"Status: UP ({info['status_code']})\n"
            f"Server IP: {info['server_ip']}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
    else:
        return (
            f"🚨 SERVER DOWN ALERT 🚨\n\n"
            f"Domain: {service['url']}\n"
            f"Status: DOWN ({info['status_code'] or 'No Response'})\n"
            f"Server IP: {info['server_ip']}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

# ================== Main Monitor ==================
def monitor_services():
    services = []
    for ip in SERVERS:
        ip = ip.strip()
        if not ip:
            continue
        ssh = connect_ssh(ip)
        if ssh:
            folders = get_website_folders(ssh, ip)
            for folder in folders:
                services.append({
                    "name": f"{folder} on {ip}",
                    "url": f"https://{folder}",
                    "timeout": monitoring.get("timeout", 5)
                })
            ssh.close()

    if not services:
        logger.error("❌ No websites found to monitor. Exiting.")
        print("❌ No websites found to monitor. Exiting.")
        return

    print("🚀 Starting Multi-Server Monitor...")
    print("Checking for UP/DOWN alerts only...")
    print("-" * 50)

    for service in services:
        is_up, info = check_service(service, service.get("timeout", 5))
        if not is_up or (is_up and info["status_code"] != 200):
            msg = format_message(service, is_up, info)
            send_whatsapp(msg)

if __name__ == "__main__":
    try:
        monitor_services()
    except KeyboardInterrupt:
        logger.info("🛑 Server Monitor stopped by user")
        print("\n🛑 Server Monitor stopped by user")

