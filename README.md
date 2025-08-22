# 🖥️ Server Monitor with WhatsApp Notifications

A Python-based server monitoring system that checks if a server is responding on port 80 and sends WhatsApp notifications to the server admin when the server goes down or recovers.

## 🚀 Features

- **Real-time Server Monitoring**: Continuously monitors server availability on port 80
- **WhatsApp Notifications**: Sends instant alerts via WhatsApp when server goes down
- **Recovery Alerts**: Notifies when server comes back online
- **Multiple WhatsApp Methods**: Supports various WhatsApp integration methods
- **Configurable Settings**: Easy configuration via JSON file
- **Comprehensive Logging**: Detailed logs for troubleshooting
- **Clean Architecture**: Modular, well-documented code

## 📋 Prerequisites

- Python 3.7 or higher
- Internet connection for WhatsApp notifications
- WhatsApp account for receiving notifications

## 🛠️ Installation

1. **Clone or download the project files**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application** (see Configuration section below)

## ⚙️ Configuration

### 1. Edit `config.json`

Update the configuration file with your settings:

```json
{
    "server": {
        "host": "your-server-ip-or-domain.com",
        "port": 80,
        "timeout": 5
    },
    "monitoring": {
        "check_interval": 30,
        "retry_attempts": 3,
        "retry_delay": 10
    },
    "whatsapp": {
        "method": "callmebot",
        "api_key": "YOUR_API_KEY_HERE",
        "phone_number": "YOUR_PHONE_NUMBER_HERE"
    }
}
```

### 2. WhatsApp Setup

Choose one of the following WhatsApp integration methods:

#### Option A: CallMeBot (Recommended - Free)
1. Go to [CallMeBot](https://www.callmebot.com/blog/free-api-whatsapp-messages/)
2. Send `/start` to `+34 644 51 95 23` on WhatsApp
3. Get your API key from the response
4. Update `config.json`:
   ```json
   "whatsapp": {
       "method": "callmebot",
       "api_key": "YOUR_CALLMEBOT_API_KEY",
       "phone_number": "YOUR_PHONE_NUMBER"
   }
   ```

#### Option B: Twilio WhatsApp API
1. Sign up for [Twilio](https://www.twilio.com/)
2. Get your Account SID and Auth Token
3. Update `config.json`:
   ```json
   "whatsapp": {
       "method": "twilio",
       "account_sid": "YOUR_ACCOUNT_SID",
       "auth_token": "YOUR_AUTH_TOKEN",
       "phone_number": "YOUR_PHONE_NUMBER"
   }
   ```

#### Option C: WhatsApp Business API
1. Set up WhatsApp Business API
2. Get your access token
3. Update `config.json`:
   ```json
   "whatsapp": {
       "method": "whatsapp_business_api",
       "api_key": "YOUR_ACCESS_TOKEN",
       "phone_number": "YOUR_PHONE_NUMBER"
   }
   ```

## 🚀 Usage

### 1. Test Configuration
```bash
python config_manager.py
```

### 2. Test WhatsApp Integration
```bash
python whatsapp_notifier.py
```

### 3. Start Monitoring
```bash
python server_monitor.py
```

### 4. Run in Background (Linux/Mac)
```bash
nohup python server_monitor.py > monitor.log 2>&1 &
```

### 5. Run as Windows Service
Use a service manager like `nssm` or create a Windows service.

## 📁 File Structure

```
├── server_monitor.py      # Main monitoring script
├── whatsapp_notifier.py   # WhatsApp notification module
├── config_manager.py      # Configuration management
├── config.json           # Configuration file
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── server_monitor.log   # Log file (created automatically)
```

## 🔧 Configuration Options

### Server Settings
- `host`: Server IP address or domain name
- `port`: Port to monitor (default: 80)
- `timeout`: Connection timeout in seconds

### Monitoring Settings
- `check_interval`: Time between checks in seconds
- `retry_attempts`: Number of retry attempts before marking as down
- `retry_delay`: Delay between retry attempts

### WhatsApp Settings
- `method`: Integration method (callmebot, twilio, whatsapp_business_api, ultramsg)
- `api_key`: API key for the chosen method
- `phone_number`: Your phone number for notifications

### Logging Settings
- `level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `file`: Log file name
- `max_size`: Maximum log file size
- `backup_count`: Number of backup log files

## 📱 WhatsApp Message Examples

### Downtime Alert
```
🚨 SERVER DOWN ALERT 🚨

Server: your-server.com:80
Status: DOWN
Downtime Duration: 2m 30s
Time: 2024-01-15 14:30:25

Please check the server immediately!
```

### Recovery Alert
```
✅ SERVER RECOVERED ✅

Server: your-server.com:80
Status: UP
Total Downtime: 5m 45s
Recovery Time: 2024-01-15 14:35:10

Server is now operational.
```

## 🐛 Troubleshooting

### Common Issues

1. **WhatsApp messages not sending**
   - Check API key and phone number
   - Verify WhatsApp integration setup
   - Check internet connection

2. **Server always showing as down**
   - Verify server host and port
   - Check firewall settings
   - Test connection manually

3. **Configuration errors**
   - Validate JSON syntax in `config.json`
   - Check required fields are present
   - Run `python config_manager.py` to test

### Log Files
- Check `server_monitor.log` for detailed error messages
- Log level can be changed in configuration

## 🔒 Security Considerations

- Keep API keys secure and don't commit them to version control
- Use environment variables for sensitive data in production
- Regularly update dependencies
- Monitor log files for suspicious activity

## 📈 Monitoring Best Practices

1. **Set appropriate check intervals** (30-60 seconds recommended)
2. **Use multiple monitoring locations** for redundancy
3. **Set up escalation procedures** for extended downtime
4. **Regularly test the monitoring system**
5. **Keep logs for historical analysis**

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this project.

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

If you encounter any issues:
1. Check the troubleshooting section
2. Review the log files
3. Test individual components
4. Create an issue with detailed information

---

**Happy Monitoring! 🚀**


