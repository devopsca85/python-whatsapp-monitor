#!/usr/bin/env python3
"""
Server API - Provides system metrics endpoint
Supports: CPU, Memory, Disk monitoring
Runs on remote servers to report system health
"""

import os, psutil, time, threading, uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401
        try:
            token = auth_header.split(' ')[1]
            expected_token = os.getenv("API_TOKEN")
            if not expected_token or token != expected_token:
                return jsonify({"error": "Invalid token"}), 401
        except:
            return jsonify({"error": "Invalid authorization format"}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_system_metrics():
    """Get system metrics for dashboard"""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_total = memory.total
        memory_available = memory.available
        memory_used = memory.used
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_total = disk.total
        disk_free = disk.free
        disk_used = disk.used
        
        # Boot time and uptime
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.now().timestamp() - boot_time
        uptime_days = int(uptime_seconds // 86400)
        uptime_hours = int((uptime_seconds % 86400) // 3600)
        uptime = f"{uptime_days} days, {uptime_hours} hours"
        
        return {
            "status": "healthy",
            "cpu_percent": round(cpu_percent, 1),
            "cpu_count": cpu_count,
            "load_average": [round(x, 2) for x in load_avg],
            "memory_percent": round(memory_percent, 1),
            "memory_total": memory_total,
            "memory_available": memory_available,
            "memory_used": memory_used,
            "disk_percent": round(disk_percent, 1),
            "disk_total": disk_total,
            "disk_free": disk_free,
            "disk_used": disk_used,
            "uptime": uptime,
            "boot_time": datetime.fromtimestamp(boot_time).isoformat()
        }
    except Exception as e:
        app.logger.error(f"Error getting system metrics: {str(e)}")
        return {
            "status": "error",
            "cpu_percent": 0,
            "cpu_count": 1,
            "load_average": [0, 0, 0],
            "memory_percent": 0,
            "memory_total": 0,
            "memory_available": 0,
            "memory_used": 0,
            "disk_percent": 0,
            "disk_total": 0,
            "disk_free": 0,
            "disk_used": 0,
            "uptime": "Unknown",
            "boot_time": ""
        }

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint - no authentication required"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# Dashboard endpoints
@app.route('/api/dashboard/summary', methods=['GET'])
@require_auth
def dashboard_summary():
    """Get complete dashboard summary with all servers, databases, websites, and alerts"""
    try:
        # Get system metrics
        system_data = get_system_metrics()
        
        # Get websites
        websites_data = get_websites_data()
        
        # Create basic summary with system data
        summary = {
            "servers": [
                {
                    "ip": "135.148.164.94",  # This is the staging server
                    "name": "Old Staging Server",
                    "status": "up" if system_data.get("status") == "healthy" else "down",
                    "cpu": system_data.get("cpu_percent", 0),
                    "ram": system_data.get("memory_percent", 0),
                    "disk": system_data.get("disk_percent", 0),
                    "uptime": system_data.get("uptime", "Unknown"),
                    "lastCheck": datetime.now().isoformat(),
                    "responseTime": 50,  # Mock response time
                    "websites": [
                        check_website_status_cached(website)
                        for website in websites_data
                    ],
                    "services": get_real_services_status()
                }
            ],
            "alerts": alerts_storage[-10:],  # Last 10 alerts
            "stats": {
                "totalServers": 1,  # Single server (this one)
                "serversUp": 1,  # This server
                "serversDown": 0,
                "serversSlow": 0,
                "totalAlerts24h": len([a for a in alerts_storage if (datetime.now() - datetime.fromisoformat(a["timestamp"])).days < 1]),
                "criticalAlerts": len([a for a in alerts_storage if a["type"] == "critical"]),
                "warningAlerts": len([a for a in alerts_storage if a["type"] == "warning"]),
                "recoveryAlerts": len([a for a in alerts_storage if a["type"] == "recovery"]),
                "avgUptime": 99.5
            }
        }
        
        return jsonify(summary)
        
    except Exception as e:
        app.logger.error(f"Error in dashboard_summary: {str(e)}")
        return jsonify({"error": "Failed to get dashboard summary"}), 500

# Global alerts storage (in production, use a database)
alerts_storage = []

def send_website_status_alert(website_url, old_status, new_status, response_time=None, error=None):
    """Send alert to dashboard when website status changes"""
    try:
        alert_type = "recovery" if new_status == "up" and old_status != "up" else "warning" if new_status == "slow" else "critical" if new_status == "down" else "info"
        severity = "high" if new_status == "down" else "medium" if new_status == "slow" else "low"
        
        if new_status == "up" and old_status != "up":
            message = f"✅ Website recovered: {website_url} is now UP"
        elif new_status == "down":
            message = f"🚨 Website down: {website_url} is DOWN"
            if error:
                message += f" - {error}"
        elif new_status == "slow":
            message = f"⚠️ Website slow: {website_url} is responding slowly ({response_time}ms)"
        else:
            message = f"ℹ️ Website status: {website_url} is {new_status.upper()}"
        
        alert = {
            "id": f"website_{website_url}_{uuid.uuid4().hex[:12]}",
            "type": alert_type,
            "severity": severity,
            "category": "website",
            "message": message,
            "server": "135.148.164.94",
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to alerts storage
        alerts_storage.append(alert)
        
        # Keep only last 1000 alerts
        if len(alerts_storage) > 1000:
            alerts_storage[:] = alerts_storage[-1000:]
            
        app.logger.info(f"Website status alert: {message}")
        
    except Exception as e:
        app.logger.error(f"Error sending website status alert: {str(e)}")

def send_service_status_alert(service_name, old_status, new_status):
    """Send alert to dashboard when service status changes"""
    try:
        alert_type = "recovery" if new_status == "up" and old_status != "up" else "critical" if new_status == "down" else "info"
        severity = "high" if new_status == "down" else "low"
        
        if new_status == "up" and old_status != "up":
            message = f"✅ Service recovered: {service_name.upper()} is now UP"
        elif new_status == "down":
            message = f"🚨 Service down: {service_name.upper()} is DOWN"
        else:
            message = f"ℹ️ Service status: {service_name.upper()} is {new_status.upper()}"
        
        alert = {
            "id": f"service_{service_name}_{uuid.uuid4().hex[:12]}",
            "type": alert_type,
            "severity": severity,
            "category": "database",
            "message": message,
            "server": "135.148.164.94",
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to alerts storage
        alerts_storage.append(alert)
        
        # Keep only last 1000 alerts
        if len(alerts_storage) > 1000:
            alerts_storage[:] = alerts_storage[-1000:]
            
        app.logger.info(f"Service status alert: {message}")
        
    except Exception as e:
        app.logger.error(f"Error sending service status alert: {str(e)}")

def monitor_websites_background():
    """Background function to monitor websites and detect changes"""
    try:
        websites_data = get_websites_data()
        app.logger.info(f"Background monitoring: Checking {len(websites_data)} websites")
        
        for website in websites_data:
            try:
                # This will automatically detect status changes and send alerts
                check_website_status_cached(website)
            except Exception as e:
                app.logger.error(f"Error checking website {website}: {str(e)}")
                
    except Exception as e:
        app.logger.error(f"Error in background website monitoring: {str(e)}")

def start_background_monitoring():
    """Start background monitoring thread"""
    def run_monitor():
        while True:
            try:
                monitor_websites_background()
                time.sleep(15)  # Wait 15 seconds before next check
            except Exception as e:
                app.logger.error(f"Error in background monitoring: {str(e)}")
                time.sleep(15)  # Wait 15 seconds before retry
    
    # Start background thread
    monitor_thread = threading.Thread(target=run_monitor, daemon=True)
    monitor_thread.start()
    app.logger.info("Background website monitoring started")

# Website status cache to avoid checking websites on every request
website_status_cache = {}
CACHE_DURATION = 10  # Cache for 10 seconds for faster updates

# Service status cache to track changes
service_status_cache = {}
SERVICE_CACHE_DURATION = 5  # Cache for 5 seconds for faster service monitoring

@app.route('/api/dashboard/alerts', methods=['GET'])
@require_auth
def dashboard_alerts():
    """Get recent alerts (populated by monitoring scripts)"""
    try:
        # Return alerts from storage
        return jsonify({
            "alerts": alerts_storage[-50:],  # Last 50 alerts
            "total": len(alerts_storage),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error in dashboard_alerts: {str(e)}")
        return jsonify({"error": "Failed to get alerts"}), 500

@app.route('/api/dashboard/alert', methods=['POST'])
@require_auth
def add_alert():
    """Add new alert from monitoring scripts"""
    try:
        data = request.get_json()
        
        # Create alert object
        alert = {
            "id": f"alert_{len(alerts_storage) + 1}_{int(datetime.now().timestamp())}",
            "type": data.get("type", "info"),  # critical, warning, info, recovery
            "severity": data.get("severity", "low"),  # high, medium, low
            "category": data.get("category", "system"),  # server, database, website
            "message": data.get("message", ""),
            "server": data.get("server", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to storage
        alerts_storage.append(alert)
        
        # Keep only last 1000 alerts
        if len(alerts_storage) > 1000:
            alerts_storage[:] = alerts_storage[-1000:]
        
        app.logger.info(f"New alert added: {alert['message']}")
        
        return jsonify({
            "status": "success",
            "alert_id": alert["id"],
            "message": "Alert added successfully"
        })
        
    except Exception as e:
        app.logger.error(f"Error adding alert: {str(e)}")
        return jsonify({"error": "Failed to add alert"}), 500

@app.route('/api/dashboard/server/<server_ip>', methods=['GET'])
@require_auth
def get_server_details(server_ip):
    """Get detailed information for a specific server"""
    try:
        if server_ip == "135.148.164.94":  # This is the staging server
            # Get system metrics
            system_data = get_system_metrics()
            
            # Get websites
            websites_data = get_websites_data()
            
            server_details = {
                "ip": server_ip,
                "name": "Old Staging Server",
                "status": "up" if system_data.get("status") == "healthy" else "down",
                "system": {
                    "cpu": {
                        "current": system_data.get("cpu_percent", 0),
                        "cores": system_data.get("cpu_count", 1),
                        "load": system_data.get("load_average", [0, 0, 0])
                    },
                    "memory": {
                        "current": system_data.get("memory_percent", 0),
                        "total": system_data.get("memory_total", 0),
                        "available": system_data.get("memory_available", 0),
                        "used": system_data.get("memory_used", 0)
                    },
                    "disk": {
                        "current": system_data.get("disk_percent", 0),
                        "total": system_data.get("disk_total", 0),
                        "free": system_data.get("disk_free", 0),
                        "used": system_data.get("disk_used", 0)
                    },
                    "uptime": system_data.get("uptime", "Unknown"),
                    "boot_time": system_data.get("boot_time", ""),
                    "lastCheck": datetime.now().isoformat()
                },
                "databases": {
                    "mysql": {
                        "status": check_mysql_service(),
                        "databases": {},
                        "lastCheck": datetime.now().isoformat()
                    },
                    "postgresql": {
                        "status": "not_available",
                        "databases": {},
                        "lastCheck": datetime.now().isoformat()
                    },
                    "mongodb": {
                        "status": "not_available",
                        "databases": {},
                        "lastCheck": datetime.now().isoformat()
                    }
                },
                "websites": [
                    check_website_status_cached(website)
                    for website in websites_data
                ],
                "alerts": alerts_storage[-10:],  # Last 10 alerts
                "lastUpdate": datetime.now().isoformat()
            }
            
            return jsonify(server_details)
            
        else:
            # For other servers, return not found
            return jsonify({"error": "Server not found"}), 404
            
    except Exception as e:
        app.logger.error(f"Error in get_server_details: {str(e)}")
        return jsonify({"error": "Failed to get server details"}), 500

def get_websites_data():
    """Get websites from /var/www/* folders and custom URLs from environment"""
    try:
        import glob
        websites = []
        
        # 1. Get custom websites from environment variable (comma-separated URLs)
        custom_websites = os.getenv("CUSTOM_WEBSITES", "")
        if custom_websites:
            for url in custom_websites.split(","):
                url = url.strip()
                if url:
                    # Extract domain from URL (remove http://, https://, trailing slash)
                    domain = url.replace("http://", "").replace("https://", "").split("/")[0]
                    if domain and domain not in websites:
                        websites.append(domain)
                        app.logger.info(f"Added custom website from env: {domain}")
        
        # 2. Auto-discover from /var/www/* folders
        www_paths = ["/var/www/*", "/var/www/html/*"]
        app.logger.info(f"Searching for websites in paths: {www_paths}")
        
        for path_pattern in www_paths:
            try:
                folders = glob.glob(path_pattern)
                app.logger.debug(f"Found {len(folders)} folders in {path_pattern}")
                for folder in folders:
                    if os.path.isdir(folder):
                        folder_name = os.path.basename(folder)
                        # Only .com and .in domains
                        if (folder_name.endswith('.com') or folder_name.endswith('.in')) and folder_name not in websites:
                            websites.append(folder_name)
                            app.logger.info(f"Added website from folder: {folder_name}")
            except Exception as path_error:
                app.logger.warning(f"Error scanning path {path_pattern}: {str(path_error)}")
                continue
        
        # Remove duplicates and return simple list
        result = list(set(websites))
        app.logger.info(f"Final websites list ({len(result)}): {result}")
        return result
    except Exception as e:
        app.logger.error(f"Error in get_websites_data: {str(e)}")
        return []

def check_website_status_cached(website_name, timeout=2):
    """Check website status with caching and change detection"""
    current_time = time.time()
    cache_key = website_name
    
    # Check if we have cached data that's still valid
    old_status = None
    if cache_key in website_status_cache:
        cached_data, cache_time = website_status_cache[cache_key]
        if current_time - cache_time < CACHE_DURATION:
            # Return cached data with updated lastCheck time
            cached_data["lastCheck"] = datetime.now().isoformat()
            return cached_data
        else:
            # Cache expired, get old status for comparison
            old_status = cached_data.get("status")
    
    # If no cache or cache expired, check the website
    status_data = check_website_status(website_name, timeout)
    new_status = status_data.get("status")
    
    # Check for status changes and send alerts
    if old_status and old_status != new_status:
        send_website_status_alert(
            status_data.get("url", website_name),
            old_status,
            new_status,
            status_data.get("responseTime"),
            status_data.get("error")
        )
    
    # Cache the result
    website_status_cache[cache_key] = (status_data, current_time)
    
    return status_data

def get_websites_with_mock_status(websites_data):
    """Get websites with mock status for faster response"""
    return [
        {
            "url": f"http://{website}" if not website.startswith("http") else website,
            "status": "up",  # Mock status for faster response
            "responseTime": 150,  # Mock response time
            "statusCode": 200,
            "lastCheck": datetime.now().isoformat()
        }
        for website in websites_data
    ]

def check_mysql_service():
    """Check MySQL service status"""
    try:
        import subprocess
        result = subprocess.run(['systemctl', 'is-active', 'mysql'], 
                              capture_output=True, text=True, timeout=5)
        status = result.stdout.strip()
        return "up" if status == "active" else "down"
    except Exception as e:
        app.logger.error(f"Error checking MySQL service: {str(e)}")
        return "down"

def check_postgresql_service():
    """Check PostgreSQL service status (Docker container)"""
    try:
        import subprocess
        # Try with sudo first, then without
        try:
            result = subprocess.run(['sudo', 'docker', 'ps', '--filter', 'name=postgres-monitor', '--format', '{{.Status}}'], 
                                  capture_output=True, text=True, timeout=5)
        except:
            result = subprocess.run(['docker', 'ps', '--filter', 'name=postgres-monitor', '--format', '{{.Status}}'], 
                                  capture_output=True, text=True, timeout=5)
        
        status = result.stdout.strip()
        app.logger.info(f"PostgreSQL container status: '{status}'")
        return "up" if "Up" in status and status else "down"
    except Exception as e:
        app.logger.error(f"Error checking PostgreSQL service: {str(e)}")
        return "down"

def check_mongodb_service():
    """Check MongoDB service status (Docker container)"""
    try:
        import subprocess
        # Try with sudo first, then without
        try:
            result = subprocess.run(['sudo', 'docker', 'ps', '--filter', 'name=mongodb-monitor', '--format', '{{.Status}}'], 
                                  capture_output=True, text=True, timeout=5)
        except:
            result = subprocess.run(['docker', 'ps', '--filter', 'name=mongodb-monitor', '--format', '{{.Status}}'], 
                                  capture_output=True, text=True, timeout=5)
        
        status = result.stdout.strip()
        app.logger.info(f"MongoDB container status: '{status}'")
        return "up" if "Up" in status and status else "down"
    except Exception as e:
        app.logger.error(f"Error checking MongoDB service: {str(e)}")
        return "down"

def get_real_services_status():
    """Get real-time status of all database services with change detection"""
    current_time = time.time()
    
    # Check each service and detect changes
    services = {}
    
    for service_name, check_function in [
        ("mysql", check_mysql_service),
        ("postgresql", check_postgresql_service),
        ("mongodb", check_mongodb_service)
    ]:
        # Get current status
        current_status = check_function()
        
        # Check for status changes
        cache_key = f"service_{service_name}"
        if cache_key in service_status_cache:
            old_status, cache_time = service_status_cache[cache_key]
            if current_time - cache_time < SERVICE_CACHE_DURATION:
                # Use cached status if still valid
                current_status = old_status
            elif old_status != current_status:
                # Status changed, send alert
                send_service_status_alert(service_name, old_status, current_status)
        
        # Update cache
        service_status_cache[cache_key] = (current_status, current_time)
        
        # Add to services dict
        if service_name == "mongodb":
            services[service_name] = {
                "status": current_status,
                "databases": 0,  # Will be updated by monitoring scripts
                "collections": 0
            }
        else:
            services[service_name] = {
                "status": current_status,
                "databases": 0,  # Will be updated by monitoring scripts
                "tables": 0
            }
    
    return services

def check_website_status(website_name, timeout=2):
    """Check the actual status of a website with shorter timeout"""
    try:
        import requests
        from requests.exceptions import Timeout, ConnectionError
        
        # Handle URLs that may already include http:// or https://
        if website_name.startswith("http://") or website_name.startswith("https://"):
            url = website_name
        else:
            # Try HTTPS first, then HTTP if that fails
            url = f"https://{website_name}"
        
        start_time = time.time()
        try:
            response = requests.get(url, timeout=timeout, verify=False, allow_redirects=True)
            response_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
            
            if 200 <= response.status_code < 300:
                status = "up"
            elif 300 <= response.status_code < 400:
                status = "up"  # Redirects are considered up
            elif response.status_code >= 500:
                status = "down"
            else:
                status = "down"
                
            return {
                "url": url,
                "status": status,
                "responseTime": response_time,
                "statusCode": response.status_code,
                "lastCheck": datetime.now().isoformat()
            }
        except ConnectionError:
            # Try HTTP if HTTPS fails (for websites without SSL)
            if url.startswith("https://"):
                http_url = url.replace("https://", "http://")
                try:
                    response = requests.get(http_url, timeout=timeout, verify=False, allow_redirects=True)
                    response_time = int((time.time() - start_time) * 1000)
                    status = "up" if 200 <= response.status_code < 400 else "down"
                    return {
                        "url": http_url,
                        "status": status,
                        "responseTime": response_time,
                        "statusCode": response.status_code,
                        "lastCheck": datetime.now().isoformat()
                    }
                except:
                    pass
            
            # If HTTP also fails, return down status
            return {
                "url": url if url.startswith("http") else f"http://{website_name}",
                "status": "down",
                "responseTime": 0,
                "statusCode": None,
                "lastCheck": datetime.now().isoformat(),
                "error": "Connection failed"
            }
        except Timeout:
            return {
                "url": url if url.startswith("http") else f"http://{website_name}",
                "status": "slow",
                "responseTime": timeout * 1000,
                "statusCode": None,
                "lastCheck": datetime.now().isoformat(),
                "error": "Request timeout"
            }
    except Exception as e:
        return {
            "url": website_name if website_name.startswith("http") else f"http://{website_name}",
            "status": "down",
            "responseTime": 0,
            "statusCode": None,
            "lastCheck": datetime.now().isoformat(),
            "error": str(e)
        }

@app.route('/api/websites', methods=['GET'])
@require_auth
def get_websites():
    """Get .com and .in website folders from /var/www/html/*"""
    websites = get_websites_data()
    return jsonify({"websites": websites})

@app.route('/api/system-metrics', methods=['GET'])
@require_auth
def system_metrics():
    """Get current system resource usage"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        
        return jsonify({
            "cpu_percent": round(cpu_percent, 2),
            "cpu_count": psutil.cpu_count(),
            "memory_percent": round(memory.percent, 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": round(disk.percent, 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "load_average_1min": round(load_avg[0], 2),
            "load_average_5min": round(load_avg[1], 2),
            "load_average_15min": round(load_avg[2], 2),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/database-services-status', methods=['GET'])
@require_auth
def database_services_status():
    """Check if MySQL, PostgreSQL, MongoDB services are running"""
    services = {}
    
    # Check MySQL service
    try:
        import pymysql
        mysql_host = os.getenv("MYSQL_HOST", "localhost")
        mysql_user = os.getenv("MYSQL_USER", "root")
        mysql_password = os.getenv("MYSQL_PASSWORD", "")
        mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
        
        conn = pymysql.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            port=mysql_port,
            connect_timeout=3
        )
        conn.close()
        services["mysql"] = "running"
    except Exception as e:
        services["mysql"] = "down"
    
    
    # Check PostgreSQL service (Docker container)
    try:
        import psycopg2
        postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        postgres_user = os.getenv("POSTGRES_USER", "postgres")
        postgres_password = os.getenv("POSTGRES_PASSWORD", "")
        postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
        
        conn = psycopg2.connect(
            host=postgres_host,
            user=postgres_user,
            password=postgres_password,
            port=postgres_port,
            database="postgres",
            connect_timeout=3
        )
        conn.close()
        services["postgresql"] = "running"
    except Exception as e:
        services["postgresql"] = "down"
    
    # Check MongoDB service
    try:
        import pymongo
        mongo_host = os.getenv("MONGO_HOST", "localhost")
        mongo_port = int(os.getenv("MONGO_PORT", "27017"))
        mongo_user = os.getenv("MONGO_USER", "")
        mongo_password = os.getenv("MONGO_PASSWORD", "")
        
        if mongo_user and mongo_password:
            uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/"
        else:
            uri = f"mongodb://{mongo_host}:{mongo_port}/"
        
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        client.close()
        services["mongodb"] = "running"
    except Exception as e:
        services["mongodb"] = "down"
    
    services["timestamp"] = datetime.now().isoformat()
    return jsonify(services)

@app.route('/api/mysql-all-dbs-health', methods=['GET'])
@require_auth
def mysql_all_dbs_health():
    """Check health of all MySQL databases"""
    try:
        import pymysql
        mysql_host = os.getenv("MYSQL_HOST", "localhost")
        mysql_user = os.getenv("MYSQL_USER", "root")
        mysql_password = os.getenv("MYSQL_PASSWORD", "")
        mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
        
        conn = pymysql.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            port=mysql_port,
            connect_timeout=5
        )
        
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            databases = [row[0] for row in cursor.fetchall() 
                        if row[0] not in ['information_schema', 'performance_schema', 'mysql', 'sys']]
            
            db_status = {}
            for db in databases:
                try:
                    cursor.execute(f"USE `{db}`")
                    cursor.execute("SELECT 1")
                    db_status[db] = "up"
                except:
                    db_status[db] = "down"
            
            conn.close()
            return jsonify(db_status)
    except Exception as e:
        return jsonify({})

@app.route('/api/mysql-all-tables-health', methods=['GET'])
@require_auth
def mysql_all_tables_health():
    """Check health of all MySQL tables with corruption detection"""
    try:
        import pymysql
        mysql_host = os.getenv("MYSQL_HOST", "localhost")
        mysql_user = os.getenv("MYSQL_USER", "root")
        mysql_password = os.getenv("MYSQL_PASSWORD", "")
        mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
        
        conn = pymysql.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            port=mysql_port,
            connect_timeout=5
        )
        
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            databases = [row[0] for row in cursor.fetchall() 
                        if row[0] not in ['information_schema', 'performance_schema', 'mysql', 'sys']]
            
            all_tables_status = {}
            for db in databases:
                try:
                    cursor.execute(f"USE `{db}`")
                    cursor.execute("SHOW TABLES")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    db_tables_status = {}
                    for table in tables:
                        try:
                            # Basic table check
                            cursor.execute(f"SELECT COUNT(*) FROM `{table}` LIMIT 1")
                            cursor.fetchone()
                            
                            # Corruption detection using CHECK TABLE
                            cursor.execute(f"CHECK TABLE `{table}`")
                            check_result = cursor.fetchall()
                            
                            corruption_detected = False
                            for row in check_result:
                                if len(row) >= 3 and row[2] in ['Error', 'Corrupt', 'Crashed']:
                                    corruption_detected = True
                                    break
                            
                            db_tables_status[table] = "corrupted" if corruption_detected else "ok"
                            
                        except Exception as e:
                            error_str = str(e).lower()
                            if "doesn't exist" in error_str:
                                db_tables_status[table] = "missing"
                            elif "access denied" in error_str:
                                db_tables_status[table] = "access_denied"
                            elif "corrupt" in error_str or "crash" in error_str:
                                db_tables_status[table] = "corrupted"
                            else:
                                db_tables_status[table] = "error"
                    
                    all_tables_status[db] = db_tables_status
                except:
                    all_tables_status[db] = {}
            
            conn.close()
            return jsonify(all_tables_status)
    except Exception as e:
        return jsonify({})

@app.route('/api/postgresql-all-dbs-health', methods=['GET'])
@require_auth
def postgresql_all_dbs_health():
    """Check health of all PostgreSQL databases (Docker container)"""
    try:
        import psycopg2
        postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        postgres_user = os.getenv("POSTGRES_USER", "postgres")
        postgres_password = os.getenv("POSTGRES_PASSWORD", "")
        postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
        
        conn = psycopg2.connect(
            host=postgres_host,
            user=postgres_user,
            password=postgres_password,
            port=postgres_port,
            database="postgres",
            connect_timeout=5
        )
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres', 'template0', 'template1')")
            databases = [row[0] for row in cursor.fetchall()]
            
            db_status = {}
            for db in databases:
                try:
                    test_conn = psycopg2.connect(
                        host=postgres_host,
                        user=postgres_user,
                        password=postgres_password,
                        port=postgres_port,
                        database=db,
                        connect_timeout=3
                    )
                    test_conn.close()
                    db_status[db] = "up"
                except:
                    db_status[db] = "down"
            
            conn.close()
            return jsonify(db_status)
    except Exception as e:
        app.logger.error(f"PostgreSQL connection failed: {e}")
        return jsonify({})

@app.route('/api/postgresql-all-tables-health', methods=['GET'])
@require_auth
def postgresql_all_tables_health():
    """Check health of all PostgreSQL tables (Docker container)"""
    try:
        import psycopg2
        postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        postgres_user = os.getenv("POSTGRES_USER", "postgres")
        postgres_password = os.getenv("POSTGRES_PASSWORD", "")
        postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
        
        conn = psycopg2.connect(
            host=postgres_host,
            user=postgres_user,
            password=postgres_password,
            port=postgres_port,
            database="postgres",
            connect_timeout=5
        )
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres', 'template0', 'template1')")
            databases = [row[0] for row in cursor.fetchall()]
            
            all_tables_status = {}
            for db in databases:
                try:
                    db_conn = psycopg2.connect(
                        host=postgres_host,
                        user=postgres_user,
                        password=postgres_password,
                        port=postgres_port,
                        database=db,
                        connect_timeout=3
                    )
                    
                    with db_conn.cursor() as db_cursor:
                        db_cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                        tables = [row[0] for row in db_cursor.fetchall()]
                        
                        db_tables_status = {}
                        for table in tables:
                            try:
                                db_cursor.execute(f'SELECT COUNT(*) FROM "{table}" LIMIT 1')
                                db_cursor.fetchone()
                                db_tables_status[table] = "ok"
                            except Exception as e:
                                error_str = str(e).lower()
                                if "does not exist" in error_str:
                                    db_tables_status[table] = "missing"
                                elif "permission denied" in error_str:
                                    db_tables_status[table] = "access_denied"
                                else:
                                    db_tables_status[table] = "error"
                        
                        all_tables_status[db] = db_tables_status
                    db_conn.close()
                except:
                    all_tables_status[db] = {}
            
            conn.close()
            return jsonify(all_tables_status)
    except Exception as e:
        app.logger.error(f"PostgreSQL connection failed: {e}")
        return jsonify({})

@app.route('/api/mongodb-all-dbs-health', methods=['GET'])
@require_auth
def mongodb_all_dbs_health():
    """Check health of all MongoDB databases (Docker container)"""
    try:
        import pymongo
        mongo_host = os.getenv("MONGO_HOST", "localhost")
        mongo_port = int(os.getenv("MONGO_PORT", "27017"))
        mongo_user = os.getenv("MONGO_USER", "")
        mongo_password = os.getenv("MONGO_PASSWORD", "")
        
        if mongo_user and mongo_password:
            uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/"
        else:
            uri = f"mongodb://{mongo_host}:{mongo_port}/"
        
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # Get list of databases (exclude system databases)
        db_list = client.list_database_names()
        exclude_dbs = ['admin', 'config', 'local']
        databases = [db for db in db_list if db not in exclude_dbs]
        
        db_status = {}
        for db_name in databases:
            try:
                db = client[db_name]
                db.list_collection_names()  # Test access
                db_status[db_name] = "up"
            except:
                db_status[db_name] = "down"
        
        client.close()
        return jsonify(db_status)
    except Exception as e:
        app.logger.error(f"MongoDB connection failed: {e}")
        return jsonify({})

@app.route('/api/mongodb-all-collections-health', methods=['GET'])
@require_auth
def mongodb_all_collections_health():
    """Check health of all MongoDB collections (Docker container)"""
    try:
        import pymongo
        mongo_host = os.getenv("MONGO_HOST", "localhost")
        mongo_port = int(os.getenv("MONGO_PORT", "27017"))
        mongo_user = os.getenv("MONGO_USER", "")
        mongo_password = os.getenv("MONGO_PASSWORD", "")
        
        if mongo_user and mongo_password:
            uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/"
        else:
            uri = f"mongodb://{mongo_host}:{mongo_port}/"
        
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # Get list of databases (exclude system databases)
        db_list = client.list_database_names()
        exclude_dbs = ['admin', 'config', 'local']
        databases = [db for db in db_list if db not in exclude_dbs]
        
        all_collections_status = {}
        for db_name in databases:
            try:
                db = client[db_name]
                collections = db.list_collection_names()
                
                db_collections_status = {}
                for collection_name in collections:
                    try:
                        collection = db[collection_name]
                        collection.find_one()  # Test access
                        db_collections_status[collection_name] = "ok"
                    except Exception as e:
                        error_str = str(e).lower()
                        if "not found" in error_str or "does not exist" in error_str:
                            db_collections_status[collection_name] = "missing"
                        elif "unauthorized" in error_str or "not authorized" in error_str:
                            db_collections_status[collection_name] = "access_denied"
                        else:
                            db_collections_status[collection_name] = "error"
                
                all_collections_status[db_name] = db_collections_status
            except:
                all_collections_status[db_name] = {}
        
        client.close()
        return jsonify(all_collections_status)
    except Exception as e:
        app.logger.error(f"MongoDB connection failed: {e}")
        return jsonify({})

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "5000"))
    print(f"🚀 Starting Server API on port {port}")
    print(f"🌐 Running without SSL (HTTP only)")
    
    # Start background website monitoring
    start_background_monitoring()
    
    app.run(host="0.0.0.0", port=port, debug=False)
