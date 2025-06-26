import asyncio
import aiohttp
import json
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import sqlite3
import threading

from app.core.config import settings
from app.core.database import SessionLocal, TrafficData
from app.data.traffic_collector import TrafficCollector
from app.services.real_estate_service import RealEstateService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CollectionTask:
    location: str
    frequency_hours: int
    last_collected: Optional[datetime]
    is_active: bool
    priority: int  # 1=high, 2=medium, 3=low


class HistoricalDataCollector:
    def __init__(self):
        self.traffic_collector = TrafficCollector()
        self.real_estate_service = RealEstateService()
        self.collection_tasks: List[CollectionTask] = []
        self.is_running = False
        self.session = None
        
        # Rate limiting
        self.request_count = 0
        self.last_request_time = datetime.now()
        self.rate_limit_per_minute = 60  # Default rate limit
        
        # Atlanta locations to monitor
        self.atlanta_locations = [
            "Atlanta, GA",
            "Sandy Springs, GA",
            "Roswell, GA",
            "Alpharetta, GA",
            "Marietta, GA",
            "Decatur, GA",
            "Johns Creek, GA",
            "Duluth, GA",
            "Smyrna, GA",
            "Norcross, GA",
            "Peachtree Corners, GA",
            "Brookhaven, GA",
            "Dunwoody, GA",
            "Kennesaw, GA",
            "Woodstock, GA",
            "Lawrenceville, GA",
            "Stone Mountain, GA",
            "College Park, GA",
            "East Point, GA",
            "Tucker, GA"
        ]
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def initialize_collection_tasks(self):
        """Initialize collection tasks for Atlanta area"""
        # High priority locations (downtown, major suburbs) - collect every hour
        high_priority = ["Atlanta, GA", "Sandy Springs, GA", "Alpharetta, GA", "Marietta, GA"]
        
        # Medium priority locations - collect every 3 hours
        medium_priority = ["Decatur, GA", "Johns Creek, GA", "Duluth, GA", "Smyrna, GA", "Brookhaven, GA", "Dunwoody, GA"]
        
        # Low priority locations - collect every 6 hours
        low_priority = ["Roswell, GA", "Norcross, GA", "Peachtree Corners, GA", "Kennesaw, GA", "Woodstock, GA", 
                       "Lawrenceville, GA", "Stone Mountain, GA", "College Park, GA", "East Point, GA", "Tucker, GA"]
        
        for location in high_priority:
            self.collection_tasks.append(CollectionTask(
                location=location,
                frequency_hours=1,
                last_collected=None,
                is_active=True,
                priority=1
            ))
        
        for location in medium_priority:
            self.collection_tasks.append(CollectionTask(
                location=location,
                frequency_hours=3,
                last_collected=None,
                is_active=True,
                priority=2
            ))
        
        for location in low_priority:
            self.collection_tasks.append(CollectionTask(
                location=location,
                frequency_hours=6,
                last_collected=None,
                is_active=True,
                priority=3
            ))
        
        logger.info(f"Initialized {len(self.collection_tasks)} collection tasks")
    
    async def check_rate_limit(self):
        """Check and enforce rate limiting"""
        current_time = datetime.now()
        
        # Reset counter if a minute has passed
        if (current_time - self.last_request_time).total_seconds() >= 60:
            self.request_count = 0
            self.last_request_time = current_time
        
        # Check if we're at the limit
        if self.request_count >= self.rate_limit_per_minute:
            wait_time = 60 - (current_time - self.last_request_time).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
                self.request_count = 0
                self.last_request_time = datetime.now()
        
        self.request_count += 1
    
    async def collect_traffic_data(self, location: str) -> bool:
        """Collect traffic data for a specific location"""
        try:
            await self.check_rate_limit()
            
            async with TrafficCollector() as collector:
                traffic_data = await collector.get_traffic_data(location)
                
                if traffic_data:
                    # Save to database
                    saved_ids = []
                    for data in traffic_data:
                        saved_id = collector.save_traffic_data(data)
                        if saved_id:
                            saved_ids.append(saved_id)
                    
                    logger.info(f"Collected traffic data for {location}: {len(saved_ids)} data points")
                    return True
                else:
                    logger.warning(f"No traffic data collected for {location}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error collecting traffic data for {location}: {e}")
            return False
    
    async def collect_real_estate_data(self, location: str) -> bool:
        """Collect real estate data for a specific location"""
        try:
            await self.check_rate_limit()
            
            async with RealEstateService() as service:
                # Get property listings
                properties = await service.get_simulated_properties(location, max_results=20)
                
                # Get market data
                market_data = await service.get_market_data(location)
                
                # Save to database (simplified)
                logger.info(f"Collected real estate data for {location}: {len(properties)} properties")
                return True
                
        except Exception as e:
            logger.error(f"Error collecting real estate data for {location}: {e}")
            return False
    
    async def run_collection_cycle(self):
        """Run one collection cycle for all active tasks"""
        current_time = datetime.now()
        tasks_to_run = []
        
        # Check which tasks need to be run
        for task in self.collection_tasks:
            if not task.is_active:
                continue
            
            if (task.last_collected is None or 
                (current_time - task.last_collected).total_seconds() >= task.frequency_hours * 3600):
                tasks_to_run.append(task)
        
        if not tasks_to_run:
            logger.debug("No tasks to run in this cycle")
            return
        
        logger.info(f"Running collection cycle for {len(tasks_to_run)} locations")
        
        # Run tasks concurrently with rate limiting
        for task in tasks_to_run:
            try:
                # Collect traffic data
                traffic_success = await self.collect_traffic_data(task.location)
                
                # Collect real estate data (less frequently)
                real_estate_success = False
                if task.priority == 1:  # Only for high priority locations
                    real_estate_success = await self.collect_real_estate_data(task.location)
                
                if traffic_success or real_estate_success:
                    task.last_collected = current_time
                    logger.info(f"Successfully collected data for {task.location}")
                else:
                    logger.warning(f"Failed to collect data for {task.location}")
                
                # Small delay between requests to be respectful
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in collection cycle for {task.location}: {e}")
    
    async def start_continuous_collection(self):
        """Start continuous data collection"""
        self.is_running = True
        logger.info("Starting continuous data collection...")
        
        # Initialize tasks
        self.initialize_collection_tasks()
        
        # Run initial collection
        await self.run_collection_cycle()
        
        # Set up periodic collection
        while self.is_running:
            try:
                # Wait for next cycle (every 30 minutes)
                await asyncio.sleep(30 * 60)
                
                if self.is_running:
                    await self.run_collection_cycle()
                    
            except Exception as e:
                logger.error(f"Error in continuous collection: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    def stop_collection(self):
        """Stop continuous data collection"""
        self.is_running = False
        logger.info("Stopping data collection...")
    
    async def collect_historical_data(self, days: int = 365, locations: List[str] = None):
        """Collect historical data for specified period"""
        if locations is None:
            locations = self.atlanta_locations
        
        logger.info(f"Starting historical data collection for {len(locations)} locations over {days} days")
        
        # Calculate data points needed
        total_data_points = len(locations) * days * 24  # Hourly data for each location
        logger.info(f"Estimated total data points: {total_data_points}")
        
        # Collect data for each location
        for location in locations:
            logger.info(f"Collecting historical data for {location}")
            
            # Collect data for each day
            for day in range(days):
                target_date = datetime.now() - timedelta(days=day)
                
                # Simulate historical data collection
                await self.collect_traffic_data(location)
                
                # Progress update
                if day % 30 == 0:
                    logger.info(f"Progress: {day}/{days} days completed for {location}")
                
                # Rate limiting
                await asyncio.sleep(1)
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about data collection"""
        try:
            db = SessionLocal()
            
            # Get total data points
            total_traffic_data = db.query(TrafficData).count()
            
            # Get data by location
            location_stats = {}
            for location in self.atlanta_locations:
                count = db.query(TrafficData).filter(TrafficData.location == location).count()
                location_stats[location] = count
            
            # Get data by date range
            today = datetime.now()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            recent_week = db.query(TrafficData).filter(TrafficData.timestamp >= week_ago).count()
            recent_month = db.query(TrafficData).filter(TrafficData.timestamp >= month_ago).count()
            
            db.close()
            
            return {
                "total_traffic_data_points": total_traffic_data,
                "data_by_location": location_stats,
                "recent_week_data": recent_week,
                "recent_month_data": recent_month,
                "active_tasks": len([t for t in self.collection_tasks if t.is_active]),
                "collection_running": self.is_running
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def export_data(self, format: str = "json", location: str = None, days: int = 30) -> str:
        """Export collected data"""
        try:
            db = SessionLocal()
            
            # Build query
            query = db.query(TrafficData)
            
            if location:
                query = query.filter(TrafficData.location == location)
            
            if days:
                cutoff_date = datetime.now() - timedelta(days=days)
                query = query.filter(TrafficData.timestamp >= cutoff_date)
            
            data = query.all()
            
            if format == "json":
                export_data = []
                for record in data:
                    export_data.append({
                        "location": record.location,
                        "latitude": record.latitude,
                        "longitude": record.longitude,
                        "timestamp": record.timestamp.isoformat(),
                        "traffic_level": record.traffic_level,
                        "congestion_score": record.congestion_score,
                        "average_speed": record.average_speed,
                        "source": record.source
                    })
                
                filename = f"traffic_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                db.close()
                return filename
            
            elif format == "csv":
                import csv
                filename = f"traffic_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['location', 'latitude', 'longitude', 'timestamp', 'traffic_level', 'congestion_score', 'average_speed', 'source'])
                    
                    for record in data:
                        writer.writerow([
                            record.location,
                            record.latitude,
                            record.longitude,
                            record.timestamp.isoformat(),
                            record.traffic_level,
                            record.congestion_score,
                            record.average_speed,
                            record.source
                        ])
                
                db.close()
                return filename
            
            else:
                db.close()
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return None


# Background task runner
def run_background_collection():
    """Run data collection in background thread"""
    async def run():
        async with HistoricalDataCollector() as collector:
            await collector.start_continuous_collection()
    
    asyncio.run(run())


def start_background_collection():
    """Start background data collection"""
    thread = threading.Thread(target=run_background_collection, daemon=True)
    thread.start()
    return thread 