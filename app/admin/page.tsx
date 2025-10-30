'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Users, UserPlus, Edit, Trash2, Server, Shield, Key, X, Check } from 'lucide-react';

interface User {
  username: string;
  role: 'admin' | 'user';
  assignedServers: string[];
}

interface Server {
  ip: string;
  name: string;
}

export default function AdminPage() {
  const router = useRouter();
  const { user, isAuthenticated, isAdmin, loading: authLoading } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddUser, setShowAddUser] = useState(false);
  const [editingUser, setEditingUser] = useState<string | null>(null);
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'user' as 'admin' | 'user' });
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Redirect if not authenticated or not admin
  useEffect(() => {
    if (!authLoading && (!isAuthenticated || !isAdmin)) {
      router.push('/');
    }
  }, [authLoading, isAuthenticated, isAdmin, router]);

  // Fetch users and servers
  useEffect(() => {
    if (isAdmin) {
      fetchUsers();
      fetchServers();
    }
  }, [isAdmin]);

  const fetchUsers = async () => {
    try {
      const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:5001';
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${authApiUrl}/api/users`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchServers = async () => {
    // Hardcoded servers for now (can be fetched from API later)
    setServers([
      { ip: '192.168.1.19', name: 'Ubuntu Server 1' },
      { ip: '192.168.1.116', name: 'Windows Server' },
      { ip: '135.148.164.94', name: 'Old Staging Server' }
    ]);
  };

  const handleAddUser = async () => {
    if (!newUser.username || !newUser.password) {
      setMessage({ type: 'error', text: 'Username and password are required' });
      return;
    }

    try {
      const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:5001';
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${authApiUrl}/api/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          username: newUser.username,
          password: newUser.password,
          role: newUser.role,
          assignedServers: []
        })
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'User created successfully' });
        setShowAddUser(false);
        setNewUser({ username: '', password: '', role: 'user' });
        fetchUsers();
      } else {
        const data = await response.json();
        setMessage({ type: 'error', text: data.error || 'Failed to create user' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to create user' });
    }
  };

  const handleDeleteUser = async (username: string) => {
    if (!confirm(`Are you sure you want to delete user "${username}"?`)) return;

    try {
      const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:5001';
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${authApiUrl}/api/users/${username}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'User deleted successfully' });
        fetchUsers();
      } else {
        setMessage({ type: 'error', text: 'Failed to delete user' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to delete user' });
    }
  };

  const handleAssignServer = async (username: string, serverIp: string, assign: boolean) => {
    try {
      const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:5001';
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${authApiUrl}/api/users/${username}/servers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          serverIp,
          action: assign ? 'assign' : 'revoke'
        })
      });

      if (response.ok) {
        setMessage({ type: 'success', text: `Server ${assign ? 'assigned' : 'revoked'} successfully` });
        fetchUsers();
      } else {
        setMessage({ type: 'error', text: 'Failed to update server assignment' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update server assignment' });
    }
  };

  // Show loading while checking authentication
  if (authLoading || !isAuthenticated || !isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Shield className="w-8 h-8 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Admin Panel</h1>
            </div>
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Message */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg flex items-center justify-between ${
            message.type === 'success' 
              ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' 
              : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
          }`}>
            <span>{message.text}</span>
            <button onClick={() => setMessage(null)}>
              <X className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Add User Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <Users className="w-6 h-6" />
              User Management
            </h2>
            <button
              onClick={() => setShowAddUser(!showAddUser)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <UserPlus className="w-5 h-5" />
              Add User
            </button>
          </div>

          {showAddUser && (
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mb-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <input
                  type="text"
                  placeholder="Username"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                <input
                  type="password"
                  placeholder="Password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value as 'admin' | 'user' })}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleAddUser}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
                >
                  <Check className="w-4 h-4" />
                  Create User
                </button>
                <button
                  onClick={() => {
                    setShowAddUser(false);
                    setNewUser({ username: '', password: '', role: 'user' });
                  }}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
                >
                  <X className="w-4 h-4" />
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Users List */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            </div>
          ) : (
            users.map((u) => (
              <div key={u.username} className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                      <Users className="w-6 h-6 text-blue-600 dark:text-blue-300" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white">{u.username}</h3>
                      <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                        u.role === 'admin' 
                          ? 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                      }`}>
                        {u.role.toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteUser(u.username)}
                    className="px-3 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>

                {/* Server Assignments */}
                <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                    <Server className="w-4 h-4" />
                    Server Access {u.role === 'admin' && <span className="text-xs font-normal">(All servers - Admin)</span>}
                  </h4>
                  {u.role === 'user' ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {servers.map((server) => {
                        const isAssigned = u.assignedServers.includes(server.ip);
                        return (
                          <div
                            key={server.ip}
                            className={`p-3 rounded-lg border-2 flex items-center justify-between ${
                              isAssigned
                                ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                                : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700'
                            }`}
                          >
                            <div>
                              <div className="font-medium text-gray-900 dark:text-white">{server.name}</div>
                              <div className="text-sm text-gray-600 dark:text-gray-400">{server.ip}</div>
                            </div>
                            <button
                              onClick={() => handleAssignServer(u.username, server.ip, !isAssigned)}
                              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                                isAssigned
                                  ? 'bg-red-600 text-white hover:bg-red-700'
                                  : 'bg-blue-600 text-white hover:bg-blue-700'
                              }`}
                            >
                              {isAssigned ? 'Revoke' : 'Assign'}
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                      Admin users have access to all servers by default.
                    </p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}


