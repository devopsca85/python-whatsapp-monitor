#!/usr/bin/env python3
"""
Server Monitor - Multi-server monitoring with secure API-based access.
Monitors:
- Websites (.com)
- MySQL databases and tables (crash/corruption/missing)
- PostgreSQL databases and tables (missing/error)
Sends WhatsApp alerts on status changes.
"""

import json, logging, requests, socket, os, schedule, time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from whatsapp_notifier import WhatsAppNotifier
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

# Override WhatsApp/Twilio values from .env
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
    backupCount=logging_cfg["backup_count"],
)
logging.basicConfig(
    level=getattr(logging, logging_cfg["level"]),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler, logging.StreamHandler()],
)
logger = logging.getLogger()

# ================== WhatsApp Notifier ==================
whatsapp_notifier = WhatsAppNotifier(config)

# Track previous status
previous_status = {}        # Websites
previous_db_status = {}     # { ip: { "mysql": {"dbs": {}, "tables": {}}, "postgresql": {"dbs": {}, "tables": {}} } }

# ================== WhatsApp Helper ==================
def send_whatsapp(message):
    try:
        success = whatsapp_notifier.send_message(message)
        if success:
            logger.info("📩 WhatsApp message sent successfully")
        else:
            logger.error("❌ Failed to send WhatsApp message")
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp: {e}")

# ================== API Helpers ==================
def get_server_api_credentials(ip):
    env_ip = ip.replace(".", "_")
    api_token = os.getenv(f"API_TOKEN_{env_ip}")
    api_endpoint = os.getenv(f"API_ENDPOINT_{env_ip}", f"http://{ip}:5000/api")
    return api_token, api_endpoint

def get_website_folders_via_api(ip):
    try:
        api_token, api_endpoint = get_server_api_credentials(ip)
        if not api_token:
            return []
        headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
        resp = requests.get(f"{api_endpoint}/websites", headers=headers, timeout=10)
        if resp.status_code == 200:
            # Include both .com and .in domains
            return [site for site in resp.json().get("websites", []) if site.endswith(".com") or site.endswith(".in")]
        else:
            return []
    except:
        return []


def check_server_health_via_api(ip):
    try:
        api_token, api_endpoint = get_server_api_credentials(ip)
        if not api_token:
            print(f"   No API token for {ip}")
            return False
        headers = {"Authorization": f"Bearer {api_token}"}
        resp = requests.get(f"{api_endpoint}/health", headers=headers, timeout=5)
        print(f"   Health check response: {resp.status_code}")
        return resp.status_code == 200
    except Exception as e:
        print(f"   Health check error: {e}")
        return False

