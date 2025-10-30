/**
 * Database Configuration Module
 * Handles MySQL connection pooling and queries
 */

const mysql = require('mysql2/promise');
require('dotenv').config();

// Database configuration
const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '3306'),
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'orion_auth',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  enableKeepAlive: true,
  keepAliveInitialDelay: 0
};

// Create connection pool
let pool = null;

/**
 * Initialize database connection pool
 */
async function initializeDatabase() {
  try {
    pool = mysql.createPool(dbConfig);
    
    // Test connection
    const connection = await pool.getConnection();
    console.log('✅ MySQL database connected successfully');
    console.log(`📊 Database: ${dbConfig.database}`);
    connection.release();
    
    return true;
  } catch (error) {
    console.error('❌ MySQL connection failed:', error.message);
    console.error('   Make sure MySQL is running and credentials are correct');
    return false;
  }
}

/**
 * Get database connection pool
 */
function getPool() {
  if (!pool) {
    throw new Error('Database not initialized. Call initializeDatabase() first.');
  }
  return pool;
}

/**
 * Execute a query
 */
async function query(sql, params = []) {
  try {
    const [results] = await pool.execute(sql, params);
    return results;
  } catch (error) {
    console.error('Database query error:', error);
    throw error;
  }
}

/**
 * Get a user by username
 */
async function getUserByUsername(username) {
  const sql = 'SELECT * FROM users WHERE username = ? AND is_active = TRUE LIMIT 1';
  const results = await query(sql, [username]);
  return results[0] || null;
}

/**
 * Get all users (without passwords)
 */
async function getAllUsers() {
  const sql = `
    SELECT 
      id, username, role, created_at, updated_at, last_login, is_active
    FROM users 
    WHERE is_active = TRUE
    ORDER BY created_at DESC
  `;
  return await query(sql);
}

/**
 * Get user's assigned servers
 */
async function getUserServers(userId) {
  const sql = `
    SELECT server_ip, server_name, assigned_at 
    FROM server_assignments 
    WHERE user_id = ?
    ORDER BY assigned_at DESC
  `;
  return await query(sql, [userId]);
}

/**
 * Create a new user
 */
async function createUser(username, hashedPassword, role = 'user') {
  const sql = `
    INSERT INTO users (username, password, role) 
    VALUES (?, ?, ?)
  `;
  const result = await query(sql, [username, hashedPassword, role]);
  return result.insertId;
}

/**
 * Update user password
 */
async function updateUserPassword(userId, hashedPassword) {
  const sql = 'UPDATE users SET password = ?, updated_at = NOW() WHERE id = ?';
  await query(sql, [hashedPassword, userId]);
}

/**
 * Update user last login
 */
async function updateLastLogin(userId) {
  const sql = 'UPDATE users SET last_login = NOW() WHERE id = ?';
  await query(sql, [userId]);
}

/**
 * Delete user
 */
async function deleteUser(userId) {
  const sql = 'DELETE FROM users WHERE id = ?';
  await query(sql, [userId]);
}

/**
 * Assign server to user
 */
async function assignServer(userId, serverIp, serverName = null) {
  const sql = `
    INSERT INTO server_assignments (user_id, server_ip, server_name) 
    VALUES (?, ?, ?)
    ON DUPLICATE KEY UPDATE server_name = VALUES(server_name)
  `;
  await query(sql, [userId, serverIp, serverName]);
}

/**
 * Revoke server from user
 */
async function revokeServer(userId, serverIp) {
  const sql = 'DELETE FROM server_assignments WHERE user_id = ? AND server_ip = ?';
  await query(sql, [userId, serverIp]);
}

/**
 * Get all server assignments for a user
 */
async function getServerAssignments(userId) {
  const assignments = await getUserServers(userId);
  return assignments.map(a => a.server_ip);
}

/**
 * Log audit action
 */
async function logAudit(userId, action, details = null, ipAddress = null) {
  try {
    const sql = `
      INSERT INTO audit_logs (user_id, action, details, ip_address) 
      VALUES (?, ?, ?, ?)
    `;
    await query(sql, [userId, action, details, ipAddress]);
  } catch (error) {
    // Don't fail the main operation if logging fails
    console.error('Audit log error:', error.message);
  }
}

/**
 * Close database connection
 */
async function closeDatabase() {
  if (pool) {
    await pool.end();
    console.log('✅ Database connection closed');
  }
}

module.exports = {
  initializeDatabase,
  getPool,
  query,
  getUserByUsername,
  getAllUsers,
  getUserServers,
  createUser,
  updateUserPassword,
  updateLastLogin,
  deleteUser,
  assignServer,
  revokeServer,
  getServerAssignments,
  logAudit,
  closeDatabase
};


