#!/usr/bin/env python3
"""
IMMEDIATE Ubuntu Server Monitor
- Monitors Ubuntu Server with ULTRA-FAST detection
- Sends WhatsApp alerts IMMEDIATELY when server/services go down
- Check interval: 5 seconds (configurable)
- Timeout: 5 seconds
- Monitors: Server health, MySQL, PostgreSQL, MongoDB services
- System resources: CPU, Memory, Disk
"""

import os
import time
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from twilio.rest import Client

# ==============================
# Load ENV
# ==============================
load_dotenv()

# ULTRA-FAST monitoring intervals from .env
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 5))  # Check every 5 seconds
TIMEOUT = int(os.getenv("TIMEOUT", 3))  # 3 second timeout
WARNING_TIMEOUT = float(os.getenv("WARNING_TIMEOUT", 2.0))  # 2 seconds - triggers warning
SHUTDOWN_TIMEOUT = int(os.getenv("SHUTDOWN_TIMEOUT", 10))  # 10 seconds - confirms shutdown
FAILURE_COUNT_THRESHOLD = int(os.getenv("FAILURE_COUNT_THRESHOLD", 2))  # 2 failures = down

SERVERS = os.getenv("SERVERS", "").split(",")

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("WHATSAPP_FROM_NUMBER")
TWILIO_TO = os.getenv("WHATSAPP_TO_NUMBERS", "")

# Thresholds
CPU_THRESHOLD = int(os.getenv("CPU_THRESHOLD", 85))
MEMORY_THRESHOLD = int(os.getenv("MEMORY_THRESHOLD", 85))
DISK_THRESHOLD = int(os.getenv("DISK_THRESHOLD", 90))

twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# Track last known state
last_state = {}
down_start_time = {}
failure_count = {}  # Track consecutive failures
response_times = {}  # Track response times
warning_sent = {}  # Track if warning was already sent

# ==============================
# WhatsApp Alert
# ==============================
def send_whatsapp_alert(title, body):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg_text = f"{title}\n\n{body}\nTimestamp: {timestamp}"

    numbers = [n.strip() for n in TWILIO_TO.split(",") if n.strip()]
    for to in numbers:
        try:
            msg = twilio_client.messages.create(
                body=msg_text,
                from_=TWILIO_FROM,
                to=to
            )
            logging.info(f"📩 WhatsApp sent → {to}")
        except Exception as e:
            logging.error(f"❌ WhatsApp failed to {to}: {e}")

# ==============================
# API Helpers
# ==============================
def get_api_credentials(ip):
    env_ip = ip.replace(".", "_")
    api_token = os.getenv(f"API_TOKEN_{env_ip}")
    api_endpoint = os.getenv(f"API_ENDPOINT_{env_ip}", f"http://{ip}:5000/api")
    return api_token, api_endpoint

