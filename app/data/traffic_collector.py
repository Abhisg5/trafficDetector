import asyncio
import aiohttp
import json
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass

from app.core.config import settings
from app.core.database import TrafficData, SessionLocal


@dataclass
class TrafficInfo:
    location: str
    latitude: float
    longitude: float
    traffic_level: str
    congestion_score: float
    average_speed: float
    travel_time: float
    distance: float
    source: str
    timestamp: datetime


class TrafficCollector:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        # Create SSL context that doesn't verify certificates (for development)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_coordinates(self, location: str) -> Tuple[float, float]:
        """Get coordinates for a location string"""
        # Atlanta metro area coordinates
        atlanta_coords = {
            "atlanta": (33.7490, -84.3880),
            "sandy springs": (33.9304, -84.3733),
            "roswell": (34.0232, -84.3616),
            "alpharetta": (34.0754, -84.2941),
            "marietta": (33.9525, -84.5499),
            "decatur": (33.7748, -84.2963),
            "johns creek": (34.0289, -84.1986),
            "duluth": (34.0029, -84.1446),
            "smyrna": (33.8834, -84.5144),
            "norcross": (33.9412, -84.2135),
            "peachtree corners": (33.9701, -84.2216),
            "brookhaven": (33.8595, -84.3369),
            "dunwoody": (33.9462, -84.3346),
            "kennesaw": (34.0234, -84.6155),
            "woodstock": (34.1015, -84.5194),
            "lawrenceville": (33.9562, -83.9880),
            "stone mountain": (33.7940, -84.1702),
            "college park": (33.6534, -84.4494),
            "east point": (33.6795, -84.4394),
            "tucker": (33.8545, -84.2171)
        }
        
        location_lower = location.lower()
        for city, coords in atlanta_coords.items():
            if city in location_lower:
                return coords
        
        # Default to Atlanta if no match
        return (33.7490, -84.3880)
    
    async def get_tomtom_traffic_data(self, location: str) -> Optional[TrafficInfo]:
        """Get traffic data from TomTom API"""
        if not settings.tomtom_api_key:
            print("TomTom API key not configured")
            return None
        
        try:
            lat, lng = self._get_coordinates(location)
            print(f"Getting TomTom traffic data for {location} at coordinates ({lat}, {lng})")
            
            # TomTom Traffic Flow API
            url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
            params = {
                'key': settings.tomtom_api_key,
                'point': f"{lat},{lng}",
                'unit': 'KMPH'
            }
            
            async with self.session.get(url, params=params) as response:
                print(f"TomTom API response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"TomTom API response: {data}")
                    
                    if 'flowSegmentData' in data and data['flowSegmentData']:
                        flow_data = data['flowSegmentData']
                        
                        # Extract traffic metrics
                        current_speed = flow_data.get('currentSpeed', 0)
                        free_flow_speed = flow_data.get('freeFlowSpeed', 1)
                        
                        print(f"Current speed: {current_speed}, Free flow speed: {free_flow_speed}")
                        
                        # Calculate congestion score
                        if free_flow_speed > 0:
                            congestion_score = 1 - (current_speed / free_flow_speed)
                        else:
                            congestion_score = 0.5
                        
                        # Determine traffic level
                        if congestion_score > 0.7:
                            traffic_level = "severe"
                        elif congestion_score > 0.5:
                            traffic_level = "high"
                        elif congestion_score > 0.3:
                            traffic_level = "medium"
                        else:
                            traffic_level = "low"
                        
                        return TrafficInfo(
                            location=location,
                            latitude=lat,
                            longitude=lng,
                            traffic_level=traffic_level,
                            congestion_score=congestion_score,
                            average_speed=current_speed,
                            travel_time=0,  # Not provided by TomTom
                            distance=0,     # Not provided by TomTom
                            source="tomtom",
                            timestamp=datetime.utcnow()
                        )
                    else:
                        print("No flow segment data in TomTom response")
                else:
                    print(f"TomTom API returned status {response.status}")
                    if response.status == 403:
                        print("TomTom API key might be invalid or expired")
                    elif response.status == 404:
                        print("No traffic data available for this location")
            
            return None
            
        except Exception as e:
            print(f"Error getting TomTom traffic data: {e}")
            return None
    
    async def get_here_traffic_data(self, location: str) -> Optional[TrafficInfo]:
        """Get traffic data from HERE API"""
        if not settings.here_api_key:
            print("HERE API key not configured")
            return None
        
        try:
            lat, lng = self._get_coordinates(location)
            print(f"Getting HERE traffic data for {location} at coordinates ({lat}, {lng})")
            
            # HERE Traffic Flow API
            url = f"https://traffic.ls.hereapi.com/traffic/6.2/flow.json"
            params = {
                'apiKey': settings.here_api_key,
                'bbox': f"{lat-0.01},{lng-0.01},{lat+0.01},{lng+0.01}",
                'responseattributes': 'sh,fc'
            }
            
            async with self.session.get(url, params=params) as response:
                print(f"HERE API response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"HERE API response: {data}")
                    
                    if 'RWS' in data and data['RWS']:
                        rws = data['RWS'][0]
                        if 'RW' in rws and rws['RW']:
                            rw = rws['RW'][0]
                            if 'FIS' in rw and rw['FIS']:
                                fis = rw['FIS'][0]
                                if 'FI' in fis and fis['FI']:
                                    fi = fis['FI'][0]
                                    
                                    # Extract traffic metrics
                                    current_speed = fi.get('CF', [{}])[0].get('SP', 0)
                                    free_flow_speed = fi.get('CF', [{}])[0].get('FF', 1)
                                    
                                    print(f"Current speed: {current_speed}, Free flow speed: {free_flow_speed}")
                                    
                                    # Calculate congestion score
                                    if free_flow_speed > 0:
                                        congestion_score = 1 - (current_speed / free_flow_speed)
                                    else:
                                        congestion_score = 0.5
                                    
                                    # Determine traffic level
                                    if congestion_score > 0.7:
                                        traffic_level = "severe"
                                    elif congestion_score > 0.5:
                                        traffic_level = "high"
                                    elif congestion_score > 0.3:
                                        traffic_level = "medium"
                                    else:
                                        traffic_level = "low"
                                    
                                    return TrafficInfo(
                                        location=location,
                                        latitude=lat,
                                        longitude=lng,
                                        traffic_level=traffic_level,
                                        congestion_score=congestion_score,
                                        average_speed=current_speed,
                                        travel_time=0,
                                        distance=0,
                                        source="here",
                                        timestamp=datetime.utcnow()
                                    )
                    else:
                        print("No traffic flow data in HERE response")
                else:
                    print(f"HERE API returned status {response.status}")
                    if response.status == 403:
                        print("HERE API key might be invalid or expired")
                    elif response.status == 404:
                        print("No traffic data available for this location")
            
            return None
            
        except Exception as e:
            print(f"Error getting HERE traffic data: {e}")
            return None
    
    async def get_traffic_data(self, location: str, sources: List[str] = None) -> List[TrafficInfo]:
        """Get traffic data from multiple sources"""
        if sources is None:
            sources = ["tomtom", "here"]
        
        tasks = []
        
        if "tomtom" in sources:
            tasks.append(self.get_tomtom_traffic_data(location))
        
        if "here" in sources:
            tasks.append(self.get_here_traffic_data(location))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        traffic_data = []
        for result in results:
            if isinstance(result, TrafficInfo):
                traffic_data.append(result)
            elif isinstance(result, Exception):
                print(f"Error collecting traffic data: {result}")
        
        return traffic_data
    
    def save_traffic_data(self, traffic_info: TrafficInfo):
        """Save traffic data to database"""
        try:
            db = SessionLocal()
            traffic_data = TrafficData(
                location=traffic_info.location,
                latitude=traffic_info.latitude,
                longitude=traffic_info.longitude,
                timestamp=traffic_info.timestamp,
                traffic_level=traffic_info.traffic_level,
                congestion_score=traffic_info.congestion_score,
                average_speed=traffic_info.average_speed,
                travel_time=traffic_info.travel_time,
                distance=traffic_info.distance,
                source=traffic_info.source,
                raw_data=json.dumps({
                    "traffic_level": traffic_info.traffic_level,
                    "congestion_score": traffic_info.congestion_score,
                    "average_speed": traffic_info.average_speed,
                    "travel_time": traffic_info.travel_time,
                    "distance": traffic_info.distance
                })
            )
            
            db.add(traffic_data)
            db.commit()
            db.refresh(traffic_data)
            db.close()
            
            return traffic_data.id
            
        except Exception as e:
            print(f"Error saving traffic data: {e}")
            return None
    
    async def collect_and_save_traffic_data(self, location: str) -> List[int]:
        """Collect traffic data and save to database"""
        traffic_data = await self.get_traffic_data(location)
        saved_ids = []
        
        for data in traffic_data:
            saved_id = self.save_traffic_data(data)
            if saved_id:
                saved_ids.append(saved_id)
        
        return saved_ids
    
    def get_historical_traffic_data(self, location: str, days: int = 7) -> List[TrafficData]:
        """Get historical traffic data from database"""
        try:
            db = SessionLocal()
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            traffic_data = db.query(TrafficData).filter(
                TrafficData.location == location,
                TrafficData.timestamp >= cutoff_date
            ).order_by(TrafficData.timestamp.desc()).all()
            
            db.close()
            return traffic_data
            
        except Exception as e:
            print(f"Error getting historical traffic data: {e}")
            return [] 