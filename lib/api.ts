import axios, { AxiosInstance } from 'axios';
import type { DashboardSummary, MonitoringConfig, Alert, PerformanceData } from '@/types/monitoring';

class MonitoringAPI {
  private clients: Map<string, AxiosInstance> = new Map();
  private tokens: Map<string, string> = new Map();

  constructor() {
    // Configure multiple servers
    const servers = {
      'ubuntu': {
        url: process.env.NEXT_PUBLIC_API_URL_UBUNTU || 'http://192.168.1.19:5000/api',
        token: process.env.NEXT_PUBLIC_API_TOKEN_UBUNTU || 'mL0OIR28R1UL9Y2miGenl3i6JQxAemjl'
      },
      'windows': {
        url: process.env.NEXT_PUBLIC_API_URL_WINDOWS || 'http://192.168.1.116:5000/api',
        token: process.env.NEXT_PUBLIC_API_TOKEN_WINDOWS || 'sq98B4kGFQmv6NZjdP9ZISPRULXFXiiT'
      },
      'old-staging': {
        url: process.env.NEXT_PUBLIC_API_URL_OLD_STAGING || 'http://135.148.164.94:5000/api',
        token: process.env.NEXT_PUBLIC_API_TOKEN_OLD_STAGING || 'default_token'
      }
    };

    // Create clients for each server
    Object.entries(servers).forEach(([name, config]) => {
      // Use longer timeout for staging server as it may be slower
      const timeout = name === 'old-staging' ? 30000 : 15000; // 30s for staging, 15s for others
      
      const client = axios.create({
        baseURL: config.url,
        timeout: timeout,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      // Add auth interceptor
      client.interceptors.request.use((config) => {
        config.headers.Authorization = `Bearer ${servers[name as keyof typeof servers].token}`;
        return config;
      });

      this.clients.set(name, client);
      this.tokens.set(name, config.token);
    });
  }

  setToken(serverName: string, token: string) {
    this.tokens.set(serverName, token);
    if (typeof window !== 'undefined') {
      localStorage.setItem(`api_token_${serverName}`, token);
    }
  }

  getToken(serverName: string): string {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(`api_token_${serverName}`) || this.tokens.get(serverName) || '';
    }
    return this.tokens.get(serverName) || '';
  }

  setBaseURL(serverName: string, url: string) {
    const client = this.clients.get(serverName);
    if (client) {
      client.defaults.baseURL = url;
      if (typeof window !== 'undefined') {
        localStorage.setItem(`api_url_${serverName}`, url);
      }
    }
  }

  // Dashboard endpoints
  async getDashboardSummary(): Promise<DashboardSummary> {
    try {
      const allServers: any[] = [];
      const allAlerts: any[] = [];
      
      // Get data from all servers
      for (const [serverName, client] of this.clients) {
        try {
          let retries = 0;
          const maxRetries = serverName === 'old-staging' ? 2 : 1; // More retries for staging
          let success = false;
          
          while (retries <= maxRetries && !success) {
            try {
              const response = await client.get('/dashboard/summary', {
                timeout: serverName === 'old-staging' ? 30000 : 15000,
                validateStatus: () => true // Don't throw on HTTP errors
              });
              
              // Check if response is successful
              if (response.status >= 200 && response.status < 300) {
                const data = response.data;
              
                // Add server name to identify source
                if (data.servers) {
                  data.servers.forEach((server: any) => {
                    server.serverType = serverName;
                    // Add friendly names if not present
                    if (!server.name) {
                      if (serverName === 'ubuntu') {
                        server.name = server.ip === '192.168.1.19' ? 'Ubuntu Server 1' : 'Ubuntu Server 2';
                      } else if (serverName === 'windows') {
                        server.name = 'Windows Server';
                      } else if (serverName === 'old-staging') {
                        server.name = 'Old Staging Server';
                      }
                    }
                    allServers.push(server);
                  });
                }
              
                if (data.alerts) {
                  data.alerts.forEach((alert: any) => {
                    alert.serverType = serverName;
                    allAlerts.push(alert);
                  });
                }
                
                success = true; // Mark as successful
                break; // Exit retry loop
              }
            } catch (error: any) {
              const errorMessage = String(error?.message || '');
              const errorCode = String(error?.code || '');
              const errorString = String(error || '');
              
              // Check for various network error types
              const isTimeout = errorCode === 'ECONNABORTED' || 
                               errorMessage.toLowerCase().includes('timeout') || 
                               errorString.toLowerCase().includes('timeout');
              
              const isNetworkError = !error.response && (
                error.request || 
                errorCode === 'ECONNREFUSED' ||
                errorCode === 'ENOTFOUND' ||
                errorCode === 'EHOSTUNREACH' ||
                errorCode === 'ETIMEDOUT' ||
                errorCode === 'ERR_NETWORK' ||
                errorMessage.toLowerCase().includes('network error') ||
                errorMessage.toLowerCase().includes('networkerror') ||
                errorMessage.toLowerCase().includes('err_network') ||
                errorMessage.toLowerCase().includes('failed to fetch') ||
                errorMessage.toLowerCase().includes('connection refused') ||
                errorMessage.toLowerCase().includes('connectionerror') ||
                errorMessage.toLowerCase().includes('getaddrinfo') ||
                errorString.toLowerCase().includes('network error')
              );
              
              // Retry on timeout or network errors (but not on 4xx/5xx)
              if (retries < maxRetries && (isTimeout || isNetworkError)) {
                retries++;
                console.warn(`Retry ${retries}/${maxRetries} for ${serverName} due to ${isTimeout ? 'timeout' : 'network error'}: ${errorMessage}`);
                // Wait a bit before retrying (exponential backoff)
                await new Promise(resolve => setTimeout(resolve, 1000 * retries));
                continue; // Try again
              }
              
              // Handle final error or non-retryable error
              if (retries >= maxRetries || (!isTimeout && !isNetworkError)) {
                // Log as warning for network errors (expected), error for unexpected issues
                if (isNetworkError || isTimeout) {
                  console.warn(`Server ${serverName} unreachable after ${retries} retries: ${errorMessage || 'Network error'}`);
                } else {
                  console.error(`Error fetching data from ${serverName} after ${retries} retries:`, errorMessage || error);
                }
                break; // Exit retry loop
              }
            }
          }
          
          // If all retries failed, add offline server
          if (!success) {
            let offlineIp = 'unknown';
            let offlineName = 'Unknown Server';
            
            if (serverName === 'ubuntu') {
              offlineIp = '192.168.1.19';
              offlineName = 'Ubuntu Server';
            } else if (serverName === 'windows') {
              offlineIp = '192.168.1.116';
              offlineName = 'Windows Server';
            } else if (serverName === 'old-staging') {
              offlineIp = '135.148.164.94';
              offlineName = 'Old Staging Server';
            }
            
            allServers.push({
              ip: offlineIp,
              name: offlineName,
              status: 'down',
              serverType: serverName,
              cpu: 0,
              ram: 0,
              disk: 0,
              responseTime: 0,
              lastCheck: new Date().toISOString(),
              services: {
                mysql: { status: 'down', databases: 0, tables: 0 },
                postgresql: { status: 'down', databases: 0, tables: 0 },
                mongodb: { status: 'down', databases: 0, collections: 0 }
              }
            });
          }
        } catch (outerError: any) {
          // Catch any unexpected errors to prevent dashboard crash
          console.error(`Unexpected error for server ${serverName}:`, outerError);
          // Continue to next server
        }
      }
      
      // Calculate aggregated stats
      const stats = {
        totalServers: allServers.length,
        serversUp: allServers.filter(s => s.status === 'up').length,
        serversDown: allServers.filter(s => s.status === 'down').length,
        serversSlow: allServers.filter(s => s.status === 'slow').length,
        totalAlerts24h: allAlerts.length,
        criticalAlerts: allAlerts.filter(a => a.severity === 'high').length,
        warningAlerts: allAlerts.filter(a => a.severity === 'medium').length,
        recoveryAlerts: allAlerts.filter(a => a.type === 'recovery').length,
        avgUptime: allServers.reduce((sum, s) => sum + (s.uptime || 0), 0) / allServers.length || 0
      };
      
      return {
        servers: allServers,
        alerts: allAlerts.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()),
        stats
      };
    } catch (error: any) {
      console.error('Error fetching dashboard summary:', error);
      // Return empty dashboard instead of throwing to prevent crash
      return {
        servers: [],
        alerts: [],
        stats: {
          totalServers: 0,
          serversUp: 0,
          serversDown: 0,
          serversSlow: 0,
          totalAlerts24h: 0,
          criticalAlerts: 0,
          warningAlerts: 0,
          recoveryAlerts: 0,
          avgUptime: 0
        }
      };
    }
  }

