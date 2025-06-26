from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json

from app.core.database import get_db, TrafficData
from app.data.traffic_collector import TrafficCollector
from app.services.investment_analyzer import InvestmentAnalyzer

router = APIRouter()


@router.get("/collect/{location}")
async def collect_traffic_data(
    location: str,
    sources: Optional[str] = Query("tomtom,here", description="Traffic data sources"),
    db: Session = Depends(get_db)
):
    """Collect real-time traffic data for a location"""
    try:
        async with TrafficCollector() as collector:
            source_list = sources.split(",")
            traffic_data = await collector.get_traffic_data(location, source_list)
            
            if not traffic_data:
                raise HTTPException(status_code=404, detail="No real traffic data available for this location. Please check your API keys.")
            
            # Save to database
            saved_ids = []
            for data in traffic_data:
                saved_id = collector.save_traffic_data(data)
                if saved_id:
                    saved_ids.append(saved_id)
            
            return {
                "message": "Real traffic data collected successfully",
                "location": location,
                "sources": source_list,
                "data_points": len(traffic_data),
                "saved_ids": saved_ids,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error collecting traffic data: {str(e)}")


@router.get("/current/{location}")
async def get_current_traffic(
    location: str,
    db: Session = Depends(get_db)
):
    """Get current traffic data for a location"""
    try:
        # Get the most recent traffic data
        traffic_data = db.query(TrafficData).filter(
            TrafficData.location == location
        ).order_by(TrafficData.timestamp.desc()).first()
        
        if not traffic_data:
            raise HTTPException(status_code=404, detail="No traffic data found for location")
        
        return {
            "location": traffic_data.location,
            "coordinates": {
                "latitude": traffic_data.latitude,
                "longitude": traffic_data.longitude
            },
            "traffic_level": traffic_data.traffic_level,
            "congestion_score": traffic_data.congestion_score,
            "average_speed": traffic_data.average_speed,
            "travel_time": traffic_data.travel_time,
            "distance": traffic_data.distance,
            "source": traffic_data.source,
            "timestamp": traffic_data.timestamp.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving traffic data: {str(e)}")


@router.get("/historical/{location}")
async def get_historical_traffic(
    location: str,
    days: int = Query(7, ge=1, le=90, description="Number of days of historical data"),
    db: Session = Depends(get_db)
):
    """Get historical traffic data for a location"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        traffic_data = db.query(TrafficData).filter(
            TrafficData.location == location,
            TrafficData.timestamp >= cutoff_date
        ).order_by(TrafficData.timestamp.desc()).all()
        
        if not traffic_data:
            raise HTTPException(status_code=404, detail="No historical traffic data found")
        
        # Calculate summary statistics
        congestion_scores = [data.congestion_score for data in traffic_data]
        avg_congestion = sum(congestion_scores) / len(congestion_scores)
        
        # Group by traffic level
        traffic_levels = {}
        for data in traffic_data:
            level = data.traffic_level
            if level not in traffic_levels:
                traffic_levels[level] = 0
            traffic_levels[level] += 1
        
        return {
            "location": location,
            "period_days": days,
            "total_data_points": len(traffic_data),
            "average_congestion": avg_congestion,
            "traffic_level_distribution": traffic_levels,
            "data_points": [
                {
                    "timestamp": data.timestamp.isoformat(),
                    "traffic_level": data.traffic_level,
                    "congestion_score": data.congestion_score,
                    "average_speed": data.average_speed,
                    "source": data.source
                }
                for data in traffic_data
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving historical data: {str(e)}")


@router.get("/hotspots/90days")
async def get_traffic_hotspots_90days(
    region: str = Query(..., description="Region to analyze (e.g., Atlanta, Georgia)"),
    min_congestion: float = Query(0.4, ge=0, le=1, description="Minimum congestion score"),
    db: Session = Depends(get_db)
):
    """Get traffic hotspots in a region based on 90 days of data"""
    try:
        # Get traffic data for the last 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        traffic_data = db.query(TrafficData).filter(
            TrafficData.timestamp >= cutoff_date
        ).all()
        
        if not traffic_data:
            raise HTTPException(status_code=404, detail="No traffic data found for the last 90 days")
        
        # Filter by region (case-insensitive)
        region_lower = region.lower()
        region_data = []
        for data in traffic_data:
            if (region_lower in data.location.lower() or 
                any(word in data.location.lower() for word in region_lower.split())):
                region_data.append(data)
        
        if not region_data:
            raise HTTPException(status_code=404, detail=f"No traffic data found for region: {region}")
        
        # Group by location and calculate hotspot scores
        location_stats = {}
        for data in region_data:
            if data.location not in location_stats:
                location_stats[data.location] = {
                    "congestion_scores": [],
                    "coordinates": {"lat": data.latitude, "lng": data.longitude},
                    "data_points": 0,
                    "sources": set(),
                    "traffic_levels": {"low": 0, "medium": 0, "high": 0, "severe": 0}
                }
            
            location_stats[data.location]["congestion_scores"].append(data.congestion_score)
            location_stats[data.location]["data_points"] += 1
            location_stats[data.location]["sources"].add(data.source)
            location_stats[data.location]["traffic_levels"][data.traffic_level] += 1
        
        # Calculate hotspot scores
        hotspots = []
        for location, stats in location_stats.items():
            avg_congestion = sum(stats["congestion_scores"]) / len(stats["congestion_scores"])
            
            if avg_congestion >= min_congestion:
                # Calculate hotspot score based on average congestion and data consistency
                data_consistency = min(stats["data_points"] / 90, 1.0)  # Normalize by days
                hotspot_score = avg_congestion * data_consistency
                
                # Determine dominant traffic level
                dominant_level = max(stats["traffic_levels"], key=stats["traffic_levels"].get)
                
                hotspots.append({
                    "location": location,
                    "coordinates": stats["coordinates"],
                    "hotspot_score": min(hotspot_score, 1.0),
                    "average_congestion": round(avg_congestion, 3),
                    "data_points": stats["data_points"],
                    "data_consistency": round(data_consistency, 3),
                    "dominant_traffic_level": dominant_level,
                    "traffic_level_distribution": stats["traffic_levels"],
                    "data_sources": list(stats["sources"]),
                    "analysis_period": "90 days"
                })
        
        # Sort by hotspot score
        hotspots.sort(key=lambda x: x["hotspot_score"], reverse=True)
        
        # Calculate region summary
        total_data_points = len(region_data)
        avg_region_congestion = sum(data.congestion_score for data in region_data) / len(region_data)
        
        return {
            "region": region,
            "analysis_period_days": 90,
            "total_data_points": total_data_points,
            "average_region_congestion": round(avg_region_congestion, 3),
            "hotspots_found": len(hotspots),
            "hotspots": hotspots[:20],  # Top 20 hotspots
            "summary": {
                "high_congestion_locations": len([h for h in hotspots if h["average_congestion"] > 0.7]),
                "medium_congestion_locations": len([h for h in hotspots if 0.5 <= h["average_congestion"] <= 0.7]),
                "low_congestion_locations": len([h for h in hotspots if h["average_congestion"] < 0.5])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing 90-day hotspots: {str(e)}")


@router.get("/hotspots")
async def get_traffic_hotspots(
    region: str = Query(..., description="Region to analyze"),
    min_congestion: float = Query(0.5, ge=0, le=1, description="Minimum congestion score"),
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get traffic hotspots in a region for specified number of days"""
    try:
        # Get traffic data for the specified period
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        traffic_data = db.query(TrafficData).filter(
            TrafficData.timestamp >= cutoff_date
        ).all()
        
        if not traffic_data:
            raise HTTPException(status_code=404, detail=f"No traffic data found for the last {days} days")
        
        # Filter by region (simplified - in real app would use geospatial queries)
        region_data = [data for data in traffic_data if region.lower() in data.location.lower()]
        
        if not region_data:
            raise HTTPException(status_code=404, detail="No traffic data found for region")
        
        # Group by location and calculate hotspot scores
        location_stats = {}
        for data in region_data:
            if data.location not in location_stats:
                location_stats[data.location] = {
                    "congestion_scores": [],
                    "coordinates": {"lat": data.latitude, "lng": data.longitude},
                    "data_points": 0
                }
            
            location_stats[data.location]["congestion_scores"].append(data.congestion_score)
            location_stats[data.location]["data_points"] += 1
        
        # Calculate hotspot scores
        hotspots = []
        for location, stats in location_stats.items():
            avg_congestion = sum(stats["congestion_scores"]) / len(stats["congestion_scores"])
            
            if avg_congestion >= min_congestion:
                hotspot_score = avg_congestion * (stats["data_points"] / 10)  # Normalize by data points
                
                hotspots.append({
                    "location": location,
                    "coordinates": stats["coordinates"],
                    "hotspot_score": min(hotspot_score, 1.0),
                    "average_congestion": round(avg_congestion, 3),
                    "data_points": stats["data_points"],
                    "traffic_level": "high" if avg_congestion > 0.7 else "medium" if avg_congestion > 0.5 else "low"
                })
        
        # Sort by hotspot score
        hotspots.sort(key=lambda x: x["hotspot_score"], reverse=True)
        
        return {
            "region": region,
            "analysis_period_days": days,
            "hotspots": hotspots[:10],  # Top 10 hotspots
            "total_hotspots": len(hotspots)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing hotspots: {str(e)}")


@router.get("/analysis/{location}")
async def analyze_traffic_patterns(
    location: str,
    analysis_type: str = Query("comprehensive", description="Type of analysis"),
    db: Session = Depends(get_db)
):
    """Analyze traffic patterns for investment insights"""
    try:
        # Get historical data
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        traffic_data = db.query(TrafficData).filter(
            TrafficData.location == location,
            TrafficData.timestamp >= cutoff_date
        ).all()
        
        if not traffic_data:
            raise HTTPException(status_code=404, detail="Insufficient traffic data for analysis")
        
        # Perform analysis
        analyzer = InvestmentAnalyzer()
        
        # Calculate various metrics
        traffic_score = analyzer.calculate_traffic_score(location)
        peak_hours = analyzer._analyze_peak_hours(traffic_data)
        consistency_score = analyzer._calculate_consistency_score(traffic_data)
        
        # Calculate hourly patterns
        hourly_patterns = {}
        for hour in range(24):
            hour_data = [data for data in traffic_data if data.timestamp.hour == hour]
            if hour_data:
                avg_congestion = sum(data.congestion_score for data in hour_data) / len(hour_data)
                hourly_patterns[hour] = {
                    "average_congestion": avg_congestion,
                    "data_points": len(hour_data)
                }
        
        # Calculate weekly patterns
        weekly_patterns = {}
        for day in range(7):
            day_data = [data for data in traffic_data if data.timestamp.weekday() == day]
            if day_data:
                avg_congestion = sum(data.congestion_score for data in day_data) / len(day_data)
                weekly_patterns[day] = {
                    "average_congestion": avg_congestion,
                    "data_points": len(day_data)
                }
        
        return {
            "location": location,
            "analysis_type": analysis_type,
            "traffic_score": traffic_score,
            "consistency_score": consistency_score,
            "peak_hours": peak_hours,
            "hourly_patterns": hourly_patterns,
            "weekly_patterns": weekly_patterns,
            "total_data_points": len(traffic_data),
            "analysis_period_days": 30,
            "investment_insights": {
                "traffic_potential": "high" if traffic_score > 0.7 else "medium" if traffic_score > 0.5 else "low",
                "consistency": "high" if consistency_score > 0.7 else "medium" if consistency_score > 0.5 else "low",
                "peak_hour_count": len([h for h, score in peak_hours.items() if score > 0.6])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing traffic patterns: {str(e)}")


@router.post("/bulk-collect")
async def bulk_collect_traffic_data(
    locations: List[str],
    sources: Optional[str] = Query("tomtom", description="Traffic data sources")
):
    """Collect traffic data for multiple locations"""
    try:
        async with TrafficCollector() as collector:
            source_list = sources.split(",")
            results = []
            
            for location in locations:
                try:
                    traffic_data = await collector.get_traffic_data(location, source_list)
                    
                    saved_ids = []
                    
                    for data in traffic_data:
                        saved_id = collector.save_traffic_data(data)
                        if saved_id:
                            saved_ids.append(saved_id)
                    
                    results.append({
                        "location": location,
                        "status": "success",
                        "data_points": len(traffic_data),
                        "saved_ids": saved_ids
                    })
                    
                except Exception as e:
                    results.append({
                        "location": location,
                        "status": "error",
                        "error": str(e)
                    })
            
            return {
                "message": "Bulk traffic data collection completed",
                "total_locations": len(locations),
                "results": results
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in bulk collection: {str(e)}") 