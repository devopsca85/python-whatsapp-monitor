#!/usr/bin/env node

/**
 * Orion Monitoring Dashboard - Authentication Server
 * 
 * Provides JWT-based authentication and user management
 * for the monitoring dashboard with role-based access control.
 */

const express = require('express');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const PORT = process.env.AUTH_PORT || 5001;
const JWT_SECRET = process.env.JWT_SECRET || 'orion-monitoring-secret-key-change-in-production';
const JWT_EXPIRATION = '24h';

// Paths
const USERS_FILE = path.join(__dirname, 'data', 'users.json');
const SERVER_ASSIGNMENTS_FILE = path.join(__dirname, 'data', 'server-assignments.json');

// Middleware
app.use(cors({
  origin: [
    'http://localhost:3000', 
    'http://localhost:3001',
    'http://192.168.1.15:3000',
    'http://192.168.1.15:3001',
    'http://192.168.1.15:3002',
    'http://192.168.1.15:3003'
  ],
  credentials: true
}));
app.use(express.json());

// Logging middleware
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Load users from JSON file
 */
async function loadUsers() {
  try {
    const data = await fs.readFile(USERS_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error loading users:', error);
    return { users: [] };
  }
}

/**
 * Save users to JSON file
 */
async function saveUsers(usersData) {
  try {
    await fs.writeFile(USERS_FILE, JSON.stringify(usersData, null, 2));
    return true;
  } catch (error) {
    console.error('Error saving users:', error);
    return false;
  }
}

/**
 * Generate JWT token
 */
function generateToken(user) {
  const payload = {
    userId: user.id,
    username: user.username,
    role: user.role,
    assignedServers: user.assignedServers || []
  };
  
  return jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRATION });
}

/**
 * Verify JWT token middleware
 */
function verifyToken(req, res, next) {
  const token = req.headers['authorization']?.replace('Bearer ', '');
  
  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }
  
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}

/**
 * Admin only middleware
 */
function requireAdmin(req, res, next) {
  if (req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Admin access required' });
  }
  next();
}

// ============================================================================
// AUTHENTICATION ENDPOINTS
// ============================================================================

/**
 * POST /api/auth/login
 * Login with username and password
 */
app.post('/api/auth/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password are required' });
    }
    
    // Load users
    const usersData = await loadUsers();
    const user = usersData.users.find(u => u.username === username);
    
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    // For development: accept plain text password "admin123" or "user123"
    // In production, all passwords should be hashed
    let passwordValid = false;
    
    if (password === 'admin123' && user.role === 'admin') {
      passwordValid = true;
    } else if (password === 'user123' && user.role === 'user') {
      passwordValid = true;
    } else {
      // Try bcrypt verification
      try {
        passwordValid = await bcrypt.compare(password, user.password);
      } catch (bcryptError) {
        console.error('Bcrypt error:', bcryptError);
        passwordValid = false;
      }
    }
    
    if (!passwordValid) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    // Update last login
    user.lastLogin = new Date().toISOString();
    await saveUsers(usersData);
    
    // Generate token
    const token = generateToken(user);
    
    // Return user info (without password)
    const { password: _, ...userWithoutPassword } = user;
    
    res.json({
      success: true,
      token,
      user: userWithoutPassword
    });
    
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * POST /api/auth/logout
 * Logout (client-side token removal)
 */
app.post('/api/auth/logout', verifyToken, (req, res) => {
  res.json({ success: true, message: 'Logged out successfully' });
});

/**
 * GET /api/auth/validate
 * Validate current token
 */
app.get('/api/auth/validate', verifyToken, (req, res) => {
  res.json({
    valid: true,
    user: req.user
  });
});

/**
 * GET /api/auth/me
 * Get current user info
 */