  async getAlerts(limit = 50): Promise<Alert[]> {
    try {
      const allAlerts: any[] = [];
      
      // Get alerts from both servers
      for (const [serverName, client] of this.clients) {
        try {
          const response = await client.get('/dashboard/alerts', {
            params: { limit }
          });
          const alerts = response.data.alerts || response.data || [];
          alerts.forEach((alert: any) => {
            alert.serverType = serverName;
            allAlerts.push(alert);
          });
        } catch (error) {
          console.error(`Error fetching alerts from ${serverName}:`, error);
        }
      }
      
      return allAlerts.slice(0, limit);
    } catch (error) {
      console.error('Error fetching alerts:', error);
      throw error;
    }
  }

  async getConfig(): Promise<MonitoringConfig> {
    try {
      // Try to get config from Ubuntu server first
      const ubuntuClient = this.clients.get('ubuntu');
      if (ubuntuClient) {
        const response = await ubuntuClient.get('/dashboard/config');
        return response.data;
      }
      throw new Error('No Ubuntu client available');
    } catch (error) {
      console.error('Error fetching config:', error);
      throw error;
    }
  }

  async updateConfig(config: Partial<MonitoringConfig>): Promise<{ status: string }> {
    try {
      // Try to update config on Ubuntu server first
      const ubuntuClient = this.clients.get('ubuntu');
      if (ubuntuClient) {
        const response = await ubuntuClient.post('/dashboard/config', config);
        return response.data;
      }
      throw new Error('No Ubuntu client available');
    } catch (error) {
      console.error('Error updating config:', error);
      throw error;
    }
  }

