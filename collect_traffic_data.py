#!/usr/bin/env python3
"""
Script to collect real traffic data for Atlanta metro area locations.
This will help build up the database for hotspot analysis.
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List
import time
from app.data.traffic_hotspots_atlanta import ATLANTA_HOTSPOT_LOCATIONS

# Use real Atlanta traffic hotspots
ATLANTA_LOCATIONS = ATLANTA_HOTSPOT_LOCATIONS

async def collect_traffic_data_for_location(session: aiohttp.ClientSession, location: str) -> dict:
    """Collect traffic data for a single location"""
    try:
        url = f"http://localhost:8000/api/v1/traffic/collect/{location.replace(' ', '%20')}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Collected data for {location}: {data['data_points']} data points")
                return {"location": location, "status": "success", "data": data}
            else:
                error_text = await response.text()
                print(f"❌ Failed to collect data for {location}: {response.status} - {error_text}")
                return {"location": location, "status": "error", "error": error_text}
    except Exception as e:
        print(f"❌ Error collecting data for {location}: {str(e)}")
        return {"location": location, "status": "error", "error": str(e)}

async def collect_traffic_data_batch(locations: List[str], batch_size: int = 5):
    """Collect traffic data for multiple locations in batches"""
    print(f"🚀 Starting traffic data collection for {len(locations)} locations...")
    print(f"📊 Batch size: {batch_size}")
    print("-" * 60)
    
    async with aiohttp.ClientSession() as session:
        results = []
        
        # Process in batches to avoid overwhelming the API
        for i in range(0, len(locations), batch_size):
            batch = locations[i:i + batch_size]
            print(f"\n📦 Processing batch {i//batch_size + 1}: {batch}")
            
            # Collect data for this batch
            batch_tasks = [collect_traffic_data_for_location(session, loc) for loc in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
            
            # Wait between batches to be respectful to the API
            if i + batch_size < len(locations):
                print("⏳ Waiting 2 seconds before next batch...")
                await asyncio.sleep(2)
        
        return results

async def main():
    """Main function to collect traffic data"""
    print("🌆 Atlanta Traffic Data Collector")
    print("=" * 60)
    print(f"📍 Target locations: {len(ATLANTA_LOCATIONS)}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Collect traffic data
    results = await collect_traffic_data_batch(ATLANTA_LOCATIONS, batch_size=3)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COLLECTION SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        total_data_points = sum(r["data"]["data_points"] for r in successful)
        print(f"📈 Total data points collected: {total_data_points}")
    
    if failed:
        print("\n❌ Failed locations:")
        for result in failed:
            print(f"   - {result['location']}: {result['error']}")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test hotspots endpoint
    print("\n" + "=" * 60)
    print("🔥 TESTING HOTSPOTS ENDPOINT")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test 90-day hotspots
            url = "http://localhost:8000/api/v1/traffic/hotspots/90days?region=Atlanta"
            async with session.get(url) as response:
                if response.status == 200:
                    hotspots_data = await response.json()
                    print("✅ 90-day hotspots endpoint working!")
                    print(f"📍 Found {hotspots_data.get('hotspots_found', 0)} hotspots")
                    print(f"📊 Total data points: {hotspots_data.get('total_data_points', 0)}")
                    
                    if hotspots_data.get('hotspots'):
                        print("\n🏆 Top 5 hotspots:")
                        for i, hotspot in enumerate(hotspots_data['hotspots'][:5], 1):
                            print(f"   {i}. {hotspot['location']} - Score: {hotspot['hotspot_score']:.3f}")
                else:
                    error_text = await response.text()
                    print(f"❌ Hotspots endpoint failed: {response.status} - {error_text}")
    except Exception as e:
        print(f"❌ Error testing hotspots: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 