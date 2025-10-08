#!/usr/bin/env python3
"""
System Resource Monitor - Monitors CPU, Memory, and Disk usage
Sends WhatsApp alerts when thresholds are exceeded
Monitors: CPU usage, Memory usage, Disk usage, Load average

Author: AI Assistant
Date: 2025
"""

import json, logging, requests, os, schedule, time, psutil
from datetime import datetime
from logging.handlers import RotatingFileHandler
from whatsapp_notifier import WhatsAppNotifier
from dotenv import load_dotenv

# ================== Load Environment Variables ==================
load_dotenv()
SERVERS = os.getenv("SERVERS", "").split(",")

# ================== Load Config from Environment ==================
from config_helper import get_config, SYSTEM_MONITORING

config = get_config()
system_monitoring = SYSTEM_MONITORING
whatsapp_cfg = config["whatsapp"]

# Override WhatsApp/Twilio values from .env
whatsapp_cfg["account_sid"] = os.getenv("TWILIO_ACCOUNT_SID", whatsapp_cfg.get("account_sid", ""))
whatsapp_cfg["auth_token"] = os.getenv("TWILIO_AUTH_TOKEN", whatsapp_cfg.get("auth_token", ""))
whatsapp_cfg["from_number"] = os.getenv("WHATSAPP_FROM_NUMBER", whatsapp_cfg.get("from_number", ""))
env_to_numbers = os.getenv("WHATSAPP_TO_NUMBERS")
if env_to_numbers:
    whatsapp_cfg["to_numbers"] = [n.strip() for n in env_to_numbers.split(",") if n.strip()]

# ================== Logging Setup ==================
handler = RotatingFileHandler("system_monitor.log", maxBytes=10*1024*1024, backupCount=5)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[handler, logging.StreamHandler()])
logger = logging.getLogger()

# ================== WhatsApp Notifier ==================
whatsapp_notifier = WhatsAppNotifier(config)

# Track previous alert states to avoid spam
previous_alerts = {}  # { "server_ip:metric": alert_sent }

# ================== WhatsApp Helper ==================
def send_whatsapp(message):
    try:
        if whatsapp_notifier.send_message(message):
            logger.info("📩 System alert sent via WhatsApp")
    except Exception as e:
        logger.error(f"WhatsApp error: {e}")

# ================== API Helpers ==================
def get_server_api_credentials(ip):
    env_ip = ip.replace(".", "_")
    api_token = os.getenv(f"API_TOKEN_{env_ip}")
    api_endpoint = os.getenv(f"API_ENDPOINT_{env_ip}", f"http://{ip}:5000/api")
    return api_token, api_endpoint

def get_system_metrics_from_api(ip):
    """Get system metrics from remote server API"""
    try:
        api_token, api_endpoint = get_server_api_credentials(ip)
        if not api_token:
            return None
        headers = {"Authorization": f"Bearer {api_token}"}
        resp = requests.get(f"{api_endpoint}/system-metrics", headers=headers, timeout=10)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        logger.error(f"Failed to get system metrics from {ip}: {e}")
        return None