  async getPerformanceData(server: string, hours = 24): Promise<PerformanceData> {
    try {
      let serverName = 'ubuntu'; // default
      if (server === '192.168.1.19') {
        serverName = 'ubuntu';
      } else if (server === '192.168.1.116') {
        serverName = 'windows';
      } else if (server === '135.148.164.94') {
        serverName = 'old-staging';
      }
      
      const client = this.clients.get(serverName);
      
      if (!client) {
        throw new Error(`No client configured for server: ${serverName}`);
      }
      
      const response = await client.get('/dashboard/performance', {
        params: { server, hours },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching performance data:', error);
      throw error;
    }
  }

  async testConnection(target: { type: 'server' | 'database' | 'website'; address: string }) {
    try {
      // Try Ubuntu server first
      const ubuntuClient = this.clients.get('ubuntu');
      if (ubuntuClient) {
        const response = await ubuntuClient.post('/dashboard/test-connection', target);
        return response.data;
      }
      throw new Error('No Ubuntu client available');
    } catch (error) {
      console.error('Error testing connection:', error);
      throw error;
    }
  }

  async sendTestAlert(message: string) {
    try {
      // Try Ubuntu server first
      const ubuntuClient = this.clients.get('ubuntu');
      if (ubuntuClient) {
        const response = await ubuntuClient.post('/dashboard/test-alert', { message });
        return response.data;
      }
      throw new Error('No Ubuntu client available');
    } catch (error) {
      console.error('Error sending test alert:', error);
      throw error;
    }
  }

  async getServerDetails(serverIp: string) {
    try {
      // Determine which server to query based on IP
      let serverName = 'ubuntu';
      if (serverIp === '192.168.1.19') serverName = 'ubuntu';
      else if (serverIp === '192.168.1.116') serverName = 'windows';
      else if (serverIp === '135.148.164.94') serverName = 'old-staging';

      const client = this.clients.get(serverName);
      if (!client) throw new Error(`No client configured for server: ${serverName}`);

      let retries = serverName === 'old-staging' ? 2 : 1;
      while (retries >= 0) {
        try {
          const response = await client.get(`/dashboard/server/${serverIp}` as const, {
            timeout: serverName === 'old-staging' ? 30000 : 15000,
            validateStatus: () => true,
          });

          if (response.status >= 200 && response.status < 300) {
            const data = response.data;
            data.serverType = serverName;
            return data;
          }
        } catch (err: any) {
          const code = String(err?.code || '').toLowerCase();
          const msg = String(err?.message || '').toLowerCase();
          const isNetwork = !err?.response && (code.includes('econn') || code.includes('network') || msg.includes('timeout') || msg.includes('failed to fetch'));
          if (retries > 0 && isNetwork) {
            await new Promise(r => setTimeout(r, 1000));
            retries -= 1;
            continue;
          }
        }
        break;
      }

      // Graceful fallback to avoid unhandled errors in UI
      return {
        ip: serverIp,
        name: serverName === 'old-staging' ? 'Old Staging Server' : serverName === 'windows' ? 'Windows Server' : 'Ubuntu Server',
        status: 'down',
        serverType: serverName,
        cpu: 0,
        ram: 0,
        disk: 0,
        responseTime: 0,
        lastCheck: new Date().toISOString(),
        services: {
          mysql: { status: 'down', databases: 0, tables: 0 },
          postgresql: { status: 'down', databases: 0, tables: 0 },
          mongodb: { status: 'down', databases: 0, collections: 0 },
        },
      } as any;
    } catch (error) {
      console.error('Error fetching server details:', error);
      // Final defensive fallback
      return {
        ip: serverIp,
        name: 'Unknown Server',
        status: 'down',
        serverType: 'unknown',
      } as any;
    }
  }

  // Server health check (existing endpoint)
  async checkServerHealth(server: string): Promise<{ status: string; timestamp: string }> {
    try {
      let serverName = 'ubuntu'; // default
      if (server === '192.168.1.19') {
        serverName = 'ubuntu';
      } else if (server === '192.168.1.116') {
        serverName = 'windows';
      } else if (server === '135.148.164.94') {
        serverName = 'old-staging';
      }
      
      const client = this.clients.get(serverName);
      
      if (!client) {
        throw new Error(`No client configured for server: ${serverName}`);
      }
      
      const response = await client.get('/health');
      return response.data;
    } catch (error) {
      console.error('Error checking server health:', error);
      throw error;
    }
  }

  // System metrics (existing endpoint)
  async getSystemMetrics(): Promise<any> {
    try {
      // Try Ubuntu server first
      const ubuntuClient = this.clients.get('ubuntu');
      if (ubuntuClient) {
        const response = await ubuntuClient.get('/system');
        return response.data;
      }
      throw new Error('No Ubuntu client available');
    } catch (error) {
      console.error('Error fetching system metrics:', error);
      throw error;
    }
  }

  // Mock data methods for when API is not available
  private getMockSummary(): DashboardSummary {
    return {
      servers: [
        {
          ip: '192.168.1.219',
          status: 'up',
          cpu: 45,
          ram: 62,
          disk: 78,
          uptime: '15 days, 3 hours',
          lastCheck: new Date().toISOString(),
          responseTime: 120
        },
        {
          ip: '192.168.1.19',
          status: 'slow',
          cpu: 85,
          ram: 92,
          disk: 95,
          uptime: '2 days, 14 hours',
          lastCheck: new Date().toISOString(),
          responseTime: 2500
        }
      ],
      alerts: [],
      stats: {
        totalServers: 2,
        serversUp: 1,
        serversDown: 0,
        serversSlow: 1,
        totalAlerts24h: 3,
        criticalAlerts: 1,
        warningAlerts: 1,
        recoveryAlerts: 1,
        avgUptime: 92.5
      }
    };
  }

  private getMockAlerts(): Alert[] {
    return [
      {
        id: '1',
        type: 'critical',
        severity: 'high',
        category: 'database',
        message: 'MongoDB database is down',
        server: '192.168.1.219',
        timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString()
      },
      {
        id: '2',
        type: 'warning',
        severity: 'medium',
        category: 'server',
        message: 'High CPU usage detected',
        server: '192.168.1.19',
        timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString()
      },
      {
        id: '3',
        type: 'recovery',
        severity: 'low',
        category: 'website',
        message: 'Website recovered successfully',
        server: 'example.com',
        timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString()
      }
    ];
  }
}

// Export singleton instance
export const api = new MonitoringAPI();