# ==============================
# IMMEDIATE Server Health Check with 3-Level Alerts
# ==============================
def check_server_health_immediate(server):
    """Ultra-fast server health check with WARNING → URGENT → RECOVERY alerts"""
    key = f"{server}_health"
    
    try:
        token, endpoint = get_api_credentials(server)
        if not token:
            logging.error(f"No API token for {server}")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Measure response time
        start_time = time.time()
        resp = requests.get(f"{endpoint}/health", headers=headers, timeout=TIMEOUT)
        response_time = time.time() - start_time
        response_times[server] = response_time
        
        if resp.status_code == 200:
            # Server is responding
            
            # Check if response is slow (WARNING level)
            if response_time > WARNING_TIMEOUT:
                warning_key = f"{server}_slow_warning"
                if not warning_sent.get(warning_key, False):
                    send_whatsapp_alert(
                        "⚠️ [WARNING] Ubuntu Server Slow Response",
                        f"Server: {server}\nResponse Time: {response_time:.2f}s (Normal: <{WARNING_TIMEOUT}s)\nServer is STRUGGLING ⚠️\nStatus: Still responding but SLOW"
                    )
                    warning_sent[warning_key] = True
                    logging.warning(f"⚠️ WARNING: {server} slow response ({response_time:.2f}s)")
            else:
                # Response time is normal - clear warning if it was sent
                warning_key = f"{server}_slow_warning"
                if warning_sent.get(warning_key, False):
                    send_whatsapp_alert(
                        "✅ [Server Response Normal]",
                        f"Server: {server}\nResponse Time: {response_time:.2f}s\nServer performance RESTORED ✅"
                    )
                    warning_sent[warning_key] = False
                    logging.info(f"✅ {server} response time normalized")
            
            # Server is UP - check if recovering from DOWN state
            if last_state.get(key) == "DOWN":
                down_duration = 0
                if server in down_start_time:
                    down_duration = int(time.time() - down_start_time[server])
                    del down_start_time[server]
                
                # RECOVERY ALERT
                send_whatsapp_alert(
                    "✅ [RECOVERY] Ubuntu Server UP",
                    f"Server: {server}\nUbuntu Server RECOVERED ✅\nDowntime: {down_duration} seconds\nStatus: BACK ONLINE"
                )
                logging.info(f"✅ RECOVERY: {server} is BACK UP (was down {down_duration}s)")
            
            # Reset failure counter
            failure_count[server] = 0
            last_state[key] = "UP"
            
        else:
            # Non-200 status code
            handle_server_warning(server, f"HTTP {resp.status_code}", response_time)
            
    except requests.exceptions.Timeout:
        handle_server_warning(server, "Connection timeout", TIMEOUT)
    except requests.exceptions.ConnectionError:
        handle_server_down_immediate(server, "Connection refused")
    except Exception as e:
        handle_server_warning(server, str(e)[:50], None)

def handle_server_warning(server, error, response_time):
    """Handle server warning - server is struggling but not down yet"""
    key = f"{server}_health"
    
    # Increment failure count
    failure_count[server] = failure_count.get(server, 0) + 1
    
    # If first failure or warning not sent yet, send WARNING
    if failure_count[server] == 1 and not warning_sent.get(f"{server}_warning", False):
        # WARNING ALERT - Server is struggling
        time_info = f"Response time: {response_time:.2f}s" if response_time else f"Error: {error}"
        send_whatsapp_alert(
            "⚠️ [WARNING] Ubuntu Server Issues Detected",
            f"Server: {server}\n{time_info}\nServer is STRUGGLING ⚠️\nStatus: Still UP but having issues\nMonitoring closely..."
        )
        warning_sent[f"{server}_warning"] = True
        logging.warning(f"⚠️ WARNING: {server} is struggling - {error}")
    
    # If multiple consecutive failures, escalate to DOWN
    if failure_count[server] >= FAILURE_COUNT_THRESHOLD:
        handle_server_down_immediate(server, error)

def handle_server_down_immediate(server, error):
    """Handle confirmed server down - send URGENT alert"""
    key = f"{server}_health"
    
    if last_state.get(key) != "DOWN":
        # Record when server went down
        if server not in down_start_time:
            down_start_time[server] = time.time()
        
        # URGENT ALERT - Server is DOWN
        send_whatsapp_alert(
            "🚨 [URGENT] Ubuntu Server DOWN",
            f"Server: {server}\nUbuntu Server CONFIRMED DOWN ❌\nError: {error}\n🔴 IMMEDIATE ATTENTION REQUIRED! 🔴\nFailures: {failure_count.get(server, 0)}"
        )
        
        last_state[key] = "DOWN"
        warning_sent[f"{server}_warning"] = False  # Reset warning flag
        logging.error(f"🚨 URGENT: {server} is CONFIRMED DOWN - {error}")

# Database service checking removed - moved to database_monitor.py for better organization