def check_mysql_databases(ip):
    try:
    api_token, api_endpoint = get_server_api_credentials(ip)
        headers = {"Authorization": f"Bearer {api_token}"}
        resp = requests.get(f"{api_endpoint}/mysql-all-dbs-health", headers=headers, timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

def check_mysql_tables(ip):
    try:
        api_token, api_endpoint = get_server_api_credentials(ip)
        headers = {"Authorization": f"Bearer {api_token}"}
        resp = requests.get(f"{api_endpoint}/mysql-all-tables-health", headers=headers, timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except:
            return {}

def check_postgresql_databases(ip):
    try:
        api_token, api_endpoint = get_server_api_credentials(ip)
        headers = {"Authorization": f"Bearer {api_token}"}
        resp = requests.get(f"{api_endpoint}/postgresql-all-dbs-health", headers=headers, timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

def check_postgresql_tables(ip):
    try:
        api_token, api_endpoint = get_server_api_credentials(ip)
        headers = {"Authorization": f"Bearer {api_token}"}
        resp = requests.get(f"{api_endpoint}/postgresql-all-tables-health", headers=headers, timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

# ================== Website Checker ==================
def get_server_ip(url):
    try:
        return socket.gethostbyname(url.split("//")[-1].split("/")[0].split(":")[0])
    except:
        return "Unknown"

def check_service(service, timeout=5, retries=2):
    info = {"name": service["name"], "url": service["url"], "server_ip": get_server_ip(service["url"]), "status_code": None}
    for _ in range(retries + 1):
        try:
            resp = requests.get(service["url"], timeout=timeout, verify=True)
            info["status_code"] = resp.status_code
            return 200 <= resp.status_code < 300, info
        except:
                time.sleep(2)
    return False, info

def format_message(service, is_up, info):
    if is_up:
        return (
            f"✅ SERVER UP ✅\nDomain: {service['url']}\nStatus: UP ({info['status_code']})"
            f"\nServer IP: {info['server_ip']}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        return (
            f"🚨 SERVER DOWN ALERT 🚨\nDomain: {service['url']}\nStatus: DOWN ({info['status_code'] or 'No Response'})"
            f"\nServer IP: {info['server_ip']}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

# ================== Main Monitor ==================
def monitor_services():
    global previous_status, previous_db_status
    services = []
    print("🚀 Checking server health, websites, MySQL, and PostgreSQL...")
    
    for ip in SERVERS:
        ip = ip.strip()
        print(f"   Checking server: {ip}")
        if not ip:
            print(f"   Skipping empty IP")
            continue
        if not check_server_health_via_api(ip):
            print(f"   Server {ip} health check failed")
            continue
        print(f"   ✅ Server {ip} is healthy")
        
        # Initialize server state
        if ip not in previous_db_status:
            previous_db_status[ip] = {"mysql": {"dbs": {}, "tables": {}}, "postgresql": {"dbs": {}, "tables": {}}}

        # Websites (temporarily disabled to avoid timeouts)
        # folders = get_website_folders_via_api(ip)
        # for folder in folders:
        #     services.append({"name": f"{folder} on {ip}", "url": f"https://{folder}", "timeout": monitoring.get("timeout", 5)})
        
        # MySQL Databases
        mysql_status = check_mysql_databases(ip)
        for db, status in mysql_status.items():
            prev = previous_db_status[ip]["mysql"]["dbs"].get(db)
            if prev != status:
                msg = (
                    f"✅ MySQL DB UP ✅\nServer: {ip}\nDatabase: {db}"
                    if status == "up"
                    else f"🚨 MySQL DB DOWN 🚨\nServer: {ip}\nDatabase: {db}"
                )
                send_whatsapp(msg + f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                previous_db_status[ip]["mysql"]["dbs"][db] = status

        # MySQL Tables
        mysql_tables = check_mysql_tables(ip)
        for db, tables in mysql_tables.items():
            for table, status in tables.items():
                key = f"{db}.{table}"
                prev = previous_db_status[ip]["mysql"]["tables"].get(key)
                if prev != status:
                    if status == "ok":
                        msg = f"✅ MySQL Table OK ✅\nServer: {ip}\nDB: {db}\nTable: {table}"
                    elif status == "corrupted":
                        msg = f"🚨 MySQL Table CORRUPTED 🚨\nServer: {ip}\nDB: {db}\nTable: {table}\n⚠️ IMMEDIATE ACTION REQUIRED ⚠️"
                    elif status == "missing":
                        msg = f"🚨 MySQL Table MISSING 🚨\nServer: {ip}\nDB: {db}\nTable: {table}\n⚠️ TABLE MAY HAVE BEEN DROPPED ⚠️"
                    else:
                        msg = f"🚨 MySQL Table ERROR 🚨\nServer: {ip}\nDB: {db}\nTable: {table}\nStatus: {status}"
                    send_whatsapp(msg + f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    previous_db_status[ip]["mysql"]["tables"][key] = status

        # PostgreSQL Databases
        postgresql_status = check_postgresql_databases(ip)
        for db, status in postgresql_status.items():
            prev = previous_db_status[ip]["postgresql"]["dbs"].get(db)
            if prev != status:
                msg = (
                    f"✅ PostgreSQL DB UP ✅\nServer: {ip}\nDatabase: {db}"
                    if status == "up"
                    else f"🚨 PostgreSQL DB DOWN 🚨\nServer: {ip}\nDatabase: {db}"
                )
                send_whatsapp(msg + f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                previous_db_status[ip]["postgresql"]["dbs"][db] = status

        # PostgreSQL Tables
        postgresql_tables = check_postgresql_tables(ip)
        for db, tables in postgresql_tables.items():
            for table, status in tables.items():
                key = f"{db}.{table}"
                prev = previous_db_status[ip]["postgresql"]["tables"].get(key)
                if prev != status:
                    if status == "ok":
                        msg = f"✅ PostgreSQL Table OK ✅\nServer: {ip}\nDB: {db}\nTable: {table}"
                    elif status == "missing":
                        msg = f"🚨 PostgreSQL Table MISSING 🚨\nServer: {ip}\nDB: {db}\nTable: {table}\n⚠️ TABLE MAY HAVE BEEN DROPPED ⚠️"
                    else:
                        msg = f"🚨 PostgreSQL Table ERROR 🚨\nServer: {ip}\nDB: {db}\nTable: {table}\nStatus: {status}"
                    send_whatsapp(msg + f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    previous_db_status[ip]["postgresql"]["tables"][key] = status

    # Websites monitoring
    for service in services:
        is_up, info = check_service(service, service.get("timeout", 5))
        url = service["url"]
        if previous_status.get(url) != is_up:
                msg = format_message(service, is_up, info)
                send_whatsapp(msg)
            previous_status[url] = is_up

# ================== Run Monitor ==================
if __name__ == "__main__":
    try:
        print("🚀 Starting Secure Multi-Server Monitor (Web + MySQL + PostgreSQL)...")
        print(f"   Monitoring servers: {SERVERS}")
        print(f"   Check interval: {monitoring.get('check_interval', 300)} seconds")
        # Run one check immediately
        monitor_services()
        print("✅ First check complete, starting monitoring loop...")
        # Schedule monitoring loop
        schedule.every(monitoring.get("check_interval", 300)).seconds.do(monitor_services)
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Server Monitor stopped by user")
        print("\n🛑 Server Monitor stopped by user")

