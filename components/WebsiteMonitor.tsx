import { WebsiteStatus } from '@/types/monitoring';
import { Globe, CheckCircle, XCircle, Clock } from 'lucide-react';

interface WebsiteMonitorProps {
  websites?: WebsiteStatus[];
}

export function WebsiteMonitor({ websites }: WebsiteMonitorProps) {
  // Ensure websites is always an array
  const websitesList = websites || [];
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'up':
        return 'text-green-500';
      case 'down':
        return 'text-red-500';
      case 'slow':
        return 'text-yellow-500';
      case 'unknown':
        return 'text-gray-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      up: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      down: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      slow: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      unknown: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
    };
    return badges[status as keyof typeof badges] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  };

  const getResponseTimeColor = (time: number) => {
    if (time < 200) return 'text-green-600 dark:text-green-400';
    if (time < 500) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3 sm:p-4 lg:p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-2 mb-3 sm:mb-4">
        <Globe className="w-4 h-4 sm:w-5 sm:h-5 text-purple-600 dark:text-purple-400" />
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">Websites</h2>
      </div>

      <div className="space-y-2 sm:space-y-3 max-h-[400px] overflow-y-auto pr-1 sm:pr-2 custom-scrollbar">
        {websitesList.map((site, index) => (
          <div
            key={site.url || `website-${index}`}
            className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-2 sm:p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors gap-2"
          >
            <div className="flex-1 min-w-0 w-full sm:w-auto">
              <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 mb-1">
                <h3 className="font-medium text-sm sm:text-base text-gray-900 dark:text-white truncate flex-1 min-w-0">{site.url || 'Unknown URL'}</h3>
                <span className={`px-1.5 sm:px-2 py-0.5 rounded-full text-xs font-semibold ${getStatusBadge(site.status || 'unknown')} whitespace-nowrap`}>
                  {(site.status || 'unknown').toUpperCase()}
                </span>
                {site.statusCode && (
                  <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                    HTTP {site.statusCode}
                  </span>
                )}
              </div>
              
              <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs sm:text-sm">
                {(site.status === 'up' || site.status === 'slow') ? (
                  <>
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3 sm:w-4 sm:h-4 text-gray-500" />
                      <span className={getResponseTimeColor(site.responseTime || 0)}>
                        {site.responseTime || 0}ms
                      </span>
                    </div>
                    <span className="text-gray-400 dark:text-gray-500">
                      {site.lastCheck ? new Date(site.lastCheck).toLocaleTimeString() : 'Unknown'}
                    </span>
                  </>
                ) : (
                  <span className="text-red-500 dark:text-red-400">
                    {site.error || 'Connection failed'}
                  </span>
                )}
              </div>
            </div>

            <div className="flex-shrink-0 self-start sm:self-auto">
              {site.status === 'up' ? (
                <CheckCircle className={`w-4 h-4 sm:w-5 sm:h-5 ${getStatusColor(site.status || 'unknown')}`} />
              ) : (
                <XCircle className={`w-4 h-4 sm:w-5 sm:h-5 ${getStatusColor(site.status || 'unknown')}`} />
              )}
            </div>
          </div>
        ))}

        {websitesList.length === 0 && (
          <div className="text-center py-4 text-gray-500 dark:text-gray-400">
            <Globe className="w-10 h-10 mx-auto mb-1 opacity-50" />
            <p className="text-sm">No websites found</p>
            <p className="text-xs mt-1">Check /var/www/html/* for .com and .in folders</p>
          </div>
        )}
      </div>
    </div>
  );
}

