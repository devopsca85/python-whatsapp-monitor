// Core monitoring types

export interface ServerStatus {
  ip: string;
  name?: string;
  status: 'up' | 'down' | 'slow' | 'warning';
  cpu: number;
  ram: number;
  disk: number;
  responseTime: number;
  lastCheck: string;
  uptime?: string;
  websites?: WebsiteStatus[];
  serverType?: 'new-staging' | 'windows' | 'old-staging';
  sqlJobs?: {
    total: number;
    running: number;
    failed: number;
    succeeded: number;
  };
  services?: {
    mysql?: { status: 'up' | 'down' | 'error'; databases: number; tables: number };
    postgresql?: { status: 'up' | 'down' | 'error'; databases: number; tables: number };
    mongodb?: { status: 'up' | 'down' | 'error'; databases: number; collections: number };
    mssql?: { status: 'up' | 'down' | 'error'; databases: number; tables: number };
  };
}

export interface DatabaseStatus {
  server: string;
  type: 'mysql' | 'postgresql' | 'mongodb';
  status: 'up' | 'down' | 'error';
  databases: number;
  tables?: number;
  collections?: number;
  error?: string;
  lastCheck?: string;
}

export interface WebsiteStatus {
  url: string;
  status: 'up' | 'down' | 'slow' | 'unknown';
  responseTime: number;
  lastCheck: string;
  statusCode?: number;
  error?: string;
}

export interface Alert {
  id: string;
  timestamp: string;
  server: string;
  type: 'critical' | 'warning' | 'info' | 'recovery';
  category: 'server' | 'database' | 'website';
  message: string;
  severity: 'high' | 'medium' | 'low';
}

export interface MonitoringConfig {
  servers: string[];
  apiTokens: Record<string, string>;
  apiEndpoints: Record<string, string>;
  thresholds: {
    cpu: number;
    memory: number;
    disk: number;
    responseTime: number;
  };
  checkIntervals: {
    server: number;
    database: number;
    website: number;
  };
  whatsapp: {
    enabled: boolean;
    numbers: string[];
  };
}

export interface DashboardSummary {
  servers: ServerStatus[];
  alerts: Alert[];
  stats: {
    totalServers: number;
    serversUp: number;
    serversDown: number;
    serversSlow: number;
    totalAlerts24h: number;
    criticalAlerts: number;
    warningAlerts: number;
    recoveryAlerts: number;
    avgUptime: number;
  };
}

export interface MetricDataPoint {
  timestamp: string;
  cpu: number;
  ram: number;
  disk: number;
  responseTime: number;
}

export interface PerformanceData {
  server: string;
  metrics: MetricDataPoint[];
}


