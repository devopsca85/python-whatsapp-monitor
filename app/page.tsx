'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Server, Database as DatabaseIcon, Globe, AlertTriangle, RefreshCw, LogOut, User, Shield, MoreVertical } from 'lucide-react';
import { ServerCard } from '@/components/ServerCard';
import { AlertList } from '@/components/AlertList';
import { StatsCard } from '@/components/StatsCard';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import type { DashboardSummary } from '@/types/monitoring';

export default function DashboardPage() {
  const { user, logout, isAuthenticated, isAdmin, loading: authLoading } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      window.location.href = '/login';
    }
  }, [authLoading, isAuthenticated]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const summary = await api.getDashboardSummary();
      
      // Filter servers based on user role and permissions
      let filteredServers = summary.servers;
      if (user?.role === 'user' && user?.assignedServers && user.assignedServers.length > 0) {
        // Users can only see their assigned servers
        filteredServers = summary.servers.filter(server => 
          user.assignedServers!.includes(server.ip)
        );
      }
      // Admins can see all servers, no filtering needed
      
      setData({
        ...summary,
        servers: filteredServers,
        stats: {
          ...summary.stats,
          totalServers: filteredServers.length,
          serversUp: filteredServers.filter(s => s.status === 'up').length,
          serversDown: filteredServers.filter(s => s.status === 'down').length,
          serversSlow: filteredServers.filter(s => s.status === 'slow').length,
        }
      });
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    // Auto-refresh every 15 seconds for real-time updates
    if (autoRefresh) {
      const interval = setInterval(fetchDashboardData, 15000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // Show loading while checking authentication
  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (loading && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600 dark:text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center max-w-md p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-red-500" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Connection Error</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4 w-full sm:w-auto">
              <img 
                src="/company-logo.svg" 
                alt="Company Logo" 
                className="h-8 sm:h-12 w-auto"
              />
              <div className="border-l-0 sm:border-l border-gray-300 dark:border-gray-600 pl-0 sm:pl-4 h-auto sm:h-12 flex flex-col justify-center">
                <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white leading-tight">
                  Orion Monitoring Dashboard
                </h1>
                <p className="text-gray-600 dark:text-gray-400 text-xs sm:text-sm mt-1">
                  Last updated: {lastUpdate.toLocaleTimeString()}
                </p>
              </div>
            </div>
            
            <div className="flex flex-wrap items-center gap-2 sm:gap-4 w-full sm:w-auto justify-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-xs sm:text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">Auto-refresh</span>
              </label>
              
              <button
                onClick={fetchDashboardData}
                disabled={loading}
                className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 text-sm"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline">Refresh</span>
              </button>

              {/* User Menu Dropdown */}
              <div className="relative pl-2 sm:pl-4 border-l border-gray-300 dark:border-gray-600" ref={userMenuRef}>
                {/* 3-Dot Menu Button */}
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  title="User menu"
                >
                  <MoreVertical className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </button>

                {/* Dropdown Menu */}
                {showUserMenu && (
                  <div className="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50">
                    {/* User Profile Info */}
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                          <User className="w-6 h-6 text-blue-600 dark:text-blue-300" />
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900 dark:text-white">{user?.username}</div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">{user?.role}</div>
                        </div>
                      </div>
                    </div>

                    {/* Menu Items */}
                    {isAdmin && (
                      <button
                        onClick={() => {
                          router.push('/admin');
                          setShowUserMenu(false);
                        }}
                        className="w-full flex items-center gap-3 px-4 py-2 text-left text-gray-700 dark:text-gray-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors"
                      >
                        <Shield className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                        <span>Admin Panel</span>
                      </button>
                    )}
                    <button
                      onClick={() => {
                        logout();
                        setShowUserMenu(false);
                      }}
                      className="w-full flex items-center gap-3 px-4 py-2 text-left text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Logout</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <StatsCard
            title="Total Servers"
            value={data?.stats.totalServers || 0}
            icon={Server}
            color="blue"
          />
          <StatsCard
            title="Servers Up"
            value={data?.stats.serversUp || 0}
            icon={Server}
            color="green"
          />
          <StatsCard
            title="Servers Down"
            value={data?.stats.serversDown || 0}
            icon={Server}
            color="red"
          />
          <StatsCard
            title="Critical Alerts"
            value={data?.stats.criticalAlerts || 0}
            icon={AlertTriangle}
            color="yellow"
          />
        </div>

        {/* Servers Grid */}
        <div className="mb-6 sm:mb-8">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-4">Servers</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {data?.servers.map((server) => (
              <ServerCard key={server.ip} server={server} />
            ))}
          </div>
        </div>

        {/* Alerts */}
        <AlertList alerts={data?.alerts || []} limit={10} />
      </div>
    </div>
  );
}