# ==============================
# IMMEDIATE System Resource Check
# ==============================
def check_system_resources_immediate(server):
    """Check CPU, Memory, Disk instantly"""
    try:
        token, endpoint = get_api_credentials(server)
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{endpoint}/system-metrics", headers=headers, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            metrics = resp.json()
            
            # CPU Check
            cpu = metrics.get("cpu_percent", 0)
            if cpu >= CPU_THRESHOLD:
                key = f"{server}_cpu_high"
                if not last_state.get(key, False):
                    send_whatsapp_alert(
                        "🚨 [HIGH CPU]",
                        f"Server: {server}\nCPU: {cpu}%\nThreshold: {CPU_THRESHOLD}%\n⚠️ ACTION REQUIRED!"
                    )
                    last_state[key] = True
                    logging.warning(f"🚨 CPU HIGH on {server}: {cpu}%")
            else:
                key = f"{server}_cpu_high"
                if last_state.get(key, False):
                    send_whatsapp_alert(
                        "✅ [CPU Normal]",
                        f"Server: {server}\nCPU: {cpu}%\nStatus: RESOLVED ✅"
                    )
                    last_state[key] = False
                    logging.info(f"✅ CPU normal on {server}: {cpu}%")
            
            # Memory Check
            memory = metrics.get("memory_percent", 0)
            if memory >= MEMORY_THRESHOLD:
                key = f"{server}_memory_high"
                if not last_state.get(key, False):
                    send_whatsapp_alert(
                        "🚨 [HIGH MEMORY]",
                        f"Server: {server}\nMemory: {memory}%\nThreshold: {MEMORY_THRESHOLD}%\n⚠️ ACTION REQUIRED!"
                    )
                    last_state[key] = True
                    logging.warning(f"🚨 MEMORY HIGH on {server}: {memory}%")
            else:
                key = f"{server}_memory_high"
                if last_state.get(key, False):
                    send_whatsapp_alert(
                        "✅ [Memory Normal]",
                        f"Server: {server}\nMemory: {memory}%\nStatus: RESOLVED ✅"
                    )
                    last_state[key] = False
                    logging.info(f"✅ Memory normal on {server}: {memory}%")
            
            # Disk Check
            disk = metrics.get("disk_percent", 0)
            if disk >= DISK_THRESHOLD:
                key = f"{server}_disk_high"
                if not last_state.get(key, False):
                    send_whatsapp_alert(
                        "🚨 [HIGH DISK]",
                        f"Server: {server}\nDisk: {disk}%\nFree: {metrics.get('disk_free_gb', 0)}GB\nThreshold: {DISK_THRESHOLD}%\n⚠️ ACTION REQUIRED!"
                    )
                    last_state[key] = True
                    logging.warning(f"🚨 DISK HIGH on {server}: {disk}%")
            else:
                key = f"{server}_disk_high"
                if last_state.get(key, False):
                    send_whatsapp_alert(
                        "✅ [Disk Normal]",
                        f"Server: {server}\nDisk: {disk}%\nStatus: RESOLVED ✅"
                    )
                    last_state[key] = False
                    logging.info(f"✅ Disk normal on {server}: {disk}%")
                    
    except Exception as e:
        logging.debug(f"Resource check failed for {server}: {e}")

# ==============================
# Main IMMEDIATE Monitoring Loop
# ==============================
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("="*60)
    print("🚀 IMMEDIATE Ubuntu Server Monitor")
    print("="*60)
    print(f"⚡ Check interval: {CHECK_INTERVAL} seconds")
    print(f"⚡ Timeout: {TIMEOUT} seconds")
    print(f"⚡ Shutdown detection: {SHUTDOWN_TIMEOUT} seconds")
    print(f"📊 Thresholds: CPU {CPU_THRESHOLD}%, Memory {MEMORY_THRESHOLD}%, Disk {DISK_THRESHOLD}%")
    print(f"🖥️  Servers: {', '.join([s.strip() for s in SERVERS if s.strip()])}")
    print("="*60)
    print("")
    
    logging.info("✅ Ultra-fast monitoring started!")
    logging.info(f"   Checking every {CHECK_INTERVAL} seconds...")

    try:
        while True:
            for server in SERVERS:
                server = server.strip()
                if not server:
                    continue
                
                # IMMEDIATE checks
                check_server_health_immediate(server)
                check_system_resources_immediate(server)
            
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        logging.info("🛑 Ultra-fast monitor stopped by user")
        print("\n🛑 Monitor stopped by user")

