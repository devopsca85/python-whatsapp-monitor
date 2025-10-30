#!/bin/bash

# ============================================================================
# MySQL Setup Script for Orion Authentication System
# ============================================================================

echo "🚀 Orion Authentication - MySQL Setup"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if MySQL is installed
if ! command -v mysql &> /dev/null; then
    echo -e "${RED}❌ MySQL is not installed${NC}"
    echo "Please install MySQL first:"
    echo "  sudo apt update"
    echo "  sudo apt install mysql-server"
    exit 1
fi

echo -e "${GREEN}✅ MySQL is installed${NC}"
echo ""

# Prompt for MySQL root password
echo "Please enter your MySQL root password:"
read -s MYSQL_ROOT_PASSWORD
echo ""

# Test MySQL connection
if ! mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SELECT 1;" &> /dev/null; then
    echo -e "${RED}❌ Failed to connect to MySQL${NC}"
    echo "Please check your password and try again"
    exit 1
fi

echo -e "${GREEN}✅ MySQL connection successful${NC}"
echo ""

# Create database and tables
echo "Creating database and tables..."
mysql -u root -p"${MYSQL_ROOT_PASSWORD}" << EOF
-- Create database
CREATE DATABASE IF NOT EXISTS orion_auth;
USE orion_auth;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Server assignments table
CREATE TABLE IF NOT EXISTS server_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    server_ip VARCHAR(50) NOT NULL,
    server_name VARCHAR(100),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_server (user_id, server_ip),
    INDEX idx_user_id (user_id),
    INDEX idx_server_ip (server_ip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(50) NOT NULL,
    details TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123)
INSERT INTO users (username, password, role) VALUES 
('admin', '\$2b\$10\$YourHashedPasswordHere', 'admin')
ON DUPLICATE KEY UPDATE username=username;

-- Insert default regular user (password: user123)
INSERT INTO users (username, password, role) VALUES 
('user', '\$2b\$10\$YourHashedPasswordHere', 'user')
ON DUPLICATE KEY UPDATE username=username;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database and tables created successfully${NC}"
else
    echo -e "${RED}❌ Failed to create database${NC}"
    exit 1
fi
echo ""

# Create dedicated MySQL user
echo "Creating dedicated MySQL user for authentication..."
echo "Enter a secure password for the 'orion_auth' MySQL user:"
read -s ORION_DB_PASSWORD
echo ""

mysql -u root -p"${MYSQL_ROOT_PASSWORD}" << EOF
CREATE USER IF NOT EXISTS 'orion_auth'@'localhost' IDENTIFIED BY '${ORION_DB_PASSWORD}';
GRANT ALL PRIVILEGES ON orion_auth.* TO 'orion_auth'@'localhost';
FLUSH PRIVILEGES;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ MySQL user 'orion_auth' created${NC}"
else
    echo -e "${YELLOW}⚠️  User might already exist (this is okay)${NC}"
fi
echo ""

# Create .env file
echo "Creating .env configuration file..."
cat > .env << EOF
# Authentication Server Configuration
AUTH_SERVER_PORT=5001

# JWT Configuration
JWT_SECRET=$(openssl rand -base64 32)
JWT_EXPIRES_IN=24h

# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=orion_auth
DB_PASSWORD=${ORION_DB_PASSWORD}
DB_NAME=orion_auth

# Enable MySQL
USE_MYSQL=true
EOF

echo -e "${GREEN}✅ .env file created${NC}"
echo ""

# Test database connection
echo "Testing database connection..."
if mysql -u orion_auth -p"${ORION_DB_PASSWORD}" orion_auth -e "SHOW TABLES;" &> /dev/null; then
    echo -e "${GREEN}✅ Database connection test successful${NC}"
else
    echo -e "${RED}❌ Database connection test failed${NC}"
    exit 1
fi
echo ""

# Show summary
echo "======================================"
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "======================================"
echo ""
echo "Database: orion_auth"
echo "Tables created: users, server_assignments, audit_logs"
echo ""
echo "Default credentials:"
echo "  Admin: admin / admin123"
echo "  User:  user / user123"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Change default passwords immediately!${NC}"
echo ""
echo "Next steps:"
echo "  1. Update default user passwords in MySQL"
echo "  2. Restart authentication server:"
echo "     cd /var/www/html/new-config-manager/monitoring-dashboard"
echo "     pkill -f auth-server"
echo "     node backend/auth-server.js > /tmp/auth-server.log 2>&1 &"
echo ""


