import { DatabaseStatus as DatabaseStatusType } from '@/types/monitoring';
import { Database, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

interface DatabaseStatusProps {
  databases: DatabaseStatusType[];
}

export function DatabaseStatus({ databases }: DatabaseStatusProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'up':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'down':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      up: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      down: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      error: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    };
    return badges[status as keyof typeof badges] || badges.error;
  };

  const getDbIcon = (type: string) => {
    // You can customize icons per database type
    return <Database className="w-5 h-5" />;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <Database className="w-6 h-6 text-blue-600 dark:text-blue-400" />
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Databases</h2>
      </div>

      <div className="space-y-3">
        {databases.map((db) => (
          <div
            key={db.type}
            className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <div className="flex items-center gap-3">
              {getDbIcon(db.type)}
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-gray-900 dark:text-white capitalize">
                    {db.type}
                  </h3>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getStatusBadge(db.status)}`}>
                    {db.status.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {db.status === 'up' ? (
                    <>
                      {db.databases} {db.databases === 1 ? 'database' : 'databases'}
                      {db.tables !== undefined && ` • ${db.tables} tables`}
                      {db.collections !== undefined && ` • ${db.collections} collections`}
                    </>
                  ) : (
                    <span className="text-red-500">{db.error || 'Connection failed'}</span>
                  )}
                </p>
              </div>
            </div>
            {getStatusIcon(db.status)}
          </div>
        ))}

        {databases.length === 0 && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Database className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No databases configured</p>
          </div>
        )}
      </div>
    </div>
  );
}










