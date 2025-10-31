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
      className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 md:p-5 lg:p-6 xl:p-7 border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all cursor-pointer active:scale-95 md:hover:scale-[1.02] lg:hover:scale-105"
      onClick={handleCardClick}
    >
      {/* Header */}
      <div className="flex items-start md:items-center justify-between mb-3 md:mb-4 lg:mb-5 gap-2">
        <div className="flex items-center gap-2 md:gap-3 lg:gap-4 min-w-0 flex-1">
          <div className={`p-2 md:p-2.5 lg:p-3 rounded-lg ${status.badge} min-w-[40px] md:min-w-[44px] lg:min-w-[48px] xl:min-w-[52px] min-h-[40px] md:min-h-[44px] lg:min-h-[48px] xl:min-h-[52px] flex items-center justify-center flex-shrink-0`}>
            <Server className={`w-5 h-5 md:w-5.5 md:h-5.5 lg:w-6 lg:h-6 xl:w-7 xl:h-7 ${status.text}`} />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-sm md:text-base lg:text-lg xl:text-xl text-gray-900 dark:text-white truncate">
              {(server as any).name || server.ip}
            </h3>
            <p className="text-xs md:text-sm lg:text-base text-gray-500 dark:text-gray-400 truncate">
              {server.ip}
            </p>
            <p className="text-xs md:text-sm text-gray-400 dark:text-gray-500 truncate">
              {server.uptime || 'Uptime: N/A'}
            </p>
          </div>
        </div>
        <span className={`px-2 md:px-3 lg:px-4 py-1 md:py-1.5 rounded-full text-xs md:text-sm font-semibold ${status.badge} min-w-[50px] md:min-w-[55px] lg:min-w-[60px] text-center flex-shrink-0`}>
          {status.label}
        </span>
      </div>

      {/* Metrics */}
      <div className="space-y-2 md:space-y-2.5 lg:space-y-3">
        {/* CPU */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-1.5 md:gap-2">
              <Cpu className="w-3.5 h-3.5 md:w-4 md:h-4 lg:w-4.5 lg:h-4.5 xl:w-5 xl:h-5 text-gray-600 dark:text-gray-400" />
              <span className="text-xs md:text-sm lg:text-base font-medium text-gray-700 dark:text-gray-300">CPU</span>
            </div>
            <span className="text-xs md:text-sm lg:text-base font-semibold text-gray-900 dark:text-white">
              {server.cpu}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 md:h-2 lg:h-2.5">
            <div
              className={`h-1.5 md:h-2 lg:h-2.5 rounded-full transition-all ${getMetricColor(server.cpu)}`}
              style={{ width: `${server.cpu}%` }}
            />
          </div>
        </div>

        {/* RAM */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-1.5 md:gap-2">
              <Activity className="w-3.5 h-3.5 md:w-4 md:h-4 lg:w-4.5 lg:h-4.5 xl:w-5 xl:h-5 text-gray-600 dark:text-gray-400" />
              <span className="text-xs md:text-sm lg:text-base font-medium text-gray-700 dark:text-gray-300">RAM</span>
            </div>
            <span className="text-xs md:text-sm lg:text-base font-semibold text-gray-900 dark:text-white">
              {server.ram}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 md:h-2 lg:h-2.5">
            <div
              className={`h-1.5 md:h-2 lg:h-2.5 rounded-full transition-all ${getMetricColor(server.ram)}`}
              style={{ width: `${server.ram}%` }}
            />
          </div>
        </div>

        {/* Disk */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-1.5 md:gap-2">
              <HardDrive className="w-3.5 h-3.5 md:w-4 md:h-4 lg:w-4.5 lg:h-4.5 xl:w-5 xl:h-5 text-gray-600 dark:text-gray-400" />
              <span className="text-xs md:text-sm lg:text-base font-medium text-gray-700 dark:text-gray-300">Disk</span>
            </div>
            <span className="text-xs md:text-sm lg:text-base font-semibold text-gray-900 dark:text-white">
              {server.disk}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 md:h-2 lg:h-2.5">
            <div
              className={`h-1.5 md:h-2 lg:h-2.5 rounded-full transition-all ${getMetricColor(server.disk)}`}
              style={{ width: `${server.disk}%` }}
            />
          </div>
        </div>

        {/* Services */}
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <Database className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {(server as any).serverType === 'windows' ? 'Database' : 'Services'}
            </span>
          </div>
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
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              <div className="flex justify-between">
                <span>Databases:</span>
                <span className="font-semibold">{server.services.mssql.databases || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Tables:</span>
                <span className="font-semibold">{server.services.mssql.tables || 0}</span>
              </div>
            </div>
          )}
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
      <div className="mt-3 md:mt-4 lg:mt-5 pt-3 md:pt-4 lg:pt-5 border-t border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1 sm:gap-0 text-xs md:text-sm text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-1 md:gap-1.5">
          <Clock className="w-3 h-3 md:w-3.5 md:h-3.5 lg:w-4 lg:h-4" />
          <span>Response: {server.responseTime}ms</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="whitespace-nowrap">{new Date(server.lastCheck).toLocaleTimeString()}</span>
          <ExternalLink className="w-3 h-3 md:w-3.5 md:h-3.5 lg:w-4 lg:h-4" />
        </div>
      </div>
    </div>
  );
}


