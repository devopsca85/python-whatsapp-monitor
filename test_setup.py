#!/usr/bin/env python3
"""
Test Setup Script - Validates all components of the server monitoring system.

Author: AI Assistant
Date: 2024
"""

import sys
import json
import socket
import requests
from pathlib import Path


def test_python_version():
    """Test Python version compatibility."""
    print("🐍 Testing Python version...")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.7+")
        return False


def test_dependencies():
    """Test required dependencies."""
    print("\n📦 Testing dependencies...")
    
    dependencies = ['requests', 'urllib3']
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} - Installed")
        except ImportError:
            print(f"❌ {dep} - Missing")
            missing.append(dep)
    
    if missing:
        print(f"\n💡 Install missing dependencies: pip install {' '.join(missing)}")
        return False
    
    return True


def test_config_file():
    """Test configuration file."""
    print("\n⚙️ Testing configuration file...")
    
    if not Path("config.json").exists():
        print("❌ config.json not found")
        return False
    
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        
        # Check required sections
        required_sections = ['server', 'monitoring', 'whatsapp']
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing section: {section}")
                return False
        
        # Check server configuration
        server = config['server']
        if not all(key in server for key in ['host', 'port']):
            print("❌ Server configuration incomplete")
            return False
        
        # Check WhatsApp configuration
        whatsapp = config['whatsapp']
        if not all(key in whatsapp for key in ['method', 'api_key', 'phone_number']):
            print("❌ WhatsApp configuration incomplete")
            return False
        
        print("✅ Configuration file valid")
        print(f"   Server: {server['host']}:{server['port']}")
        print(f"   WhatsApp method: {whatsapp['method']}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading config.json: {e}")
        return False


def test_server_connection():
    """Test server connection."""
    print("\n🖥️ Testing server connection...")
    
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        
        server = config['server']
        host = server['host']
        port = server['port']
        timeout = server.get('timeout', 5)
        
        print(f"   Connecting to {host}:{port}...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print("✅ Server connection successful")
            return True
        else:
            print("❌ Server connection failed")
            print("   This is normal if the server is not running")
            return False
            
    except Exception as e:
        print(f"❌ Error testing server connection: {e}")
        return False


def test_whatsapp_config():
    """Test WhatsApp configuration."""
    print("\n📱 Testing WhatsApp configuration...")
    
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        
        whatsapp = config['whatsapp']
        method = whatsapp['method']
        api_key = whatsapp['api_key']
        phone_number = whatsapp['phone_number']
        
        print(f"   Method: {method}")
        print(f"   Phone: {phone_number}")
        
        if api_key == "YOUR_API_KEY_HERE":
            print("❌ API key not configured")
            return False
        
        if phone_number == "YOUR_PHONE_NUMBER_HERE":
            print("❌ Phone number not configured")
            return False
        
        print("✅ WhatsApp configuration looks good")
        return True
        
    except Exception as e:
        print(f"❌ Error testing WhatsApp config: {e}")
        return False


def test_modules():
    """Test Python modules."""
    print("\n🔧 Testing Python modules...")
    
    modules = ['server_monitor', 'whatsapp_notifier', 'config_manager']
    missing = []
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}.py - Found")
        except ImportError:
            print(f"❌ {module}.py - Missing")
            missing.append(module)
    
    if missing:
        print(f"\n💡 Missing modules: {', '.join(missing)}")
        return False
    
    return True


def run_quick_test():
    """Run a quick test of the monitoring system."""
    print("\n🧪 Running quick system test...")
    
    try:
        from config_manager import ConfigManager
        from whatsapp_notifier import WhatsAppNotifier
        
        # Test configuration manager
        config_manager = ConfigManager()
        config = config_manager.load_config()
        print("✅ Configuration manager working")
        
        # Test WhatsApp notifier (without sending)
        whatsapp = WhatsAppNotifier(config)
        print("✅ WhatsApp notifier initialized")
        
        print("✅ Quick test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 Server Monitor Setup Test")
    print("=" * 40)
    
    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_dependencies),
        ("Configuration File", test_config_file),
        ("Server Connection", test_server_connection),
        ("WhatsApp Configuration", test_whatsapp_config),
        ("Python Modules", test_modules),
        ("Quick System Test", run_quick_test)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Summary")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Configure your WhatsApp API key in config.json")
        print("2. Test WhatsApp integration: python whatsapp_notifier.py")
        print("3. Start monitoring: python server_monitor.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Update config.json with your settings")
        print("- Ensure all Python files are in the same directory")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())


