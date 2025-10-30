import { Alert } from '@/types/monitoring';
import { AlertTriangle, AlertCircle, Info, CheckCircle, Server, Database, Globe } from 'lucide-react';

interface AlertListProps {
  alerts: Alert[];
  limit?: number;
}

export function AlertList({ alerts, limit = 10 }: AlertListProps) {
  const displayAlerts = limit ? alerts.slice(0, limit) : alerts;

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'recovery':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'server':
        return <Server className="w-4 h-4" />;
      case 'database':
        return <Database className="w-4 h-4" />;
      case 'website':
        return <Globe className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getAlertBg = (type: string) => {
    switch (type) {
      case 'critical':
        return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
      case 'recovery':
        return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
      default:
        return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
    }
  };

  const getSeverityBadge = (severity: string) => {
    const badges = {
      high: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      low: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    };
    return badges[severity as keyof typeof badges] || badges.low;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Recent Alerts</h2>
        {alerts.length > limit && (
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Showing {limit} of {alerts.length}
          </span>
        )}
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {displayAlerts.map((alert) => (
          <div
            key={alert.id}
            className={`p-4 rounded-lg border ${getAlertBg(alert.type)} transition-all hover:shadow-md`}
          >
            <div className="flex items-start gap-3">
              {/* Alert Icon */}
              <div className="mt-0.5">{getAlertIcon(alert.type)}</div>

              {/* Alert Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {getCategoryIcon(alert.category)}
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    {alert.category}
                  </span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getSeverityBadge(alert.severity)}`}>
                    {alert.severity}
                  </span>
                </div>

                <p className="font-medium text-gray-900 dark:text-white mb-1">
                  {alert.message}
                </p>

                <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                  <span>{alert.server}</span>
                  <span>•</span>
                  <span title={alert.timestamp}>
                    {new Date(alert.timestamp).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}

        {displayAlerts.length === 0 && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <CheckCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No alerts to display</p>
            <p className="text-sm mt-1">All systems are running smoothly</p>
          </div>
        )}
      </div>
    </div>
  );
}


