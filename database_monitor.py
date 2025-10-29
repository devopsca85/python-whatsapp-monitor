#!/usr/bin/env python3
"""
Database Monitor - Monitors MySQL, PostgreSQL, and MongoDB (Docker) databases
Sends WhatsApp alerts for database corruption, crashes, and issues
"""

import json, logging, requests, os, schedule, time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from whatsapp_notifier import WhatsAppNotifier
from dotenv import load_dotenv

load_dotenv()
SERVERS = os.getenv("SERVERS", "").split(",")

with open("config.json", "r") as f:
    config = json.load(f)

whatsapp_cfg = config["whatsapp"]
whatsapp_cfg["account_sid"] = os.getenv("TWILIO_ACCOUNT_SID", whatsapp_cfg.get("account_sid", ""))
whatsapp_cfg["auth_token"] = os.getenv("TWILIO_AUTH_TOKEN", whatsapp_cfg.get("auth_token", ""))
whatsapp_cfg["from_number"] = os.getenv("WHATSAPP_FROM_NUMBER", whatsapp_cfg.get("from_number", ""))
env_to_numbers = os.getenv("WHATSAPP_TO_NUMBERS")
if env_to_numbers:
    whatsapp_cfg["to_numbers"] = [n.strip() for n in env_to_numbers.split(",") if n.strip()]

handler = RotatingFileHandler("database_monitor.log", maxBytes=10*1024*1024, backupCount=5)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[handler, logging.StreamHandler()])
logger = logging.getLogger()

whatsapp_notifier = WhatsAppNotifier(config)
previous_db_status = {}
first_run = True

def send_whatsapp(message):
    try:
        if whatsapp_notifier.send_message(message):
            logger.info("📩 Database alert sent via WhatsApp")
    except Exception as e:
        logger.error(f"WhatsApp error: {e}")

def get_api_creds(ip):
    env_ip = ip.replace(".", "_")
    return os.getenv(f"API_TOKEN_{env_ip}"), os.getenv(f"API_ENDPOINT_{env_ip}", f"http://{ip}:5000/api")

