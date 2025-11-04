import { ServerStatus } from '@/types/monitoring';
import { Server, Cpu, HardDrive, Activity, Clock, ExternalLink, Globe, Database } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface ServerCardProps {
  server: ServerStatus;
}

export function ServerCard({ server }: ServerCardProps) {
  const router = useRouter();
  
  const handleCardClick = () => {
    router.push(`/server/${server.ip}`);
  };

  const statusConfig = {
    up: {
      bg: 'bg-green-500',
      text: 'text-green-500',
      badge: 'bg-green-100 text-green-800',
      label: 'UP',
    },
    down: {
      bg: 'bg-red-500',
      text: 'text-red-500',
      badge: 'bg-red-100 text-red-800',
      label: 'DOWN',
    },
    slow: {
      bg: 'bg-yellow-500',
      text: 'text-yellow-500',
      badge: 'bg-yellow-100 text-yellow-800',
      label: 'SLOW',
    },
    warning: {
      bg: 'bg-orange-500',
      text: 'text-orange-500',
      badge: 'bg-orange-100 text-orange-800',
      label: 'WARNING',
    },
  };

  const status = statusConfig[server.status];

  function getMetricColor(value: number): string {
    if (value >= 90) return 'bg-red-500';
    if (value >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  }

  return (
    <div 
      className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all cursor-pointer hover:scale-105"
      onClick={handleCardClick}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-lg ${status.badge} min-w-[48px] min-h-[48px] flex items-center justify-center`}>
            <Server className={`w-6 h-6 ${status.text}`} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {server.ip === '135.148.164.94' ? 'Old Staging Server' : ((server as any).name || server.ip)}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {server.ip}
            </p>
            <p className="text-xs text-gray-400 dark:text-gray-500">
              {server.uptime || 'Uptime: N/A'}
            </p>
          </div>
        </div>
        <span className={`px-4 py-1.5 rounded-full text-xs font-semibold ${status.badge} min-w-[60px] text-center`}>
          {status.label}
        </span>
      </div>

      {/* Metrics */}
      <div className="space-y-3">
        {/* CPU */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">CPU</span>
            </div>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {server.cpu}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${getMetricColor(server.cpu)}`}
              style={{ width: `${server.cpu}%` }}
            />
          </div>
        </div>

        {/* RAM */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">RAM</span>
            </div>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {server.ram}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${getMetricColor(server.ram)}`}
              style={{ width: `${server.ram}%` }}
            />
          </div>
        </div>

        {/* Disk */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Disk</span>
            </div>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {server.disk}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${getMetricColor(server.disk)}`}
              style={{ width: `${server.disk}%` }}
            />
          </div>
        </div>

        {/* Database Services Block */}
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          {/* Title Bar */}
          <div className="bg-gray-50 dark:bg-gray-900 rounded-t-lg px-3 py-2 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-semibold text-gray-900 dark:text-white">
                {(server as any).serverType === 'windows' ? 'Database Services' : 'Database Services'}
              </span>
            </div>
          </div>
          
          {/* Services Content */}
          <div className="bg-gray-50 dark:bg-gray-900 rounded-b-lg p-3">
            <div className="grid grid-cols-3 gap-2 text-xs">
              {/* Show MSSQL for Windows, others for Ubuntu */}
              {(server as any).serverType === 'windows' ? (
                <div className="flex items-center gap-1">
                  <div className={`w-2 h-2 rounded-full ${server.services?.mssql?.status === 'up' ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-gray-600 dark:text-gray-400">MSSQL</span>
                </div>
              ) : (
                <>
                  {/* MySQL */}
                  <div className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${server.services?.mysql?.status === 'up' ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-gray-600 dark:text-gray-400">MySQL</span>
                  </div>
                  {/* PostgreSQL */}
                  <div className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${server.services?.postgresql?.status === 'up' ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-gray-600 dark:text-gray-400">PostgreSQL</span>
                  </div>
                  {/* MongoDB */}
                  <div className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${server.services?.mongodb?.status === 'up' ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-gray-600 dark:text-gray-400">MongoDB</span>
                  </div>
                </>
              )}
            </div>
            {/* Show MSSQL details for Windows */}
            {(server as any).serverType === 'windows' && server.services?.mssql && (
              <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
                <div className="flex justify-between">
                  <span>Databases:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">{server.services.mssql.databases || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Tables:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">{server.services.mssql.tables || 0}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* SQL Jobs (Windows only) */}
        {(server as any).serverType === 'windows' && (server as any).sqlJobs && (
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">SQL Jobs</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Total:</span>
                <span className="font-semibold text-gray-900 dark:text-white">{(server as any).sqlJobs.total || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Running:</span>
                <span className="font-semibold text-blue-600">{(server as any).sqlJobs.running || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Succeeded:</span>
                <span className="font-semibold text-green-600">{(server as any).sqlJobs.succeeded || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Failed:</span>
                <span className="font-semibold text-red-600">{(server as any).sqlJobs.failed || 0}</span>
              </div>
            </div>
          </div>
        )}

        {/* Websites Count */}
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Websites</span>
            </div>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {server.websites?.length || 0}
            </span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>Response: {server.responseTime}ms</span>
        </div>
        <div className="flex items-center gap-2">
          <span>{new Date(server.lastCheck).toLocaleTimeString()}</span>
          <ExternalLink className="w-3 h-3" />
        </div>
      </div>
    </div>
  );
}


