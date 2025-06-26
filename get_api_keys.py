#!/usr/bin/env python3
"""
Script to help you get API keys for real traffic data.
This will guide you through the process of obtaining and testing API keys.
"""

import os
import sys
import webbrowser
from pathlib import Path

def print_header():
    print("🌆 TrafficDetector - API Key Setup")
    print("=" * 60)
    print("This script will help you get API keys for real traffic data.")
    print()

def get_tomtom_key():
    print("🔑 TomTom API Key Setup")
    print("-" * 30)
    print("1. TomTom offers free traffic data with 60 requests/minute")
    print("2. Perfect for development and testing")
    print()
    
    choice = input("Would you like to get a TomTom API key? (y/n): ").lower().strip()
    
    if choice == 'y':
        print("🌐 Opening TomTom Developer Portal...")
        webbrowser.open("https://developer.tomtom.com/")
        print()
        print("📝 Steps to get your key:")
        print("   1. Create a free account")
        print("   2. Create a new application")
        print("   3. Copy your API key")
        print("   4. Add it to your .env file")
        print()
        
        key = input("Enter your TomTom API key (or press Enter to skip): ").strip()
        if key:
            return key
    
    return None

def get_here_key():
    print("🔑 HERE API Key Setup")
    print("-" * 30)
    print("1. HERE offers free traffic data with 250K requests/month")
    print("2. Good alternative to TomTom")
    print()
    
    choice = input("Would you like to get a HERE API key? (y/n): ").lower().strip()
    
    if choice == 'y':
        print("🌐 Opening HERE Developer Portal...")
        webbrowser.open("https://developer.here.com/")
        print()
        print("📝 Steps to get your key:")
        print("   1. Create a free account")
        print("   2. Create a new project")
        print("   3. Copy your API key")
        print("   4. Add it to your .env file")
        print()
        
        key = input("Enter your HERE API key (or press Enter to skip): ").strip()
        if key:
            return key
    
    return None

def update_env_file(tomtom_key=None, here_key=None):
    """Update the .env file with the provided API keys"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found! Creating from template...")
        template_file = Path("env_template.txt")
        if template_file.exists():
            with open(template_file, 'r') as f:
                content = f.read()
        else:
            print("❌ env_template.txt not found!")
            return False
    else:
        with open(env_file, 'r') as f:
            content = f.read()
    
    # Update TomTom key
    if tomtom_key:
        if "TOMTOM_API_KEY=your_tomtom_api_key_here" in content:
            content = content.replace("TOMTOM_API_KEY=your_tomtom_api_key_here", f"TOMTOM_API_KEY={tomtom_key}")
        elif "TOMTOM_API_KEY=" in content:
            # Replace existing key
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("TOMTOM_API_KEY="):
                    lines[i] = f"TOMTOM_API_KEY={tomtom_key}"
                    break
            content = '\n'.join(lines)
        else:
            content += f"\nTOMTOM_API_KEY={tomtom_key}"
    
    # Update HERE key
    if here_key:
        if "HERE_API_KEY=your_here_api_key_here" in content:
            content = content.replace("HERE_API_KEY=your_here_api_key_here", f"HERE_API_KEY={here_key}")
        elif "HERE_API_KEY=" in content:
            # Replace existing key
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("HERE_API_KEY="):
                    lines[i] = f"HERE_API_KEY={here_key}"
                    break
            content = '\n'.join(lines)
        else:
            content += f"\nHERE_API_KEY={here_key}"
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ Updated .env file with your API keys!")
    return True

def test_keys():
    """Test the API keys"""
    print("\n🧪 Testing your API keys...")
    print("(This will test the keys without making actual API calls)")
    
    try:
        sys.path.insert(0, str(Path.cwd()))
        from app.core.config import settings
        
        tomtom_configured = (settings.tomtom_api_key and 
                           settings.tomtom_api_key != "your_tomtom_api_key_here")
        here_configured = (settings.here_api_key and 
                          settings.here_api_key != "your_here_api_key_here")
        
        if tomtom_configured:
            print("✅ TomTom API key configured")
        else:
            print("❌ TomTom API key not configured")
        
        if here_configured:
            print("✅ HERE API key configured")
        else:
            print("❌ HERE API key not configured")
        
        if tomtom_configured or here_configured:
            print("\n🎉 You're ready to collect real traffic data!")
            return True
        else:
            print("\n⚠️  No API keys configured. You'll need at least one to get real data.")
            return False
            
    except Exception as e:
        print(f"❌ Error testing keys: {e}")
        return False

def print_next_steps():
    print("\n" + "=" * 60)
    print("🚀 NEXT STEPS")
    print("=" * 60)
    print("1. Restart the server:")
    print("   python3 -m app.main")
    print()
    print("2. Test traffic collection:")
    print("   curl -X GET 'http://localhost:8000/api/v1/traffic/collect/Atlanta'")
    print()
    print("3. Collect data for multiple locations:")
    print("   python3 collect_traffic_data.py")
    print()
    print("4. Analyze hotspots:")
    print("   curl 'http://localhost:8000/api/v1/traffic/hotspots/90days?region=Atlanta'")
    print()
    print("📖 See REAL_TRAFFIC_DATA_GUIDE.md for detailed instructions")

def main():
    print_header()
    
    # Get API keys
    tomtom_key = get_tomtom_key()
    here_key = get_here_key()
    
    # Update .env file
    if tomtom_key or here_key:
        update_env_file(tomtom_key, here_key)
    else:
        print("⚠️  No API keys provided. You can add them manually to .env file later.")
    
    # Test keys
    keys_working = test_keys()
    
    # Print next steps
    print_next_steps()
    
    if keys_working:
        print("\n🎯 You're all set! Start collecting real traffic data.")
    else:
        print("\n💡 Get API keys from the developer portals and add them to .env file.")

if __name__ == "__main__":
    main() 