import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple';
}

export function StatsCard({ title, value, icon: Icon, trend, color = 'blue' }: StatsCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500 text-blue-600 dark:text-blue-400',
    green: 'bg-green-500 text-green-600 dark:text-green-400',
    red: 'bg-red-500 text-red-600 dark:text-red-400',
    yellow: 'bg-yellow-500 text-yellow-600 dark:text-yellow-400',
    purple: 'bg-purple-500 text-purple-600 dark:text-purple-400',
  };

  const bgColorClasses = {
    blue: 'bg-blue-100 dark:bg-blue-900/30',
    green: 'bg-green-100 dark:bg-green-900/30',
    red: 'bg-red-100 dark:bg-red-900/30',
    yellow: 'bg-yellow-100 dark:bg-yellow-900/30',
    purple: 'bg-purple-100 dark:bg-purple-900/30',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 sm:p-5 lg:p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400 truncate">{title}</p>
          <p className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mt-1 sm:mt-2">{value}</p>
          
          {trend && (
            <div className="flex items-center gap-1 mt-1 sm:mt-2">
              <span className={`text-xs font-medium ${trend.isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400 hidden sm:inline">vs last 24h</span>
            </div>
          )}
        </div>

        <div className={`p-2 sm:p-3 rounded-lg ${bgColorClasses[color]} flex-shrink-0`}>
          <Icon className={`w-5 h-5 sm:w-6 sm:h-6 ${colorClasses[color].split(' ')[1]}`} />
        </div>
      </div>
    </div>
  );
}








