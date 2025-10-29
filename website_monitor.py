#!/usr/bin/env python3
"""
Website Monitor - Monitors website availability and uptime
Sends WhatsApp alerts for website downtime and recovery
Separate from database monitoring for better modularity

Author: AI Assistant
Date: 2025
"""

import json, logging, requests, socket, os, schedule, time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from whatsapp_notifier import WhatsAppNotifier
from dotenv import load_dotenv

# ================== Load Environment Variables ==================
load_dotenv()
SERVERS = os.getenv("WEB_SERVERS", os.getenv("SERVERS", "")).split(",")

# ================== Load Config from Environment ==================
from config_helper import get_config, WEBSITE_MONITORING, CUSTOM_ENDPOINTS

config = get_config()
web_monitoring = WEBSITE_MONITORING
whatsapp_cfg = config.get("whatsapp", {})
logging_cfg = config.get("logging", {"level": "INFO"})

# Override WhatsApp/Twilio values from .env
whatsapp_cfg["account_sid"] = os.getenv("TWILIO_ACCOUNT_SID", whatsapp_cfg.get("account_sid", ""))
whatsapp_cfg["auth_token"] = os.getenv("TWILIO_AUTH_TOKEN", whatsapp_cfg.get("auth_token", ""))
whatsapp_cfg["from_number"] = os.getenv("WHATSAPP_FROM_NUMBER", whatsapp_cfg.get("from_number", ""))
env_to_numbers = os.getenv("WHATSAPP_TO_NUMBERS")
if env_to_numbers:
    whatsapp_cfg["to_numbers"] = [n.strip() for n in env_to_numbers.split(",") if n.strip()]

# ================== Logging Setup ==================
handler = RotatingFileHandler(
    "website_monitor.log",
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler, logging.StreamHandler()],
)
logger = logging.getLogger()

# ================== WhatsApp Notifier ==================
whatsapp_notifier = WhatsAppNotifier(config)

# Track previous website status
previous_status = {}  # { url: is_up }

# ================== WhatsApp Helper ==================
def send_whatsapp(message):
    try:
        success = whatsapp_notifier.send_message(message)
        if success:
            logger.info("📩 WhatsApp website alert sent")
        else:
            logger.error("❌ Failed to send WhatsApp alert")
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp: {e}")

# ================== API Helpers ==================
def get_server_api_credentials(ip):
    env_ip = ip.replace(".", "_")
    api_token = os.getenv(f"API_TOKEN_{env_ip}")
    api_endpoint = os.getenv(f"API_ENDPOINT_{env_ip}", f"http://{ip}:5000/api")
    return api_token, api_endpoint

def get_websites_from_api(ip):
    try:
        api_token, api_endpoint = get_server_api_credentials(ip)
        if not api_token:
            return []
        headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
        resp = requests.get(f"{api_endpoint}/websites", headers=headers, timeout=10)
        if resp.status_code == 200:
            websites = resp.json().get("websites", [])
            logger.info(f"   Found {len(websites)} websites on {ip}")
            return websites
        else:
            return []
    except Exception as e:
        logger.error(f"Error getting websites from {ip}: {e}")
        return []

# ================== Website Checker ==================
def get_server_ip(url):
    try:
        hostname = url.split("//")[-1].split("/")[0].split(":")[0]
        return socket.gethostbyname(hostname)
    except:
        return "Unknown"

def check_website(website, timeout=5, retries=2):
    info = {
        "name": website,
        "url": f"https://{website}" if not website.startswith("http") else website,
        "server_ip": get_server_ip(f"https://{website}"),
        "status_code": None
    }
    
    for attempt in range(retries + 1):
        try:
            resp = requests.get(info["url"], timeout=timeout, verify=True)
            info["status_code"] = resp.status_code
            return 200 <= resp.status_code < 300, info
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
            else:
                logger.warning(f"Website {website} check failed: {e}")
    
    return False, info

def format_alert(website, is_up, info):
    if is_up:
        return (
            f"✅ WEBSITE UP ✅\n"
            f"Domain: {info['url']}\n"
            f"Status: UP ({info['status_code']})\n"
            f"Server IP: {info['server_ip']}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        return (
            f"🚨 WEBSITE DOWN 🚨\n"
            f"Domain: {info['url']}\n"
            f"Status: DOWN ({info['status_code'] or 'No Response'})\n"
            f"Server IP: {info['server_ip']}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

# ================== Main Website Monitor ==================
def monitor_websites():
    global previous_status
    
    logger.info("🌐 Checking websites and API endpoints...")
    
    websites_to_check = []
    
    # 1. Get auto-discovered websites from servers
    for ip in SERVERS:
        ip = ip.strip()
        if not ip:
            continue
        
        websites = get_websites_from_api(ip)
        for website in websites:
            websites_to_check.append({"url": website, "name": website, "type": "auto"})
    
    # 2. Add custom endpoints from environment
    custom_endpoints = CUSTOM_ENDPOINTS
    for endpoint in custom_endpoints:
        if isinstance(endpoint, str):
            websites_to_check.append({"url": endpoint, "name": endpoint, "type": "custom"})
        else:
            websites_to_check.append({
                "url": endpoint.get("url", ""),
                "name": endpoint.get("name", endpoint.get("url", "")),
                "type": "custom",
                "timeout": endpoint.get("timeout", web_monitoring.get("timeout", 5))
            })
    
    if not websites_to_check:
        logger.warning("No websites or endpoints found to monitor")
        return
    
    logger.info(f"   Checking {len(websites_to_check)} websites/endpoints...")
    
    for site in websites_to_check:
        url = site["url"] if site["url"].startswith("http") else f"https://{site['url']}"
        timeout = site.get("timeout", web_monitoring.get("timeout", 5))
        
        is_up, info = check_website(url, timeout=timeout)
        
        # Check if status changed
        if previous_status.get(url) != is_up:
            msg = format_alert(site["name"], is_up, info)
            send_whatsapp(msg)
            logger.info(f"   {site['name']}: {'✅ UP' if is_up else '❌ DOWN'} ({info.get('status_code', 'N/A')})")
        
        previous_status[url] = is_up
    
    logger.info("✅ Website/endpoint check complete")

# ================== Run Monitor ==================
if __name__ == "__main__":
    try:
        print("🌐 Starting Website Monitor...")
        print(f"   Servers: {', '.join([s.strip() for s in SERVERS if s.strip()])}")
        print(f"   Check interval: {web_monitoring.get('check_interval', 300)} seconds")
        print(f"   Timeout: {web_monitoring.get('timeout', 5)} seconds")
        print(f"   Log file: website_monitor.log")
        print("")
        
        # Run one check immediately
        monitor_websites()
        
        # Schedule monitoring loop
        interval = web_monitoring.get('check_interval', 300)
        schedule.every(interval).seconds.do(monitor_websites)
        
        print(f"✅ Monitoring started! Checking every {interval} seconds...")
        print("   Press Ctrl+C to stop")
        print("")
        
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Website Monitor stopped by user")
        print("\n🛑 Website Monitor stopped by user")
