-- ============================================================================
-- Orion Monitoring Dashboard - Authentication Database Schema
-- ============================================================================

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

-- Audit log table (optional but recommended)
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
-- Bcrypt hash for 'admin123'
INSERT INTO users (username, password, role) VALUES 
('admin', '$2b$10$rC/zKZ0XF8vY3eX9Z8kqMeTQf8FvP3YxJQJ0Qx1vWqK8Z.8FvP3Yx', 'admin')
ON DUPLICATE KEY UPDATE username=username;

-- Insert default regular user (password: user123)
-- Bcrypt hash for 'user123'
INSERT INTO users (username, password, role) VALUES 
('user', '$2b$10$tR/aKP1YG9wZ4fY0a9lrNfUQg9GwQ4ZyKRK1Ry2wXrL9a.9GwQ4Zy', 'user')
ON DUPLICATE KEY UPDATE username=username;

-- Show tables
SHOW TABLES;


