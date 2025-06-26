#!/usr/bin/env python3
"""
Automated traffic data collection script for cloud deployment.
This script runs continuously and collects data at scheduled intervals.
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List
import time
import logging

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.data.traffic_hotspots_atlanta import ATLANTA_HOTSPOT_LOCATIONS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('traffic_collector.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuration
COLLECTION_INTERVAL_HOURS = int(os.getenv('COLLECTION_INTERVAL_HOURS', '1'))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '5'))
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

async def collect_traffic_data_for_location(session: aiohttp.ClientSession, location: str) -> dict:
    """Collect traffic data for a single location"""
    try:
        url = f"{API_BASE_URL}/api/v1/traffic/collect/{location.replace(' ', '%20')}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Collected data for {location}: {data['data_points']} data points")
                return {"location": location, "status": "success", "data": data}
            else:
                error_text = await response.text()
                logger.error(f"❌ Failed to collect data for {location}: {response.status} - {error_text}")
                return {"location": location, "status": "error", "error": error_text}
    except Exception as e:
        logger.error(f"❌ Error collecting data for {location}: {str(e)}")
        return {"location": location, "status": "error", "error": str(e)}

async def collect_traffic_data_batch(locations: List[str], batch_size: int = 5):
    """Collect traffic data for multiple locations in batches"""
    logger.info(f"🚀 Starting traffic data collection for {len(locations)} locations...")
    logger.info(f"📊 Batch size: {batch_size}")
    
    async with aiohttp.ClientSession() as session:
        results = []
        
        # Process in batches to avoid overwhelming the API
        for i in range(0, len(locations), batch_size):
            batch = locations[i:i + batch_size]
            logger.info(f"📦 Processing batch {i//batch_size + 1}: {batch}")
            
            # Collect data for this batch
            batch_tasks = [collect_traffic_data_for_location(session, loc) for loc in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
            
            # Wait between batches to be respectful to the API
            if i + batch_size < len(locations):
                logger.info("⏳ Waiting 2 seconds before next batch...")
                await asyncio.sleep(2)
        
        return results

async def test_hotspots_api():
    """Test the hotspots API"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_BASE_URL}/api/v1/traffic/hotspots/90days?region=Atlanta&min_congestion=0.1"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Hotspots API working!")
                    logger.info(f"📍 Found {data.get('hotspots_found', 0)} hotspots")
                    logger.info(f"📊 Total data points: {data.get('total_data_points', 0)}")
                    
                    if data.get('hotspots'):
                        logger.info("🏆 Top 5 hotspots:")
                        for i, hotspot in enumerate(data['hotspots'][:5], 1):
                            logger.info(f"   {i}. {hotspot['location']} - Score: {hotspot['hotspot_score']:.3f}")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Hotspots API failed: {response.status} - {error_text}")
    except Exception as e:
        logger.error(f"❌ Error testing hotspots: {str(e)}")

async def main_collection_cycle():
    """Main collection cycle"""
    logger.info("🌆 Atlanta Traffic Data Collector - Automated Mode")
    logger.info("=" * 60)
    logger.info(f"📍 Target locations: {len(ATLANTA_HOTSPOT_LOCATIONS)}")
    logger.info(f"⏰ Collection interval: {COLLECTION_INTERVAL_HOURS} hours")
    logger.info(f"🌐 API Base URL: {API_BASE_URL}")
    logger.info()
    
    # Collect traffic data
    results = await collect_traffic_data_batch(ATLANTA_HOTSPOT_LOCATIONS, BATCH_SIZE)
    
    # Summary
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]
    
    logger.info("=" * 60)
    logger.info("📊 COLLECTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Successful: {len(successful)}/{len(results)}")
    logger.info(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        total_data_points = sum(r["data"]["data_points"] for r in successful)
        logger.info(f"📈 Total data points collected: {total_data_points}")
    
    if failed:
        logger.info("❌ Failed locations:")
        for result in failed:
            logger.info(f"   - {result['location']}: {result['error']}")
    
    logger.info(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test hotspots endpoint
    logger.info("=" * 60)
    logger.info("🔥 TESTING HOTSPOTS ENDPOINT")
    logger.info("=" * 60)
    await test_hotspots_api()

async def continuous_collection():
    """Run continuous collection with intervals"""
    logger.info("🚀 Starting continuous traffic data collection...")
    logger.info(f"⏰ Will collect data every {COLLECTION_INTERVAL_HOURS} hours")
    
    while True:
        try:
            await main_collection_cycle()
            
            # Wait for next collection cycle
            next_collection = datetime.now() + timedelta(hours=COLLECTION_INTERVAL_HOURS)
            logger.info(f"⏰ Next collection scheduled for: {next_collection.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("😴 Sleeping until next collection...")
            
            await asyncio.sleep(COLLECTION_INTERVAL_HOURS * 3600)  # Convert hours to seconds
            
        except Exception as e:
            logger.error(f"❌ Error in collection cycle: {e}")
            logger.info("🔄 Retrying in 5 minutes...")
            await asyncio.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    # Check if we should run continuous collection or just once
    if os.getenv('CONTINUOUS_COLLECTION', 'false').lower() == 'true':
        asyncio.run(continuous_collection())
    else:
        asyncio.run(main_collection_cycle()) 