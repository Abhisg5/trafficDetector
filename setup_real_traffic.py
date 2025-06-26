#!/usr/bin/env python3
"""
Setup script for real traffic data collection.
This script helps you configure API keys and test the setup.
"""

import os
import sys
import asyncio
import aiohttp
import ssl
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has API keys"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found!")
        print("📝 Creating .env file from template...")
        
        # Copy template
        template_file = Path("env_template.txt")
        if template_file.exists():
            with open(template_file, 'r') as f:
                template_content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(template_content)
            
            print("✅ Created .env file from template")
            print("🔑 Please edit .env file and add your API keys")
            return False
        else:
            print("❌ env_template.txt not found!")
            return False
    
    # Check for API keys
    with open(env_file, 'r') as f:
        content = f.read()
    
    has_tomtom = "TOMTOM_API_KEY=your_tomtom_api_key_here" not in content
    has_here = "HERE_API_KEY=your_here_api_key_here" not in content
    
    if not has_tomtom and not has_here:
        print("❌ No API keys configured!")
        print("🔑 Please add your API keys to .env file:")
        print("   - TOMTOM_API_KEY=your_key_here")
        print("   - HERE_API_KEY=your_key_here")
        return False
    
    print("✅ API keys found in .env file")
    if has_tomtom:
        print("   - TomTom API: Configured")
    if has_here:
        print("   - HERE API: Configured")
    
    return True

async def test_api_keys():
    """Test if API keys are working"""
    print("\n🧪 Testing API keys...")
    
    try:
        # Import settings after potential .env changes
        sys.path.insert(0, str(Path.cwd()))
        from app.core.config import settings
        
        # Create SSL context that doesn't verify certificates (for development)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        if settings.tomtom_api_key and settings.tomtom_api_key != "your_tomtom_api_key_here":
            print("🔑 Testing TomTom API...")
            # Test TomTom API
            url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
            params = {
                'key': settings.tomtom_api_key,
                'point': "33.7490,-84.3880",  # Atlanta coordinates
                'unit': 'KMPH'
            }
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'flowSegmentData' in data:
                            print("✅ TomTom API working!")
                        else:
                            print("⚠️  TomTom API responded but no traffic data for this location")
                    else:
                        print(f"❌ TomTom API error: {response.status}")
        else:
            print("⚠️  TomTom API key not configured")
        
        if settings.here_api_key and settings.here_api_key != "your_here_api_key_here":
            print("🔑 Testing HERE API...")
            # Test HERE API
            url = f"https://traffic.ls.hereapi.com/traffic/6.2/flow.json"
            params = {
                'apiKey': settings.here_api_key,
                'bbox': "33.7390,-84.3980,33.7590,-84.3780",  # Atlanta area
                'responseattributes': 'sh,fc'
            }
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'RWS' in data:
                            print("✅ HERE API working!")
                        else:
                            print("⚠️  HERE API responded but no traffic data for this location")
                    else:
                        print(f"❌ HERE API error: {response.status}")
        else:
            print("⚠️  HERE API key not configured")
            
    except Exception as e:
        print(f"❌ Error testing API keys: {e}")

async def test_traffic_collection():
    """Test traffic data collection"""
    print("\n🚗 Testing traffic data collection...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:8000/api/v1/traffic/collect/Atlanta"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Traffic collection working!")
                    print(f"   - Data points: {data.get('data_points', 0)}")
                    print(f"   - Sources: {data.get('sources', [])}")
                else:
                    error_text = await response.text()
                    print(f"❌ Traffic collection failed: {response.status}")
                    print(f"   - Error: {error_text}")
    except Exception as e:
        print(f"❌ Error testing traffic collection: {e}")

async def test_hotspots_api():
    """Test hotspots API"""
    print("\n🔥 Testing hotspots API...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:8000/api/v1/traffic/hotspots/90days?region=Atlanta&min_congestion=0.1"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Hotspots API working!")
                    print(f"   - Total data points: {data.get('total_data_points', 0)}")
                    print(f"   - Hotspots found: {data.get('hotspots_found', 0)}")
                    print(f"   - Average congestion: {data.get('average_region_congestion', 0)}")
                else:
                    error_text = await response.text()
                    print(f"❌ Hotspots API failed: {response.status}")
                    print(f"   - Error: {error_text}")
    except Exception as e:
        print(f"❌ Error testing hotspots API: {e}")

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*60)
    print("🚀 NEXT STEPS")
    print("="*60)
    print("1. Get API keys:")
    print("   - TomTom: https://developer.tomtom.com/")
    print("   - HERE: https://developer.here.com/")
    print()
    print("2. Add API keys to .env file")
    print()
    print("3. Restart the server:")
    print("   python3 -m app.main")
    print()
    print("4. Collect traffic data:")
    print("   python3 collect_traffic_data.py")
    print()
    print("5. Analyze hotspots:")
    print("   curl 'http://localhost:8000/api/v1/traffic/hotspots/90days?region=Atlanta'")
    print()
    print("📖 See REAL_TRAFFIC_DATA_GUIDE.md for detailed instructions")

async def main():
    """Main setup function"""
    print("🌆 TrafficDetector - Real Data Setup")
    print("="*60)
    
    # Check environment
    env_ok = check_env_file()
    
    # Test API keys
    await test_api_keys()
    
    # Test traffic collection (if server is running)
    try:
        await test_traffic_collection()
    except:
        print("⚠️  Server not running - start with: python3 -m app.main")
    
    # Test hotspots API (if server is running)
    try:
        await test_hotspots_api()
    except:
        print("⚠️  Server not running - start with: python3 -m app.main")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    asyncio.run(main()) 