def check_mysql_dbs(ip):
    try:
        token, endpoint = get_api_creds(ip)
        resp = requests.get(f"{endpoint}/mysql-all-dbs-health", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

def check_mysql_tables(ip):
    try:
        token, endpoint = get_api_creds(ip)
        resp = requests.get(f"{endpoint}/mysql-all-tables-health", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

def check_database_services(ip):
    """Check if MySQL, PostgreSQL, MongoDB services are running"""
    try:
        token, endpoint = get_api_creds(ip)
        resp = requests.get(f"{endpoint}/database-services-status", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

def check_postgresql_dbs(ip):
    try:
        token, endpoint = get_api_creds(ip)
        resp = requests.get(f"{endpoint}/postgresql-all-dbs-health", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

def check_postgresql_tables(ip):
    try:
        token, endpoint = get_api_creds(ip)
        resp = requests.get(f"{endpoint}/postgresql-all-tables-health", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

def check_mongodb_dbs(ip):
    try:
        token, endpoint = get_api_creds(ip)
        resp = requests.get(f"{endpoint}/mongodb-all-dbs-health", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

def check_mongodb_collections(ip):
    try:
        token, endpoint = get_api_creds(ip)
        resp = requests.get(f"{endpoint}/mongodb-all-collections-health", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}



def monitor_databases():
    global previous_db_status, first_run
    logger.info("🗄️  Checking databases...")
    
    for ip in SERVERS:
        ip = ip.strip()
        if not ip:
            continue
        
        if ip not in previous_db_status:
            previous_db_status[ip] = {
                "mysql": {"dbs": {}, "tables": {}},
                "postgresql": {"dbs": {}, "tables": {}},
                "mongodb": {"dbs": {}, "collections": {}},
                "services": {},
                "deleted_dbs": set()
            }

        # MySQL Databases
        current_mysql_dbs = set()
        mysql_dbs_data = check_mysql_dbs(ip)
        
        for db, status in mysql_dbs_data.items():
            current_mysql_dbs.add(db)
            prev = previous_db_status[ip]["mysql"]["dbs"].get(db)
            
            if prev is None:
                # Check if this database was previously deleted (recovery scenario)
                deleted_key = f"mysql.{db}"
                if deleted_key in previous_db_status[ip]["deleted_dbs"]:
                    msg = f"✅ MySQL DB RECOVERED ✅\nServer: {ip}\nDatabase: {db}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    send_whatsapp(msg)
                    logger.info(f"   MySQL database recovered: {db}")
                    previous_db_status[ip]["deleted_dbs"].discard(deleted_key)
                previous_db_status[ip]["mysql"]["dbs"][db] = status
            elif prev != status:
                if status == "up":
                    msg = f"✅ MySQL DB RECOVERED ✅\nServer: {ip}\nDatabase: {db}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                else:
                    msg = f"🚨 MySQL DB CRASHED 🚨\nServer: {ip}\nDatabase: {db}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                send_whatsapp(msg)
                previous_db_status[ip]["mysql"]["dbs"][db] = status

        # Detect deleted MySQL databases (skip on first run)
        previous_mysql_dbs = set(previous_db_status[ip]["mysql"]["dbs"].keys())
        deleted_mysql_dbs = previous_mysql_dbs - current_mysql_dbs
        
        if previous_mysql_dbs and not first_run:
            for db in deleted_mysql_dbs:
                msg = f"🚨 MySQL DATABASE DELETED 🚨\nServer: {ip}\nDatabase: {db}\n⚠️ DATABASE HAS BEEN DROPPED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                send_whatsapp(msg)
                logger.warning(f"   MySQL database deleted: {db}")
                previous_db_status[ip]["deleted_dbs"].add(f"mysql.{db}")
                del previous_db_status[ip]["mysql"]["dbs"][db]

        # MySQL Tables
        mysql_tables_data = check_mysql_tables(ip)
        
        for db, tables in mysql_tables_data.items():
            if f"mysql.{db}" in previous_db_status[ip]["deleted_dbs"]:
                continue
                
            current_tables = set(tables.keys())
            previous_tables = set(previous_db_status[ip]["mysql"]["tables"].keys())
            previous_tables_in_db = {t.split(".", 1)[1] for t in previous_tables if t.startswith(f"{db}.")}
            
            for table, status in tables.items():
                key = f"{db}.{table}"
                prev = previous_db_status[ip]["mysql"]["tables"].get(key)
                
                if prev is None:
                    # Check if this table was previously deleted (recovery scenario)
                    deleted_key = f"mysql.{db}.{table}"
                    if deleted_key in previous_db_status[ip]["deleted_dbs"]:
                        msg = f"✅ MySQL Table RECOVERED ✅\nServer: {ip}\nDB: {db}\nTable: {table}\nStatus: HEALTHY\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        send_whatsapp(msg)
                        logger.info(f"   MySQL table recovered: {key}")
                        previous_db_status[ip]["deleted_dbs"].discard(deleted_key)
                    previous_db_status[ip]["mysql"]["tables"][key] = status
                elif prev != status:
                    if status == "ok":
                        msg = f"✅ MySQL Table RECOVERED ✅\nServer: {ip}\nDB: {db}\nTable: {table}\nStatus: HEALTHY\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    elif status == "corrupted":
                        msg = f"🚨 MySQL Table CORRUPTED 🚨\nServer: {ip}\nDB: {db}\nTable: {table}\n⚠️ IMMEDIATE ACTION REQUIRED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    elif status == "missing":
                        msg = f"🚨 MySQL Table MISSING 🚨\nServer: {ip}\nDB: {db}\nTable: {table}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    else:
                        msg = f"🚨 MySQL Table ERROR 🚨\nServer: {ip}\nDB: {db}\nTable: {table}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    send_whatsapp(msg)
                    previous_db_status[ip]["mysql"]["tables"][key] = status
            
            deleted_tables = previous_tables_in_db - current_tables
            if previous_tables_in_db:
                for table in deleted_tables:
                    key = f"{db}.{table}"
                    if key in previous_db_status[ip]["mysql"]["tables"]:
                        msg = f"🚨 MySQL TABLE DELETED 🚨\nServer: {ip}\nDB: {db}\nTable: {table}\n⚠️ TABLE HAS BEEN DROPPED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        send_whatsapp(msg)
                        logger.warning(f"   MySQL table deleted: {key}")
                        previous_db_status[ip]["deleted_dbs"].add(f"mysql.{db}.{table}")
                        del previous_db_status[ip]["mysql"]["tables"][key]

        # PostgreSQL Service Status (Docker container)
        services_status = check_database_services(ip)
        for service_name, status in services_status.items():
            if service_name == "timestamp":
                continue
            if service_name == "postgresql":
                prev_status = previous_db_status[ip]["services"].get(service_name)
                if prev_status != status and prev_status is not None:
                    if status == "running":
                        msg = f"✅ POSTGRESQL CONTAINER UP ✅\nServer: {ip}\nService: PostgreSQL (Docker)\nStatus: RUNNING\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    else:
                        msg = f"🚨 POSTGRESQL CONTAINER DOWN 🚨\nServer: {ip}\nService: PostgreSQL (Docker)\nStatus: NOT RUNNING\n⚠️ CONTAINER STOPPED OR CRASHED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    send_whatsapp(msg)
                    logger.warning(f"   PostgreSQL container: {prev_status} → {status}")
                previous_db_status[ip]["services"][service_name] = status

        # PostgreSQL Databases (Docker container)
        current_pg_dbs = set()
        pg_dbs_data = check_postgresql_dbs(ip)
        
        for db, status in pg_dbs_data.items():
            current_pg_dbs.add(db)
            prev = previous_db_status[ip]["postgresql"]["dbs"].get(db)
            
            if prev is None:
                # Check if this database was previously deleted (recovery scenario)
                deleted_key = f"postgresql.{db}"
                if deleted_key in previous_db_status[ip]["deleted_dbs"]:
                    msg = f"✅ PostgreSQL DB RECOVERED ✅\nServer: {ip}\nDatabase: {db} (Docker)\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    send_whatsapp(msg)
                    logger.info(f"   PostgreSQL database recovered: {db}")
                    previous_db_status[ip]["deleted_dbs"].discard(deleted_key)
                previous_db_status[ip]["postgresql"]["dbs"][db] = status
            elif prev != status:
                if status == "up":
                    msg = f"✅ PostgreSQL DB RECOVERED ✅\nServer: {ip}\nDatabase: {db} (Docker)\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                else:
                    msg = f"🚨 PostgreSQL DB CRASHED 🚨\nServer: {ip}\nDatabase: {db} (Docker)\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                send_whatsapp(msg)
                previous_db_status[ip]["postgresql"]["dbs"][db] = status

        # Detect deleted PostgreSQL databases (skip on first run)
        previous_pg_dbs = set(previous_db_status[ip]["postgresql"]["dbs"].keys())
        deleted_pg_dbs = previous_pg_dbs - current_pg_dbs
        
        if previous_pg_dbs and not first_run:
            for db in deleted_pg_dbs:
                msg = f"🚨 PostgreSQL DATABASE DELETED 🚨\nServer: {ip}\nDatabase: {db} (Docker)\n⚠️ DATABASE HAS BEEN DROPPED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                send_whatsapp(msg)
                logger.warning(f"   PostgreSQL database deleted: {db}")
                previous_db_status[ip]["deleted_dbs"].add(f"postgresql.{db}")
                del previous_db_status[ip]["postgresql"]["dbs"][db]

        # PostgreSQL Tables (Docker container)
        pg_tables_data = check_postgresql_tables(ip)
        
        for db, tables in pg_tables_data.items():
            if f"postgresql.{db}" in previous_db_status[ip]["deleted_dbs"]:
                continue
                
            current_tables = set(tables.keys())
            previous_tables = set(previous_db_status[ip]["postgresql"]["tables"].keys())
            previous_tables_in_db = {t.split(".", 1)[1] for t in previous_tables if t.startswith(f"{db}.")}
            
            for table, status in tables.items():
                key = f"{db}.{table}"
                prev = previous_db_status[ip]["postgresql"]["tables"].get(key)
                
                if prev is None:
                    # Check if this table was previously deleted (recovery scenario)
                    deleted_key = f"postgresql.{db}.{table}"
                    if deleted_key in previous_db_status[ip]["deleted_dbs"]:
                        msg = f"✅ PostgreSQL Table RECOVERED ✅\nServer: {ip}\nDB: {db} (Docker)\nTable: {table}\nStatus: HEALTHY\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        send_whatsapp(msg)
                        logger.info(f"   PostgreSQL table recovered: {key}")
                        previous_db_status[ip]["deleted_dbs"].discard(deleted_key)
                    previous_db_status[ip]["postgresql"]["tables"][key] = status
                elif prev != status:
                    if status == "ok":
                        msg = f"✅ PostgreSQL Table RECOVERED ✅\nServer: {ip}\nDB: {db} (Docker)\nTable: {table}\nStatus: HEALTHY\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    else:
                        msg = f"🚨 PostgreSQL Table CRASHED 🚨\nServer: {ip}\nDB: {db} (Docker)\nTable: {table}\n⚠️ IMMEDIATE ACTION REQUIRED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    send_whatsapp(msg)
                    previous_db_status[ip]["postgresql"]["tables"][key] = status
            
            deleted_tables = previous_tables_in_db - current_tables
            if previous_tables_in_db:
                for table in deleted_tables:
                    key = f"{db}.{table}"
                    if key in previous_db_status[ip]["postgresql"]["tables"]:
                        msg = f"🚨 PostgreSQL TABLE DELETED 🚨\nServer: {ip}\nDB: {db} (Docker)\nTable: {table}\n⚠️ TABLE HAS BEEN DROPPED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        send_whatsapp(msg)
                        logger.warning(f"   PostgreSQL table deleted: {key}")
                        previous_db_status[ip]["deleted_dbs"].add(f"postgresql.{db}.{table}")
                        del previous_db_status[ip]["postgresql"]["tables"][key]

        # MongoDB Service Status (Docker container)
        for service_name, status in services_status.items():
            if service_name == "timestamp":
                continue
            if service_name == "mongodb":
                prev_status = previous_db_status[ip]["services"].get(service_name)
                if prev_status != status and prev_status is not None:
                    if status == "running":
                        msg = f"✅ MONGODB CONTAINER UP ✅\nServer: {ip}\nService: MongoDB (Docker)\nStatus: RUNNING\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    else:
                        msg = f"🚨 MONGODB CONTAINER DOWN 🚨\nServer: {ip}\nService: MongoDB (Docker)\nStatus: NOT RUNNING\n⚠️ CONTAINER STOPPED OR CRASHED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    send_whatsapp(msg)
                    logger.warning(f"   MongoDB container: {prev_status} → {status}")
                previous_db_status[ip]["services"][service_name] = status

        # MongoDB Databases (Docker container)
        current_mongo_dbs = set()
        mongo_dbs_data = check_mongodb_dbs(ip)
        
        for db, status in mongo_dbs_data.items():
            current_mongo_dbs.add(db)
            prev = previous_db_status[ip]["mongodb"]["dbs"].get(db)
            
            if prev is None:
                # Check if this database was previously deleted (recovery scenario)
                deleted_key = f"mongodb.{db}"
                if deleted_key in previous_db_status[ip]["deleted_dbs"]:
                    msg = f"✅ MongoDB DB RECOVERED ✅\nServer: {ip}\nDatabase: {db} (Docker)\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    send_whatsapp(msg)
                    logger.info(f"   MongoDB database recovered: {db}")
                    previous_db_status[ip]["deleted_dbs"].discard(deleted_key)
                previous_db_status[ip]["mongodb"]["dbs"][db] = status
            elif prev != status:
                if status == "up":
                    msg = f"✅ MongoDB DB RECOVERED ✅\nServer: {ip}\nDatabase: {db} (Docker)\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                else:
                    msg = f"🚨 MongoDB DB CRASHED 🚨\nServer: {ip}\nDatabase: {db} (Docker)\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                send_whatsapp(msg)
                previous_db_status[ip]["mongodb"]["dbs"][db] = status

        # Detect deleted MongoDB databases (skip on first run)
        previous_mongo_dbs = set(previous_db_status[ip]["mongodb"]["dbs"].keys())
        deleted_mongo_dbs = previous_mongo_dbs - current_mongo_dbs
        
        if previous_mongo_dbs and not first_run:
            for db in deleted_mongo_dbs:
                msg = f"🚨 MongoDB DATABASE DELETED 🚨\nServer: {ip}\nDatabase: {db} (Docker)\n⚠️ DATABASE HAS BEEN DROPPED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                send_whatsapp(msg)
                logger.warning(f"   MongoDB database deleted: {db}")
                previous_db_status[ip]["deleted_dbs"].add(f"mongodb.{db}")
                del previous_db_status[ip]["mongodb"]["dbs"][db]

        # MongoDB Collections (Docker container)
        mongo_collections_data = check_mongodb_collections(ip)
        
        for db, collections in mongo_collections_data.items():
            if f"mongodb.{db}" in previous_db_status[ip]["deleted_dbs"]:
                continue
                
            current_collections = set(collections.keys())
            previous_collections = set(previous_db_status[ip]["mongodb"]["collections"].keys())
            previous_collections_in_db = {c.split(".", 1)[1] for c in previous_collections if c.startswith(f"{db}.")}
            
            for collection, status in collections.items():
                key = f"{db}.{collection}"
                prev = previous_db_status[ip]["mongodb"]["collections"].get(key)
                
                if prev is None:
                    # Check if this collection was previously deleted (recovery scenario)
                    deleted_key = f"mongodb.{db}.{collection}"
                    if deleted_key in previous_db_status[ip]["deleted_dbs"]:
                        msg = f"✅ MongoDB Collection RECOVERED ✅\nServer: {ip}\nDB: {db} (Docker)\nCollection: {collection}\nStatus: HEALTHY\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        send_whatsapp(msg)
                        logger.info(f"   MongoDB collection recovered: {key}")
                        previous_db_status[ip]["deleted_dbs"].discard(deleted_key)
                    previous_db_status[ip]["mongodb"]["collections"][key] = status
                elif prev != status:
                    if status == "ok":
                        msg = f"✅ MongoDB Collection RECOVERED ✅\nServer: {ip}\nDB: {db} (Docker)\nCollection: {collection}\nStatus: HEALTHY\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    else:
                        msg = f"🚨 MongoDB Collection CRASHED 🚨\nServer: {ip}\nDB: {db} (Docker)\nCollection: {collection}\n⚠️ IMMEDIATE ACTION REQUIRED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    send_whatsapp(msg)
                    previous_db_status[ip]["mongodb"]["collections"][key] = status
            
            deleted_collections = previous_collections_in_db - current_collections
            if previous_collections_in_db:
                for collection in deleted_collections:
                    key = f"{db}.{collection}"
                    if key in previous_db_status[ip]["mongodb"]["collections"]:
                        msg = f"🚨 MongoDB COLLECTION DELETED 🚨\nServer: {ip}\nDB: {db} (Docker)\nCollection: {collection}\n⚠️ COLLECTION HAS BEEN DROPPED ⚠️\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        send_whatsapp(msg)
                        logger.warning(f"   MongoDB collection deleted: {key}")
                        previous_db_status[ip]["deleted_dbs"].add(f"mongodb.{db}.{collection}")
                        del previous_db_status[ip]["mongodb"]["collections"][key]
    
    # Mark first run as completed
    first_run = False

if __name__ == "__main__":
    try:
        print("🗄️  Database Monitor Started")
        print(f"Servers: {SERVERS}")
        monitor_databases()
        schedule.every(25).seconds.do(monitor_databases)
        print("✅ Monitoring databases every 25 seconds...")
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Database Monitor stopped")