app.get('/api/auth/me', verifyToken, async (req, res) => {
  try {
    const usersData = await loadUsers();
    const user = usersData.users.find(u => u.id === req.user.userId);
    
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    
    const { password: _, ...userWithoutPassword } = user;
    res.json(userWithoutPassword);
    
  } catch (error) {
    console.error('Get user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// ============================================================================
// USER MANAGEMENT ENDPOINTS (Admin Only)
// ============================================================================

/**
 * GET /api/users
 * List all users (Admin only)
 */
app.get('/api/users', verifyToken, requireAdmin, async (req, res) => {
  try {
    const usersData = await loadUsers();
    const usersWithoutPasswords = usersData.users.map(({ password, ...user }) => user);
    res.json({ users: usersWithoutPasswords });
  } catch (error) {
    console.error('List users error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * POST /api/users
 * Create new user (Admin only)
 */
app.post('/api/users', verifyToken, requireAdmin, async (req, res) => {
  try {
    const { username, password, role, email, assignedServers } = req.body;
    
    if (!username || !password || !role) {
      return res.status(400).json({ error: 'Username, password, and role are required' });
    }
    
    if (!['admin', 'user'].includes(role)) {
      return res.status(400).json({ error: 'Role must be either "admin" or "user"' });
    }
    
    const usersData = await loadUsers();
    
    // Check if username already exists
    if (usersData.users.find(u => u.username === username)) {
      return res.status(400).json({ error: 'Username already exists' });
    }
    
    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);
    
    // Create new user
    const newUser = {
      id: String(Date.now()),
      username,
      password: hashedPassword,
      role,
      email: email || '',
      createdAt: new Date().toISOString(),
      assignedServers: assignedServers || []
    };
    
    usersData.users.push(newUser);
    await saveUsers(usersData);
    
    const { password: _, ...userWithoutPassword } = newUser;
    res.status(201).json({ success: true, user: userWithoutPassword });
    
  } catch (error) {
    console.error('Create user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * PUT /api/users/:id
 * Update user (Admin only)
 */
app.put('/api/users/:id', verifyToken, requireAdmin, async (req, res) => {
  try {
    const { id } = req.params;
    const { username, password, role, email, assignedServers } = req.body;
    
    const usersData = await loadUsers();
    const userIndex = usersData.users.findIndex(u => u.id === id);
    
    if (userIndex === -1) {
      return res.status(404).json({ error: 'User not found' });
    }
    
    const user = usersData.users[userIndex];
    
    // Update fields
    if (username) user.username = username;
    if (role) user.role = role;
    if (email !== undefined) user.email = email;
    if (assignedServers !== undefined) user.assignedServers = assignedServers;
    
    // Update password if provided
    if (password) {
      user.password = await bcrypt.hash(password, 10);
    }
    
    usersData.users[userIndex] = user;
    await saveUsers(usersData);
    
    const { password: _, ...userWithoutPassword } = user;
    res.json({ success: true, user: userWithoutPassword });
    
  } catch (error) {
    console.error('Update user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * DELETE /api/users/:id
 * Delete user (Admin only)
 */
// Delete user by ID (for backward compatibility)
app.delete('/api/users/:id', verifyToken, requireAdmin, async (req, res) => {
  try {
    const id = req.params.id.trim(); // Trim whitespace
    
    const usersData = await loadUsers();
    // Try to find by ID first, then by username (with trim)
    const userIndex = usersData.users.findIndex(u => 
      u.id === id || 
      u.username === id || 
      u.username?.trim() === id
    );
    
    if (userIndex === -1) {
      return res.status(404).json({ error: 'User not found' });
    }
    
    // Prevent deleting yourself
    const user = usersData.users[userIndex];
    if (user.id === req.user.userId || user.username?.trim() === req.user.username?.trim()) {
      return res.status(400).json({ error: 'Cannot delete your own account' });
    }
    
    usersData.users.splice(userIndex, 1);
    await saveUsers(usersData);
    
    res.json({ success: true, message: 'User deleted successfully' });
    
  } catch (error) {
    console.error('Delete user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * PUT /api/users/:id/servers
 * Assign servers to user (Admin only)
 */
app.put('/api/users/:id/servers', verifyToken, requireAdmin, async (req, res) => {
  try {
    const { id } = req.params;
    const { servers } = req.body;
    
    if (!Array.isArray(servers)) {
      return res.status(400).json({ error: 'Servers must be an array' });
    }
    
    const usersData = await loadUsers();
    const userIndex = usersData.users.findIndex(u => u.id === id);
    
    if (userIndex === -1) {
      return res.status(404).json({ error: 'User not found' });
    }
    
    usersData.users[userIndex].assignedServers = servers;
    await saveUsers(usersData);
    
    const { password: _, ...userWithoutPassword } = usersData.users[userIndex];
    res.json({ success: true, user: userWithoutPassword });
    
  } catch (error) {
    console.error('Assign servers error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * POST /api/users/:username/servers
 * Assign or revoke server access for a user (Admin only)
 */
app.post('/api/users/:username/servers', verifyToken, requireAdmin, async (req, res) => {
  try {
    const { username } = req.params;
    const { serverIp, action } = req.body;
    
    if (!serverIp || !action) {
      return res.status(400).json({ error: 'serverIp and action are required' });
    }
    
    if (!['assign', 'revoke'].includes(action)) {
      return res.status(400).json({ error: 'action must be "assign" or "revoke"' });
    }
    
    const usersData = await loadUsers();
    const userIndex = usersData.users.findIndex(u => u.username === username.trim());
    
    if (userIndex === -1) {
      return res.status(404).json({ error: 'User not found' });
    }
    
    // Initialize assignedServers if it doesn't exist
    if (!usersData.users[userIndex].assignedServers) {
      usersData.users[userIndex].assignedServers = [];
    }
    
    if (action === 'assign') {
      // Add server if not already assigned
      if (!usersData.users[userIndex].assignedServers.includes(serverIp)) {
        usersData.users[userIndex].assignedServers.push(serverIp);
      }
    } else {
      // Remove server
      usersData.users[userIndex].assignedServers = usersData.users[userIndex].assignedServers.filter(
        ip => ip !== serverIp
      );
    }
    
    await saveUsers(usersData);
    
    const { password: _, ...userWithoutPassword } = usersData.users[userIndex];
    res.json({ success: true, user: userWithoutPassword });
    
  } catch (error) {
    console.error('Assign/Revoke server error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// ============================================================================
// HEALTH CHECK
// ============================================================================

app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'Orion Authentication Server',
    timestamp: new Date().toISOString()
  });
});

// ============================================================================
// START SERVER
// ============================================================================

app.listen(PORT, () => {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║   Orion Monitoring Dashboard - Authentication Server       ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  console.log('');
  console.log(`🚀 Server running on http://localhost:${PORT}`);
  console.log('');
  console.log('📋 Available Endpoints:');
  console.log('   POST   /api/auth/login           - Login');
  console.log('   POST   /api/auth/logout          - Logout');
  console.log('   GET    /api/auth/validate        - Validate token');
  console.log('   GET    /api/auth/me              - Get current user');
  console.log('   GET    /api/users                - List users (Admin)');
  console.log('   POST   /api/users                - Create user (Admin)');
  console.log('   PUT    /api/users/:id            - Update user (Admin)');
  console.log('   DELETE /api/users/:id            - Delete user (Admin)');
  console.log('   PUT    /api/users/:id/servers    - Assign servers (Admin)');
  console.log('');
  console.log('🔐 Default Accounts:');
  console.log('   Admin: username=admin, password=admin123');
  console.log('   User:  username=user,  password=user123');
  console.log('');
  console.log('⚠️  CHANGE DEFAULT PASSWORDS IN PRODUCTION!');
  console.log('');
});

module.exports = app;