# ================== Local System Metrics ==================
def get_local_system_metrics():
    """Get system metrics for local machine"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "load_average_1min": round(load_avg[0], 2),
            "load_average_5min": round(load_avg[1], 2),
            "load_average_15min": round(load_avg[2], 2)
        }
    except Exception as e:
        logger.error(f"Failed to get local metrics: {e}")
        return None

# ================== Threshold Checker ==================
def check_thresholds(ip, metrics):
    """Check if any metrics exceed configured thresholds"""
    global previous_alerts
    
    if not metrics:
        return
    
    thresholds = system_monitoring.get("thresholds", {})
    cpu_threshold = thresholds.get("cpu_percent", 85)
    memory_threshold = thresholds.get("memory_percent", 85)
    disk_threshold = thresholds.get("disk_percent", 90)
    
    # CPU Check
    cpu = metrics.get("cpu_percent", 0)
    if cpu >= cpu_threshold:
        alert_key = f"{ip}:cpu:high"
        if not previous_alerts.get(alert_key, False):
            msg = f"🚨 HIGH CPU USAGE 🚨\nServer: {ip}\nCurrent CPU: {cpu}%\nThreshold: {cpu_threshold}%\n⚠️ ACTION REQUIRED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            send_whatsapp(msg)
            previous_alerts[alert_key] = True
            logger.warning(f"🚨 CPU ALERT for {ip}: {cpu}% (threshold: {cpu_threshold}%)")
    else:
        alert_key = f"{ip}:cpu:high"
        if previous_alerts.get(alert_key, False):
            msg = f"✅ CPU RESOLVED ✅\nServer: {ip}\nCurrent CPU: {cpu}%\nThreshold: {cpu_threshold}%\nStatus: NORMAL\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            send_whatsapp(msg)
            previous_alerts[alert_key] = False
            logger.info(f"✅ CPU RESOLVED for {ip}: {cpu}%")
    
    # Memory Check
    memory = metrics.get("memory_percent", 0)
    if memory >= memory_threshold:
        alert_key = f"{ip}:memory:high"
        if not previous_alerts.get(alert_key, False):
            msg = f"🚨 HIGH MEMORY USAGE 🚨\nServer: {ip}\nCurrent Memory: {memory}%\nUsed: {metrics.get('memory_used_gb', 0)}GB / {metrics.get('memory_total_gb', 0)}GB\nThreshold: {memory_threshold}%\n⚠️ ACTION REQUIRED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            send_whatsapp(msg)
            previous_alerts[alert_key] = True
            logger.warning(f"🚨 MEMORY ALERT for {ip}: {memory}% (threshold: {memory_threshold}%)")
    else:
        alert_key = f"{ip}:memory:high"
        if previous_alerts.get(alert_key, False):
            msg = f"✅ MEMORY RESOLVED ✅\nServer: {ip}\nCurrent Memory: {memory}%\nUsed: {metrics.get('memory_used_gb', 0)}GB / {metrics.get('memory_total_gb', 0)}GB\nThreshold: {memory_threshold}%\nStatus: NORMAL\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            send_whatsapp(msg)
            previous_alerts[alert_key] = False
            logger.info(f"✅ MEMORY RESOLVED for {ip}: {memory}%")
    
    # Disk Check
    disk = metrics.get("disk_percent", 0)
    if disk >= disk_threshold:
        alert_key = f"{ip}:disk:high"
        if not previous_alerts.get(alert_key, False):
            msg = f"🚨 HIGH DISK USAGE 🚨\nServer: {ip}\nCurrent Disk: {disk}%\nUsed: {metrics.get('disk_used_gb', 0)}GB / {metrics.get('disk_total_gb', 0)}GB\nFree: {metrics.get('disk_free_gb', 0)}GB\nThreshold: {disk_threshold}%\n⚠️ ACTION REQUIRED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            send_whatsapp(msg)
            previous_alerts[alert_key] = True
            logger.warning(f"🚨 DISK ALERT for {ip}: {disk}% (threshold: {disk_threshold}%)")
    else:
        alert_key = f"{ip}:disk:high"
        if previous_alerts.get(alert_key, False):
            msg = f"✅ DISK RESOLVED ✅\nServer: {ip}\nCurrent Disk: {disk}%\nUsed: {metrics.get('disk_used_gb', 0)}GB / {metrics.get('disk_total_gb', 0)}GB\nFree: {metrics.get('disk_free_gb', 0)}GB\nThreshold: {disk_threshold}%\nStatus: NORMAL\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            send_whatsapp(msg)
            previous_alerts[alert_key] = False
            logger.info(f"✅ DISK RESOLVED for {ip}: {disk}%")

# ================== Main Monitor ==================
def monitor_system_resources():
    logger.info("💻 Checking system resources...")
    
    # Check remote servers only (skip local)
    for ip in SERVERS:
        ip = ip.strip()
        if not ip:
            continue
        
        metrics = get_system_metrics_from_api(ip)
        if metrics:
            logger.info(f"   {ip}: CPU {metrics.get('cpu_percent', 0)}%, Memory {metrics.get('memory_percent', 0)}%, Disk {metrics.get('disk_percent', 0)}%")
            check_thresholds(ip, metrics)
        else:
            logger.warning(f"   Could not get metrics from {ip}")
    
    logger.info("✅ System check complete")

# ================== Run Monitor ==================
if __name__ == "__main__":
    try:
        print("💻 System Resource Monitor Started")
        print(f"   Monitoring: {len([s for s in SERVERS if s.strip()])} remote servers")
        print(f"   Thresholds: CPU {system_monitoring.get('thresholds', {}).get('cpu_percent', 85)}%, Memory {system_monitoring.get('thresholds', {}).get('memory_percent', 85)}%, Disk {system_monitoring.get('thresholds', {}).get('disk_percent', 90)}%")
        print(f"   Check interval: {system_monitoring.get('check_interval', 60)} seconds")
        print("")
        
        monitor_system_resources()
        schedule.every(system_monitoring.get('check_interval', 60)).seconds.do(monitor_system_resources)
        
        print("✅ Monitoring started!")
        print("   Press Ctrl+C to stop")
        print("")
        
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 System Monitor stopped by user")
        print("\n🛑 System Monitor stopped by user")
