#!/usr/bin/env python3
"""
Server API - Provides system metrics endpoint
Supports: CPU, Memory, Disk monitoring
Runs on remote servers to report system health
"""

import os, psutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv

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

@app.route('/api/health', methods=['GET'])
@require_auth
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/websites', methods=['GET'])
@require_auth
def get_websites():
    """Get .com and .in website folders from /var/www/html/*"""
    try:
        import glob
        websites = []
        www_paths = ["/var/www/*", "/var/www/html/*"]
        
        for path_pattern in www_paths:
            folders = glob.glob(path_pattern)
            for folder in folders:
                if os.path.isdir(folder):
                    folder_name = os.path.basename(folder)
                    # Only .com and .in domains
                    if folder_name.endswith('.com') or folder_name.endswith('.in'):
                        websites.append(folder_name)
        
        # Remove duplicates
        websites = list(set(websites))
        return jsonify({"websites": websites})
    except Exception as e:
        return jsonify({"websites": []})

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
    app.run(host="0.0.0.0", port=port, debug=False)
