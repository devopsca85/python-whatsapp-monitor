'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { ArrowLeft, Server, Database, Globe, AlertTriangle, CheckCircle, XCircle, Activity, HardDrive, Cpu, MemoryStick } from 'lucide-react';
import { WebsiteMonitor } from '@/components/WebsiteMonitor';

interface ServerDetails {
  ip: string;
  name?: string;
  status: 'up' | 'down' | 'slow';
  serverType?: 'ubuntu' | 'windows';
  system?: {
    cpu?: { current: number; cores: number; load: number[] };
    memory?: { current: number; total: number; available: number; used: number };
    disk?: { current: number; total: number; free: number; used: number };
    uptime?: string;
    boot_time?: string;
    lastCheck?: string;
  };
  databases?: {
    mysql?: { status: string; databases: Record<string, any>; lastCheck: string };
    postgresql?: { status: string; databases: Record<string, any>; lastCheck: string };
    mongodb?: { status: string; databases: Record<string, any>; lastCheck: string };
    mssql?: { status: string; databases: any[]; count: number; tables: number; lastCheck?: string };
  };
  sqlJobs?: { total: number; running: number; failed: number; succeeded: number };
  websites?: Array<{ url: string; status: string; responseTime: number; statusCode?: number; lastCheck: string }>;
  alerts?: Array<any>;
  lastUpdate?: string;
}

export default function ServerDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const serverIp = params.ip as string;

  const [serverDetails, setServerDetails] = useState<ServerDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (user && user.role === 'user') {
      if (!user.assignedServers || !user.assignedServers.includes(serverIp)) {
        router.push('/');
      }
    }
  }, [user, serverIp, router]);

  const fetchServerDetails = async () => {
    try {
      setError(null);
      const data = await api.getServerDetails(serverIp);
      setServerDetails(data);
    } catch (err) {
      setError('Failed to fetch server details');
      console.error('Error fetching server details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServerDetails();
  }, [serverIp]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchServerDetails, 15000);
    return () => clearInterval(interval);
  }, [autoRefresh, serverIp]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'up':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'down':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'slow':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return <XCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'up':
        return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-200';
      case 'down':
        return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-200';
      case 'slow':
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-200';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const formatBytes = (bytes: number) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUptime = (uptime?: string) => uptime || 'N/A';

  if (authLoading || !isAuthenticated || loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">
            {authLoading ? 'Checking authentication...' : 'Loading server details...'}
          </p>
        </div>
      </div>
    );
  }

  if (error || !serverDetails) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Error Loading Server</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error || 'Server details not found'}</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      {/* (same header as before) */}

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Websites */}
          <div className="lg:col-span-2">
            {serverDetails?.websites ? (
              <WebsiteMonitor websites={serverDetails.websites as any} />
            ) : (
              <p className="text-gray-500 dark:text-gray-400">No website data available</p>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* System Info */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">System Information</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Uptime:</span>
                  <span className="text-gray-900 dark:text-white">
                    {serverDetails?.system?.uptime ? formatUptime(serverDetails.system.uptime) : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Boot Time:</span>
                  <span className="text-gray-900 dark:text-white">
                    {serverDetails?.system?.boot_time
                      ? new Date(serverDetails.system.boot_time).toLocaleString()
                      : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Last Check:</span>
                  <span className="text-gray-900 dark:text-white">
                    {serverDetails?.system?.lastCheck
                      ? new Date(serverDetails.system.lastCheck).toLocaleString()
                      : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* System Metrics */}
        {serverDetails?.system && (
          <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* CPU */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Cpu className="w-5 h-5 text-blue-600" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">CPU Usage</h3>
                </div>
                <span className="text-2xl font-bold text-gray-900 dark:text-white">
                  {serverDetails?.system?.cpu?.current ?? 0}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${serverDetails?.system?.cpu?.current ?? 0}%` }}
                ></div>
              </div>
              <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {serverDetails?.system?.cpu?.cores ?? 0} cores • Load:{' '}
                {serverDetails?.system?.cpu?.load?.join(', ') || 'N/A'}
              </div>
            </div>

            {/* Memory */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <MemoryStick className="w-5 h-5 text-green-600" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Memory Usage</h3>
                </div>
                <span className="text-2xl font-bold text-gray-900 dark:text-white">
                  {serverDetails?.system?.memory?.current ?? 0}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div
                  className="bg-green-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${serverDetails?.system?.memory?.current ?? 0}%` }}
                ></div>
              </div>
              <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {formatBytes(serverDetails?.system?.memory?.used ?? 0)} /{' '}
                {formatBytes(serverDetails?.system?.memory?.total ?? 0)} used
              </div>
            </div>

            {/* Disk */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <HardDrive className="w-5 h-5 text-purple-600" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Disk Usage</h3>
                </div>
                <span className="text-2xl font-bold text-gray-900 dark:text-white">
                  {serverDetails?.system?.disk?.current ?? 0}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div
                  className="bg-purple-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${serverDetails?.system?.disk?.current ?? 0}%` }}
                ></div>
              </div>
              <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {formatBytes(serverDetails?.system?.disk?.used ?? 0)} /{' '}
                {formatBytes(serverDetails?.system?.disk?.total ?? 0)} used
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

