#!/usr/bin/env python3
"""
Server Monitor - Monitors server on port 80 and sends WhatsApp notifications
when the server goes down.

Author: AI Assistant
Date: 2024
"""

import socket
import time
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
import requests
from pathlib import Path

# Import our custom modules
from whatsapp_notifier import WhatsAppNotifier
from config_manager import ConfigManager


class ServerMonitor:
    """
    Main server monitoring class that checks server availability
    and sends notifications when issues are detected.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the server monitor.
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()
        self.whatsapp = WhatsAppNotifier(self.config)
        
        # Setup logging
        self._setup_logging()
        
        # Monitoring state
        self.last_status = True  # True = up, False = down
        self.downtime_start = None
        self.notification_sent = False
        
        self.logger.info("Server Monitor initialized successfully")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.get('logging', {}).get('level', 'INFO').upper())
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('server_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_server_status(self) -> bool:
        """
        Check if the server is responding on the specified port.
        
        Returns:
            bool: True if server is up, False if down
        """
        server_config = self.config['server']
        host = server_config['host']
        port = server_config['port']
        timeout = server_config.get('timeout', 5)
        
        try:
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            # Attempt to connect
            result = sock.connect_ex((host, port))
            sock.close()
            
            return result == 0
            
        except Exception as e:
            self.logger.error(f"Error checking server status: {e}")
            return False
    
    def send_downtime_notification(self):
        """Send WhatsApp notification about server downtime."""
        if self.notification_sent:
            return
        
        try:
            server_config = self.config['server']
            downtime_duration = self._calculate_downtime_duration()
            
            message = self._format_downtime_message(downtime_duration)
            
            # Send WhatsApp notification
            success = self.whatsapp.send_message(message)
            
            if success:
                self.notification_sent = True
                self.logger.info("Downtime notification sent successfully")
            else:
                self.logger.error("Failed to send downtime notification")
                
        except Exception as e:
            self.logger.error(f"Error sending downtime notification: {e}")
    
    def send_recovery_notification(self):
        """Send WhatsApp notification about server recovery."""
        try:
            downtime_duration = self._calculate_downtime_duration()
            message = self._format_recovery_message(downtime_duration)
            
            # Send WhatsApp notification
            success = self.whatsapp.send_message(message)
            
            if success:
                self.logger.info("Recovery notification sent successfully")
            else:
                self.logger.error("Failed to send recovery notification")
                
        except Exception as e:
            self.logger.error(f"Error sending recovery notification: {e}")
    
    def _calculate_downtime_duration(self) -> str:
        """Calculate the duration of downtime."""
        if not self.downtime_start:
            return "Unknown"
        
        duration = datetime.now() - self.downtime_start
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        seconds = int(duration.total_seconds() % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _format_downtime_message(self, duration: str) -> str:
        """Format the downtime notification message."""
        server_config = self.config['server']
        host = server_config['host']
        port = server_config['port']
        
        return (
            f"🚨 SERVER DOWN ALERT 🚨\n\n"
            f"Server: {host}:{port}\n"
            f"Status: DOWN\n"
            f"Downtime Duration: {duration}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Please check the server immediately!"
        )
    
    def _format_recovery_message(self, duration: str) -> str:
        """Format the recovery notification message."""
        server_config = self.config['server']
        host = server_config['host']
        port = server_config['port']
        
        return (
            f"✅ SERVER RECOVERED ✅\n\n"
            f"Server: {host}:{port}\n"
            f"Status: UP\n"
            f"Total Downtime: {duration}\n"
            f"Recovery Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Server is now operational."
        )
    
    def run_monitoring_loop(self):
        """Main monitoring loop."""
        self.logger.info("Starting server monitoring...")
        
        check_interval = self.config.get('monitoring', {}).get('check_interval', 30)
        
        try:
            while True:
                current_status = self.check_server_status()
                
                # Log current status
                status_text = "UP" if current_status else "DOWN"
                self.logger.info(f"Server status: {status_text}")
                
                # Handle status changes
                if current_status != self.last_status:
                    if not current_status:  # Server went down
                        self.downtime_start = datetime.now()
                        self.notification_sent = False
                        self.logger.warning("Server is DOWN!")
                        self.send_downtime_notification()
                    else:  # Server came back up
                        self.logger.info("Server is UP!")
                        self.send_recovery_notification()
                        self.downtime_start = None
                        self.notification_sent = False
                
                self.last_status = current_status
                
                # Wait before next check
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error in monitoring loop: {e}")


def main():
    """Main entry point."""
    print("🚀 Starting Server Monitor...")
    print("Press Ctrl+C to stop monitoring")
    print("-" * 50)
    
    try:
        monitor = ServerMonitor()
        monitor.run_monitoring_loop()
    except Exception as e:
        print(f"Error starting server monitor: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

