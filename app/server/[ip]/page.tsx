'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { ArrowLeft, Server, Database, Globe, AlertTriangle, CheckCircle, XCircle, Activity, HardDrive, Cpu, MemoryStick, ChevronDown, ChevronUp } from 'lucide-react';
import { WebsiteMonitor } from '@/components/WebsiteMonitor';
import type { WebsiteStatus } from '@/types/monitoring';

interface ServerDetails {
  ip: string;
  name?: string;
  status: 'up' | 'down' | 'slow';
  serverType?: 'new-staging' | 'windows' | 'old-staging';
  system: {
    cpu: {
      current: number;
      cores: number;
      load: number[];
    };
    memory: {
      current: number;
      total: number;
      available: number;
      used: number;
    };
    disk: {
      current: number;
      total: number;
      free: number;
      used: number;
    };
    uptime: string;
    boot_time: string;
    lastCheck: string;
  };
  databases: {
    mysql?: {
      status: string;
      databases: Record<string, any>;
      lastCheck: string;
    };
    postgresql?: {
      status: string;
      databases: Record<string, any>;
      lastCheck: string;
      containers?: Array<{
        name: string;
        image: string;
        status: string;
        statusText: string;
      }>;
    };
    mongodb?: {
      status: string;
      containers?: Array<{
        name: string;
        image: string;
        status: string;
        statusText: string;
      }>;
      databases: Record<string, any>;
      lastCheck: string;
    };
    mssql?: {
      status: string;
      databases: any[];
      count: number;
      tables: number;
      lastCheck?: string;
    };
  };
  sqlJobs?: {
    total: number;
    running: number;
    failed: number;
    succeeded: number;
  };
  websites: Array<{
    url: string;
    status: 'up' | 'down' | 'slow' | 'unknown';
    responseTime: number;
    statusCode?: number;
    lastCheck: string;
  }>;
  alerts: Array<any>;
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
  const [expandedServices, setExpandedServices] = useState<{ [key: string]: boolean }>({});

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Check if user has permission to view this server
  useEffect(() => {
    if (user && user.role === 'user') {
      if (!user.assignedServers || !user.assignedServers.includes(serverIp)) {
        // User doesn't have access to this server
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

    const interval = setInterval(fetchServerDetails, 15000); // Refresh every 15 seconds for real-time updates
    return () => clearInterval(interval);
  }, [autoRefresh, serverIp]);

  const getStatusIcon = (status: string) => {
    const statusLower = status?.toLowerCase() || '';
    if (statusLower === 'up' || statusLower.startsWith('up')) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    } else if (statusLower === 'down') {
      return <XCircle className="w-5 h-5 text-red-500" />;
    } else if (statusLower === 'slow') {
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    } else {
      // For other statuses (like "Exited (0) 2 days ago"), show warning icon
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
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
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUptime = (uptime: string) => {
    return uptime || 'Unknown';
  };

  // Show loading while checking authentication or fetching data
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
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between py-4 sm:py-6 gap-4">
            <div className="flex items-center space-x-3 sm:space-x-4 lg:space-x-6 w-full sm:w-auto">
              <button
                onClick={() => router.back()}
                className="p-2 sm:p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <ArrowLeft className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600 dark:text-gray-400" />
              </button>
              <img 
                src="/company-logo.svg" 
                alt="Company Logo" 
                className="h-8 sm:h-10 w-auto"
              />
              <div className="border-l border-gray-300 dark:border-gray-600 pl-3 sm:pl-4 lg:pl-5 h-auto sm:h-16 flex items-center flex-1 min-w-0">
                <div className="flex items-center space-x-2 sm:space-x-3 lg:space-x-5 w-full">
                  <div className="p-2 sm:p-3 lg:p-4 rounded-lg bg-blue-100 dark:bg-blue-900 min-w-[48px] sm:min-w-[56px] lg:min-w-[64px] min-h-[48px] sm:min-h-[56px] lg:min-h-[64px] flex items-center justify-center flex-shrink-0">
                    <Server className="w-6 h-6 sm:w-7 sm:h-7 lg:w-8 lg:h-8 text-blue-600" />
                  </div>
                  <div className="flex flex-col justify-center space-y-1 min-w-0 flex-1">
                    <h1 className="text-base sm:text-lg lg:text-xl font-semibold text-gray-900 dark:text-white leading-tight truncate">
                      {serverDetails.name || (serverDetails.ip === '147.135.116.243' ? 'New Staging Server' : serverDetails.ip === '135.148.164.94' ? 'Old Staging Server' : `Server ${serverDetails.ip}`)}
                    </h1>
                    <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 truncate">
                      {serverDetails.ip}
                    </p>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(serverDetails.status)}
                      <span className={`px-2 sm:px-3 py-0.5 sm:py-1 rounded-full text-xs font-medium ${getStatusColor(serverDetails.status)} min-w-[50px] text-center`}>
                        {serverDetails.status.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2 sm:space-x-3 lg:space-x-5 w-full sm:w-auto justify-end">
              <div className="flex items-center space-x-2 sm:space-x-3">
                <input
                  type="checkbox"
                  id="auto-refresh"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="auto-refresh" className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
                  Auto-refresh
                </label>
              </div>
              <button
                onClick={fetchServerDetails}
                className="px-4 sm:px-5 lg:px-6 py-2 sm:py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-xs sm:text-sm font-medium whitespace-nowrap"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
          {/* Websites */}
          <div className="lg:col-span-2 order-2 lg:order-1">
            <WebsiteMonitor websites={(serverDetails.websites || []) as WebsiteStatus[]} />
          </div>

          {/* Sidebar */}
          <div className="space-y-4 sm:space-y-6 order-1 lg:order-2">
            {/* System Info */}
            {serverDetails.system && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">System Information</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Uptime:</span>
                    <span className="text-gray-900 dark:text-white">{formatUptime(serverDetails.system.uptime || 'Unknown')}</span>
                  </div>
                  {serverDetails.system.boot_time && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Boot Time:</span>
                      <span className="text-gray-900 dark:text-white">
                        {new Date(serverDetails.system.boot_time).toLocaleString()}
                      </span>
                    </div>
                  )}
                  {serverDetails.system.lastCheck && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Last Check:</span>
                      <span className="text-gray-900 dark:text-white">
                        {new Date(serverDetails.system.lastCheck).toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Services Status */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6">
              <div className="flex items-center space-x-2 mb-3 sm:mb-4">
                <Database className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Services</h3>
              </div>
              <div className="space-y-3">
                {/* Show MSSQL for Windows, others for Ubuntu */}
                {serverDetails.serverType === 'windows' ? (
                  <>
                    {/* MSSQL for Windows */}
                    {serverDetails.databases?.mssql && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600 dark:text-gray-400">MSSQL:</span>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(serverDetails.databases.mssql.status)}
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            serverDetails.databases.mssql.status === 'up' 
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          }`}>
                            {serverDetails.databases.mssql.status.toUpperCase()}
                          </span>
                        </div>
                      </div>
                    )}
                    {/* MSSQL Details */}
                    {serverDetails.databases?.mssql && (
                      <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500 dark:text-gray-400">Databases:</span>
                            <p className="text-lg font-semibold text-gray-900 dark:text-white">
                              {serverDetails.databases.mssql.count || 0}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-500 dark:text-gray-400">Tables:</span>
                            <p className="text-lg font-semibold text-gray-900 dark:text-white">
                              {serverDetails.databases.mssql.tables || 0}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                    {/* SQL Jobs Section */}
                    {serverDetails.sqlJobs && (
                      <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">SQL Server Agent Jobs</h4>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500 dark:text-gray-400">Total Jobs:</span>
                            <p className="text-lg font-semibold text-gray-900 dark:text-white">
                              {serverDetails.sqlJobs.total || 0}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-500 dark:text-gray-400">Running:</span>
                            <p className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                              {serverDetails.sqlJobs.running || 0}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-500 dark:text-gray-400">Succeeded:</span>
                            <p className="text-lg font-semibold text-green-600 dark:text-green-400">
                              {serverDetails.sqlJobs.succeeded || 0}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-500 dark:text-gray-400">Failed:</span>
                            <p className="text-lg font-semibold text-red-600 dark:text-red-400">
                              {serverDetails.sqlJobs.failed || 0}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    {/* MySQL, PostgreSQL, MongoDB for Ubuntu */}
                    {serverDetails.databases?.mysql && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600 dark:text-gray-400">MySQL:</span>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(serverDetails.databases.mysql.status)}
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            serverDetails.databases.mysql.status === 'up' 
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          }`}>
                            {serverDetails.databases.mysql.status.toUpperCase()}
                          </span>
                        </div>
                      </div>
                    )}
                    {serverDetails.databases?.postgresql && (
                      <div>
                        <div 
                          className="flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg p-2 -m-2 transition-colors"
                          onClick={() => setExpandedServices(prev => ({ ...prev, postgresql: !prev.postgresql }))}
                        >
                          <span className="text-gray-600 dark:text-gray-400">PostgreSQL:</span>
                          <div className="flex items-center space-x-2">
                            {getStatusIcon(serverDetails.databases.postgresql.status)}
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                              serverDetails.databases.postgresql.status?.toUpperCase() === 'UP' 
                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                            }`}>
                              {serverDetails.databases.postgresql.status?.toUpperCase() || 'NOT AVAILABLE'}
                            </span>
                            {serverDetails.databases.postgresql.containers && serverDetails.databases.postgresql.containers.length > 0 && (
                              expandedServices.postgresql ? (
                                <ChevronUp className="w-4 h-4 text-gray-500" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-gray-500" />
                              )
                            )}
                          </div>
                        </div>
                        {expandedServices.postgresql && serverDetails.databases.postgresql.containers && serverDetails.databases.postgresql.containers.length > 0 && (
                          <div className="mt-2 ml-4 space-y-2 border-l-2 border-gray-200 dark:border-gray-700 pl-4">
                            {serverDetails.databases.postgresql.containers.map((container, idx) => {
                              const isUp = container.status === 'Up' || container.status?.toLowerCase() === 'up' || container.status?.toLowerCase().startsWith('up');
                              return (
                                <div key={idx} className="flex items-center justify-between text-sm">
                                  <div className="flex flex-col">
                                    <span className="text-gray-500 dark:text-gray-400 font-mono text-xs">{container.name}</span>
                                    {container.image && (
                                      <span className="text-gray-400 dark:text-gray-500 text-xs">{container.image}</span>
                                    )}
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    {getStatusIcon(container.status)}
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                                      isUp
                                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                                    }`} title={container.statusText}>
                                      {container.status}
                                    </span>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}
                    {serverDetails.databases?.mongodb && (
                      <div>
                        <div 
                          className="flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg p-2 -m-2 transition-colors"
                          onClick={() => setExpandedServices(prev => ({ ...prev, mongodb: !prev.mongodb }))}
                        >
                          <span className="text-gray-600 dark:text-gray-400">MongoDB:</span>
                          <div className="flex items-center space-x-2">
                            {getStatusIcon(serverDetails.databases.mongodb.status)}
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                              serverDetails.databases.mongodb.status?.toUpperCase() === 'UP' 
                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                            }`}>
                              {serverDetails.databases.mongodb.status?.toUpperCase() || 'NOT AVAILABLE'}
                            </span>
                            {serverDetails.databases.mongodb.containers && serverDetails.databases.mongodb.containers.length > 0 && (
                              expandedServices.mongodb ? (
                                <ChevronUp className="w-4 h-4 text-gray-500" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-gray-500" />
                              )
                            )}
                          </div>
                        </div>
                        {expandedServices.mongodb && serverDetails.databases.mongodb.containers && serverDetails.databases.mongodb.containers.length > 0 && (
                          <div className="mt-2 ml-4 space-y-2 border-l-2 border-gray-200 dark:border-gray-700 pl-4">
                            {serverDetails.databases.mongodb.containers.map((container, idx) => {
                              const isUp = container.status === 'Up' || container.status?.toLowerCase() === 'up' || container.status?.toLowerCase().startsWith('up');
                              return (
                                <div key={idx} className="flex items-center justify-between text-sm">
                                  <div className="flex flex-col">
                                    <span className="text-gray-500 dark:text-gray-400 font-mono text-xs">{container.name}</span>
                                    {container.image && (
                                      <span className="text-gray-400 dark:text-gray-500 text-xs">{container.image}</span>
                                    )}
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    {getStatusIcon(container.status)}
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                                      isUp
                                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                                    }`} title={container.statusText}>
                                      {container.status}
                                    </span>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

          </div>
        </div>

        {/* System Metrics */}
        {serverDetails.system && (
          <div className="mt-6 sm:mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {/* CPU */}
            {serverDetails.system.cpu && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6">
                <div className="flex items-center justify-between mb-3 sm:mb-4">
                  <div className="flex items-center space-x-2">
                    <Cpu className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">CPU Usage</h3>
                  </div>
                  <span className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                    {serverDetails.system.cpu.current || 0}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${serverDetails.system.cpu.current || 0}%` }}
                  ></div>
                </div>
                <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  {serverDetails.system.cpu.cores || 0} cores {serverDetails.system.cpu.load && serverDetails.system.cpu.load.length > 0 && `• Load: ${serverDetails.system.cpu.load.join(', ')}`}
                </div>
              </div>
            )}

            {/* Memory */}
            {serverDetails.system.memory && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6">
                <div className="flex items-center justify-between mb-3 sm:mb-4">
                  <div className="flex items-center space-x-2">
                    <MemoryStick className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" />
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Memory Usage</h3>
                  </div>
                  <span className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                    {serverDetails.system.memory.current || 0}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className="bg-green-600 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${serverDetails.system.memory.current || 0}%` }}
                  ></div>
                </div>
                <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  {formatBytes(serverDetails.system.memory.used || 0)} / {formatBytes(serverDetails.system.memory.total || 0)} used
                </div>
              </div>
            )}

            {/* Disk */}
            {serverDetails.system.disk && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6">
                <div className="flex items-center justify-between mb-3 sm:mb-4">
                  <div className="flex items-center space-x-2">
                    <HardDrive className="w-4 h-4 sm:w-5 sm:h-5 text-purple-600" />
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Disk Usage</h3>
                  </div>
                  <span className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                    {serverDetails.system.disk.current || 0}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className="bg-purple-600 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${serverDetails.system.disk.current || 0}%` }}
                  ></div>
                </div>
                <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  {formatBytes(serverDetails.system.disk.used || 0)} / {formatBytes(serverDetails.system.disk.total || 0)} used
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
