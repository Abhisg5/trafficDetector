from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json

from app.core.database import get_db, TrafficData, InvestmentOpportunity, TrafficHotspot
from app.services.investment_analyzer import InvestmentAnalyzer

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(db: Session = Depends(get_db)):
    """Get dashboard overview with key metrics"""
    try:
        # Get recent traffic data
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        recent_traffic = db.query(TrafficData).filter(
            TrafficData.timestamp >= cutoff_date
        ).count()
        
        # Get investment opportunities
        total_opportunities = db.query(InvestmentOpportunity).filter(
            InvestmentOpportunity.is_active == True
        ).count()
        
        # Get hotspots
        total_hotspots = db.query(TrafficHotspot).count()
        
        # Calculate average scores
        opportunities = db.query(InvestmentOpportunity).filter(
            InvestmentOpportunity.is_active == True
        ).all()
        
        if opportunities:
            avg_score = sum(opp.investment_score for opp in opportunities) / len(opportunities)
            avg_roi = sum(opp.predicted_roi for opp in opportunities) / len(opportunities)
        else:
            avg_score = 0
            avg_roi = 0
        
        return {
            "traffic_data_points": recent_traffic,
            "active_opportunities": total_opportunities,
            "traffic_hotspots": total_hotspots,
            "average_investment_score": round(avg_score, 3),
            "average_predicted_roi": round(avg_roi, 3),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard overview: {str(e)}")


@router.get("/traffic-summary")
async def get_traffic_summary(
    days: int = Query(7, ge=1, le=30, description="Number of days"),
    db: Session = Depends(get_db)
):
    """Get traffic summary for dashboard"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        traffic_data = db.query(TrafficData).filter(
            TrafficData.timestamp >= cutoff_date
        ).all()
        
        if not traffic_data:
            return {
                "total_data_points": 0,
                "average_congestion": 0,
                "traffic_level_distribution": {},
                "top_locations": [],
                "hourly_patterns": {}
            }
        
        # Calculate metrics
        congestion_scores = [data.congestion_score for data in traffic_data]
        avg_congestion = sum(congestion_scores) / len(congestion_scores)
        
        # Traffic level distribution
        traffic_levels = {}
        for data in traffic_data:
            level = data.traffic_level
            if level not in traffic_levels:
                traffic_levels[level] = 0
            traffic_levels[level] += 1
        
        # Top locations by data points
        location_counts = {}
        for data in traffic_data:
            if data.location not in location_counts:
                location_counts[data.location] = 0
            location_counts[data.location] += 1
        
        top_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Hourly patterns
        hourly_patterns = {}
        for hour in range(24):
            hour_data = [data for data in traffic_data if data.timestamp.hour == hour]
            if hour_data:
                avg_congestion_hour = sum(data.congestion_score for data in hour_data) / len(hour_data)
                hourly_patterns[hour] = {
                    "average_congestion": avg_congestion_hour,
                    "data_points": len(hour_data)
                }
        
        return {
            "total_data_points": len(traffic_data),
            "average_congestion": round(avg_congestion, 3),
            "traffic_level_distribution": traffic_levels,
            "top_locations": [
                {"location": loc, "data_points": count}
                for loc, count in top_locations
            ],
            "hourly_patterns": hourly_patterns
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting traffic summary: {str(e)}")


@router.get("/investment-summary")
async def get_investment_summary(db: Session = Depends(get_db)):
    """Get investment summary for dashboard"""
    try:
        opportunities = db.query(InvestmentOpportunity).filter(
            InvestmentOpportunity.is_active == True
        ).all()
        
        if not opportunities:
            return {
                "total_opportunities": 0,
                "average_score": 0,
                "average_roi": 0,
                "score_distribution": {},
                "top_opportunities": [],
                "property_type_distribution": {}
            }
        
        # Calculate metrics
        scores = [opp.investment_score for opp in opportunities]
        rois = [opp.predicted_roi for opp in opportunities]
        
        avg_score = sum(scores) / len(scores)
        avg_roi = sum(rois) / len(rois)
        
        # Score distribution
        score_distribution = {
            "excellent": len([s for s in scores if s >= 0.8]),
            "good": len([s for s in scores if 0.6 <= s < 0.8]),
            "fair": len([s for s in scores if 0.4 <= s < 0.6]),
            "poor": len([s for s in scores if s < 0.4])
        }
        
        # Top opportunities
        top_opportunities = sorted(opportunities, key=lambda x: x.investment_score, reverse=True)[:5]
        
        # Property type distribution
        property_types = {}
        for opp in opportunities:
            prop_type = opp.property_type
            if prop_type not in property_types:
                property_types[prop_type] = 0
            property_types[prop_type] += 1
        
        return {
            "total_opportunities": len(opportunities),
            "average_score": round(avg_score, 3),
            "average_roi": round(avg_roi, 3),
            "score_distribution": score_distribution,
            "top_opportunities": [
                {
                    "location": opp.location,
                    "score": opp.investment_score,
                    "roi": opp.predicted_roi,
                    "property_type": opp.property_type
                }
                for opp in top_opportunities
            ],
            "property_type_distribution": property_types
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting investment summary: {str(e)}")


@router.get("/hotspots-summary")
async def get_hotspots_summary(db: Session = Depends(get_db)):
    """Get traffic hotspots summary for dashboard"""
    try:
        hotspots = db.query(TrafficHotspot).all()
        
        if not hotspots:
            return {
                "total_hotspots": 0,
                "average_score": 0,
                "top_hotspots": [],
                "congestion_distribution": {}
            }
        
        # Calculate metrics
        scores = [hotspot.hotspot_score for hotspot in hotspots]
        avg_score = sum(scores) / len(scores)
        
        # Top hotspots
        top_hotspots = sorted(hotspots, key=lambda x: x.hotspot_score, reverse=True)[:5]
        
        # Congestion distribution
        congestion_distribution = {
            "high": len([h for h in hotspots if h.average_congestion > 0.7]),
            "medium": len([h for h in hotspots if 0.4 <= h.average_congestion <= 0.7]),
            "low": len([h for h in hotspots if h.average_congestion < 0.4])
        }
        
        return {
            "total_hotspots": len(hotspots),
            "average_score": round(avg_score, 3),
            "top_hotspots": [
                {
                    "location": hotspot.location,
                    "score": hotspot.hotspot_score,
                    "average_congestion": hotspot.average_congestion,
                    "frequency": hotspot.frequency
                }
                for hotspot in top_hotspots
            ],
            "congestion_distribution": congestion_distribution
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting hotspots summary: {str(e)}")


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Number of recent activities"),
    db: Session = Depends(get_db)
):
    """Get recent activity for dashboard"""
    try:
        # Get recent traffic data
        recent_traffic = db.query(TrafficData).order_by(
            TrafficData.timestamp.desc()
        ).limit(limit).all()
        
        # Get recent investment opportunities
        recent_opportunities = db.query(InvestmentOpportunity).order_by(
            InvestmentOpportunity.created_at.desc()
        ).limit(limit).all()
        
        activities = []
        
        # Add traffic activities
        for data in recent_traffic:
            activities.append({
                "type": "traffic_data",
                "timestamp": data.timestamp.isoformat(),
                "location": data.location,
                "description": f"Traffic data collected - {data.traffic_level} congestion",
                "details": {
                    "congestion_score": data.congestion_score,
                    "source": data.source
                }
            })
        
        # Add investment activities
        for opp in recent_opportunities:
            activities.append({
                "type": "investment_opportunity",
                "timestamp": opp.created_at.isoformat(),
                "location": opp.location,
                "description": f"Investment opportunity identified - Score: {opp.investment_score:.2f}",
                "details": {
                    "investment_score": opp.investment_score,
                    "predicted_roi": opp.predicted_roi,
                    "property_type": opp.property_type
                }
            })
        
        # Sort by timestamp and limit
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "recent_activities": activities[:limit],
            "total_activities": len(activities)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recent activity: {str(e)}")


@router.get("/geographic-data")
async def get_geographic_data(
    region: Optional[str] = Query(None, description="Filter by region"),
    db: Session = Depends(get_db)
):
    """Get geographic data for mapping"""
    try:
        # Get traffic data points
        traffic_query = db.query(TrafficData)
        if region:
            traffic_query = traffic_query.filter(TrafficData.location.contains(region))
        
        traffic_data = traffic_query.all()
        
        # Get investment opportunities
        opportunities_query = db.query(InvestmentOpportunity).filter(
            InvestmentOpportunity.is_active == True
        )
        if region:
            opportunities_query = opportunities_query.filter(InvestmentOpportunity.location.contains(region))
        
        opportunities = opportunities_query.all()
        
        # Get hotspots
        hotspots_query = db.query(TrafficHotspot)
        if region:
            hotspots_query = hotspots_query.filter(TrafficHotspot.location.contains(region))
        
        hotspots = hotspots_query.all()
        
        return {
            "traffic_points": [
                {
                    "location": data.location,
                    "coordinates": {"lat": data.latitude, "lng": data.longitude},
                    "congestion_score": data.congestion_score,
                    "traffic_level": data.traffic_level,
                    "timestamp": data.timestamp.isoformat()
                }
                for data in traffic_data
            ],
            "investment_opportunities": [
                {
                    "location": opp.location,
                    "coordinates": {"lat": opp.latitude, "lng": opp.longitude},
                    "investment_score": opp.investment_score,
                    "predicted_roi": opp.predicted_roi,
                    "property_type": opp.property_type
                }
                for opp in opportunities
            ],
            "hotspots": [
                {
                    "location": hotspot.location,
                    "coordinates": {"lat": hotspot.latitude, "lng": hotspot.longitude},
                    "hotspot_score": hotspot.hotspot_score,
                    "average_congestion": hotspot.average_congestion
                }
                for hotspot in hotspots
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting geographic data: {str(e)}")


@router.get("/trends")
async def get_trends(
    days: int = Query(30, ge=7, le=90, description="Number of days for trend analysis"),
    db: Session = Depends(get_db)
):
    """Get trend data for dashboard charts"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get traffic data for trend analysis
        traffic_data = db.query(TrafficData).filter(
            TrafficData.timestamp >= cutoff_date
        ).order_by(TrafficData.timestamp).all()
        
        # Group by date
        daily_traffic = {}
        for data in traffic_data:
            date_str = data.timestamp.date().isoformat()
            if date_str not in daily_traffic:
                daily_traffic[date_str] = []
            daily_traffic[date_str].append(data.congestion_score)
        
        # Calculate daily averages
        traffic_trend = [
            {
                "date": date,
                "average_congestion": sum(scores) / len(scores),
                "data_points": len(scores)
            }
            for date, scores in daily_traffic.items()
        ]
        
        # Sort by date
        traffic_trend.sort(key=lambda x: x["date"])
        
        # Get investment opportunities trend
        opportunities = db.query(InvestmentOpportunity).filter(
            InvestmentOpportunity.created_at >= cutoff_date
        ).order_by(InvestmentOpportunity.created_at).all()
        
        # Group by date
        daily_opportunities = {}
        for opp in opportunities:
            date_str = opp.created_at.date().isoformat()
            if date_str not in daily_opportunities:
                daily_opportunities[date_str] = []
            daily_opportunities[date_str].append(opp.investment_score)
        
        # Calculate daily averages
        investment_trend = [
            {
                "date": date,
                "average_score": sum(scores) / len(scores),
                "opportunities_count": len(scores)
            }
            for date, scores in daily_opportunities.items()
        ]
        
        # Sort by date
        investment_trend.sort(key=lambda x: x["date"])
        
        return {
            "traffic_trend": traffic_trend,
            "investment_trend": investment_trend,
            "analysis_period_days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trends: {str(e)}")


@router.get("/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    """Get system alerts and notifications"""
    try:
        alerts = []
        
        # Check for low data collection
        cutoff_date = datetime.utcnow() - timedelta(hours=24)
        recent_traffic = db.query(TrafficData).filter(
            TrafficData.timestamp >= cutoff_date
        ).count()
        
        if recent_traffic < 10:
            alerts.append({
                "type": "warning",
                "title": "Low Traffic Data Collection",
                "message": f"Only {recent_traffic} traffic data points collected in the last 24 hours",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check for high-risk opportunities
        high_risk_opportunities = db.query(InvestmentOpportunity).filter(
            InvestmentOpportunity.risk_score > 0.7,
            InvestmentOpportunity.is_active == True
        ).count()
        
        if high_risk_opportunities > 0:
            alerts.append({
                "type": "info",
                "title": "High-Risk Opportunities",
                "message": f"{high_risk_opportunities} high-risk investment opportunities identified",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check for severe traffic conditions
        severe_traffic = db.query(TrafficData).filter(
            TrafficData.traffic_level == "severe",
            TrafficData.timestamp >= cutoff_date
        ).count()
        
        if severe_traffic > 5:
            alerts.append({
                "type": "alert",
                "title": "Severe Traffic Conditions",
                "message": f"{severe_traffic} severe traffic conditions detected in the last 24 hours",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return {
            "alerts": alerts,
            "total_alerts": len(alerts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}") 