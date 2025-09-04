# 🚀 Quick Start Guide

Get your server monitoring system up and running in 5 minutes!

## 📋 Prerequisites
- Python 3.7 or higher
- WhatsApp account
- Server to monitor

## ⚡ Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure WhatsApp (Choose ONE method)

#### Option A: CallMeBot (Free & Easy)
1. Send `/start` to `+34 644 51 95 23` on WhatsApp
2. You'll receive an API key
3. Edit `config.json`:
   ```json
   "whatsapp": {
       "method": "callmebot",
       "api_key": "YOUR_API_KEY_FROM_WHATSAPP",
       "phone_number": "YOUR_PHONE_NUMBER"
   }
   ```

#### Option B: Twilio (Paid)
1. Sign up at [Twilio](https://www.twilio.com/)
2. Get Account SID and Auth Token
3. Edit `config.json`:
   ```json
   "whatsapp": {
       "method": "twilio",
       "account_sid": "YOUR_ACCOUNT_SID",
       "auth_token": "YOUR_AUTH_TOKEN",
       "phone_number": "YOUR_PHONE_NUMBER"
   }
   ```

### 3. Configure Server
Edit `config.json`:
```json
"server": {
    "host": "your-server-ip-or-domain.com",
    "port": 80,
    "timeout": 5
}
```

### 4. Test Setup
```bash
python test_setup.py
```

### 5. Start Monitoring
```bash
python server_monitor.py
```

## 🎯 What You'll Get

- **Real-time monitoring** of your server on port 80
- **Instant WhatsApp alerts** when server goes down
- **Recovery notifications** when server comes back up
- **Detailed logs** for troubleshooting

## 📱 Sample Messages

**Server Down:**
```
🚨 SERVER DOWN ALERT 🚨
Server: your-server.com:80
Status: DOWN
Downtime Duration: 2m 30s
Time: 2024-01-15 14:30:25
Please check the server immediately!
```

**Server Recovery:**
```
✅ SERVER RECOVERED ✅
Server: your-server.com:80
Status: UP
Total Downtime: 5m 45s
Recovery Time: 2024-01-15 14:35:10
Server is now operational.
```

## 🔧 Troubleshooting

### WhatsApp not working?
- Check API key and phone number
- Verify you sent `/start` to CallMeBot
- Test with: `python whatsapp_notifier.py`

### Server always showing as down?
- Verify server host and port
- Check if server is actually running
- Test connection manually

### Need help?
- Check `server_monitor.log` for errors
- Run `python test_setup.py` for diagnostics
- Review the full README.md for detailed instructions

---

**That's it! Your server monitoring system is ready! 🎉**


