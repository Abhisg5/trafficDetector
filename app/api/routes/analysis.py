from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json
import numpy as np

from app.core.database import get_db, TrafficData, InvestmentOpportunity
from app.services.investment_analyzer import InvestmentAnalyzer

router = APIRouter()


@router.get("/traffic-patterns/{location}")
async def analyze_traffic_patterns(
    location: str,
    analysis_type: str = Query("comprehensive", description="Type of analysis"),
    days: int = Query(30, ge=7, le=90, description="Analysis period in days"),
    db: Session = Depends(get_db)
):
    """Analyze traffic patterns for a location"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        traffic_data = db.query(TrafficData).filter(
            TrafficData.location == location,
            TrafficData.timestamp >= cutoff_date
        ).order_by(TrafficData.timestamp).all()
        
        if not traffic_data:
            raise HTTPException(status_code=404, detail="No traffic data available for analysis")
        
        # Calculate basic statistics
        congestion_scores = [data.congestion_score for data in traffic_data]
        avg_congestion = np.mean(congestion_scores)
        std_congestion = np.std(congestion_scores)
        
        # Hourly analysis
        hourly_data = {}
        for hour in range(24):
            hour_data = [data for data in traffic_data if data.timestamp.hour == hour]
            if hour_data:
                hourly_data[hour] = {
                    "average_congestion": np.mean([d.congestion_score for d in hour_data]),
                    "std_congestion": np.std([d.congestion_score for d in hour_data]),
                    "data_points": len(hour_data),
                    "peak_hours": len([d for d in hour_data if d.congestion_score > 0.7])
                }
        
        # Daily analysis
        daily_data = {}
        for day in range(7):
            day_data = [data for data in traffic_data if data.timestamp.weekday() == day]
            if day_data:
                daily_data[day] = {
                    "average_congestion": np.mean([d.congestion_score for d in day_data]),
                    "data_points": len(day_data),
                    "peak_periods": len([d for d in day_data if d.congestion_score > 0.7])
                }
        
        # Traffic level distribution
        traffic_levels = {}
        for data in traffic_data:
            level = data.traffic_level
            if level not in traffic_levels:
                traffic_levels[level] = 0
            traffic_levels[level] += 1
        
        # Peak hour identification
        peak_hours = []
        for hour, data in hourly_data.items():
            if data["average_congestion"] > avg_congestion + std_congestion:
                peak_hours.append({
                    "hour": hour,
                    "average_congestion": data["average_congestion"],
                    "frequency": data["peak_hours"]
                })
        
        # Sort peak hours by congestion
        peak_hours.sort(key=lambda x: x["average_congestion"], reverse=True)
        
        return {
            "location": location,
            "analysis_period_days": days,
            "total_data_points": len(traffic_data),
            "statistics": {
                "average_congestion": round(avg_congestion, 3),
                "std_congestion": round(std_congestion, 3),
                "min_congestion": round(min(congestion_scores), 3),
                "max_congestion": round(max(congestion_scores), 3)
            },
            "traffic_level_distribution": traffic_levels,
            "hourly_analysis": hourly_data,
            "daily_analysis": daily_data,
            "peak_hours": peak_hours[:5],  # Top 5 peak hours
            "patterns": {
                "has_consistent_patterns": std_congestion < 0.2,
                "peak_hour_count": len(peak_hours),
                "weekend_vs_weekday": {
                    "weekend_avg": np.mean([daily_data.get(d, {}).get("average_congestion", 0) for d in [5, 6]]),
                    "weekday_avg": np.mean([daily_data.get(d, {}).get("average_congestion", 0) for d in range(5)])
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing traffic patterns: {str(e)}")


@router.get("/correlation-analysis")
async def correlation_analysis(
    region: str = Query(..., description="Region for correlation analysis"),
    db: Session = Depends(get_db)
):
    """Analyze correlations between traffic and investment metrics"""
    try:
        analyzer = InvestmentAnalyzer()
        
        # Get opportunities in the region
        opportunities = analyzer.find_investment_opportunities(region, min_score=0.3, max_results=50)
        
        if len(opportunities) < 5:
            raise HTTPException(status_code=404, detail="Insufficient data for correlation analysis")
        
        # Extract metrics
        traffic_scores = [opp.traffic_score for opp in opportunities]
        demographic_scores = [opp.demographic_score for opp in opportunities]
        economic_scores = [opp.economic_score for opp in opportunities]
        risk_scores = [opp.risk_score for opp in opportunities]
        rois = [opp.predicted_roi for opp in opportunities]
        overall_scores = [opp.overall_score for opp in opportunities]
        
        # Calculate correlations
        correlations = {
            "traffic_vs_roi": np.corrcoef(traffic_scores, rois)[0, 1],
            "traffic_vs_overall": np.corrcoef(traffic_scores, overall_scores)[0, 1],
            "demographic_vs_roi": np.corrcoef(demographic_scores, rois)[0, 1],
            "economic_vs_roi": np.corrcoef(economic_scores, rois)[0, 1],
            "risk_vs_roi": np.corrcoef(risk_scores, rois)[0, 1],
            "overall_vs_roi": np.corrcoef(overall_scores, rois)[0, 1]
        }
        
        # Handle NaN values
        correlations = {k: round(v, 3) if not np.isnan(v) else 0.0 for k, v in correlations.items()}
        
        # Identify strongest correlations
        strong_correlations = [
            {"metric": k, "correlation": v}
            for k, v in correlations.items()
            if abs(v) > 0.5
        ]
        
        strong_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        return {
            "region": region,
            "data_points": len(opportunities),
            "correlations": correlations,
            "strong_correlations": strong_correlations,
            "insights": {
                "traffic_impact": "High" if abs(correlations["traffic_vs_roi"]) > 0.5 else "Medium" if abs(correlations["traffic_vs_roi"]) > 0.3 else "Low",
                "demographic_impact": "High" if abs(correlations["demographic_vs_roi"]) > 0.5 else "Medium" if abs(correlations["demographic_vs_roi"]) > 0.3 else "Low",
                "economic_impact": "High" if abs(correlations["economic_vs_roi"]) > 0.5 else "Medium" if abs(correlations["economic_vs_roi"]) > 0.3 else "Low"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing correlation analysis: {str(e)}")


@router.get("/predictive-analysis")
async def predictive_analysis(
    location: str,
    prediction_horizon: int = Query(12, ge=1, le=60, description="Prediction horizon in months"),
    db: Session = Depends(get_db)
):
    """Perform predictive analysis for investment potential"""
    try:
        analyzer = InvestmentAnalyzer()
        
        # Get historical data
        historical_data = analyzer.traffic_collector.get_historical_traffic_data(location, days=90)
        
        if len(historical_data) < 10:
            raise HTTPException(status_code=404, detail="Insufficient historical data for prediction")
        
        # Calculate current metrics
        traffic_score = analyzer.calculate_traffic_score(location)
        demographic_score = analyzer.calculate_demographic_score(location)
        economic_score = analyzer.calculate_economic_score(location)
        risk_score = analyzer.calculate_risk_score(location)
        
        # Simple trend analysis
        recent_data = historical_data[:30]  # Last 30 days
        older_data = historical_data[-30:]  # Previous 30 days
        
        if len(recent_data) > 0 and len(older_data) > 0:
            recent_avg = np.mean([d.congestion_score for d in recent_data])
            older_avg = np.mean([d.congestion_score for d in older_data])
            trend = recent_avg - older_avg
        else:
            trend = 0
        
        # Predict future traffic score
        traffic_trend_factor = 1 + (trend * 0.1)  # Adjust based on trend
        predicted_traffic_score = min(1.0, traffic_score * traffic_trend_factor)
        
        # Predict future ROI
        current_metrics = analyzer.InvestmentMetrics(
            location=location,
            latitude=0, longitude=0,  # Not needed for ROI calculation
            traffic_score=predicted_traffic_score,
            demographic_score=demographic_score,
            economic_score=economic_score,
            risk_score=risk_score,
            overall_score=0, predicted_roi=0, confidence=0, factors={}
        )
        
        predicted_roi = analyzer.predict_roi(current_metrics)
        
        # Confidence calculation
        data_confidence = min(1.0, len(historical_data) / 100)  # More data = higher confidence
        trend_confidence = 0.8 if abs(trend) > 0.1 else 0.6  # Strong trend = higher confidence
        overall_confidence = (data_confidence + trend_confidence) / 2
        
        return {
            "location": location,
            "prediction_horizon_months": prediction_horizon,
            "current_metrics": {
                "traffic_score": traffic_score,
                "demographic_score": demographic_score,
                "economic_score": economic_score,
                "risk_score": risk_score
            },
            "predicted_metrics": {
                "traffic_score": round(predicted_traffic_score, 3),
                "predicted_roi": round(predicted_roi, 3)
            },
            "trend_analysis": {
                "traffic_trend": round(trend, 3),
                "trend_direction": "increasing" if trend > 0.05 else "decreasing" if trend < -0.05 else "stable"
            },
            "confidence": round(overall_confidence, 3),
            "data_quality": {
                "historical_data_points": len(historical_data),
                "data_confidence": round(data_confidence, 3),
                "trend_confidence": round(trend_confidence, 3)
            },
            "recommendations": {
                "investment_timing": "immediate" if predicted_roi > 0.1 else "wait" if predicted_roi < 0.05 else "monitor",
                "risk_level": "low" if risk_score < 0.3 else "medium" if risk_score < 0.6 else "high",
                "focus_areas": ["traffic"] if abs(trend) > 0.1 else ["demographics", "economics"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing predictive analysis: {str(e)}")


@router.get("/comparative-analysis")
async def comparative_analysis(
    locations: str = Query(..., description="Comma-separated list of locations"),
    analysis_type: str = Query("investment", description="Type of comparison"),
    db: Session = Depends(get_db)
):
    """Compare multiple locations for investment analysis"""
    try:
        location_list = [loc.strip() for loc in locations.split(",")]
        
        if len(location_list) < 2:
            raise HTTPException(status_code=400, detail="At least 2 locations required for comparison")
        
        analyzer = InvestmentAnalyzer()
        comparison_data = []
        
        for location in location_list:
            # Calculate metrics for each location
            traffic_score = analyzer.calculate_traffic_score(location)
            demographic_score = analyzer.calculate_demographic_score(location)
            economic_score = analyzer.calculate_economic_score(location)
            risk_score = analyzer.calculate_risk_score(location)
            
            overall_score = (
                traffic_score * 0.4 +
                demographic_score * 0.25 +
                economic_score * 0.25 +
                (1 - risk_score) * 0.1
            )
            
            # Get coordinates
            lat, lng = analyzer.traffic_collector._get_coordinates(location)
            
            # Create metrics object for ROI prediction
            metrics = analyzer.InvestmentMetrics(
                location=location,
                latitude=lat,
                longitude=lng,
                traffic_score=traffic_score,
                demographic_score=demographic_score,
                economic_score=economic_score,
                risk_score=risk_score,
                overall_score=overall_score,
                predicted_roi=0.0,
                confidence=0.8,
                factors={}
            )
            
            predicted_roi = analyzer.predict_roi(metrics)
            
            comparison_data.append({
                "location": location,
                "coordinates": {"lat": lat, "lng": lng},
                "scores": {
                    "overall": round(overall_score, 3),
                    "traffic": round(traffic_score, 3),
                    "demographic": round(demographic_score, 3),
                    "economic": round(economic_score, 3),
                    "risk": round(risk_score, 3)
                },
                "predicted_roi": round(predicted_roi, 3),
                "recommended_property_types": analyzer._get_recommended_property_types(metrics),
                "key_factors": analyzer._get_key_factors(metrics)
            })
        
        # Sort by overall score
        comparison_data.sort(key=lambda x: x["scores"]["overall"], reverse=True)
        
        # Calculate rankings
        for i, data in enumerate(comparison_data):
            data["rank"] = i + 1
        
        # Find best and worst performers
        best_location = comparison_data[0]
        worst_location = comparison_data[-1]
        
        # Calculate averages
        avg_scores = {
            "overall": np.mean([d["scores"]["overall"] for d in comparison_data]),
            "traffic": np.mean([d["scores"]["traffic"] for d in comparison_data]),
            "demographic": np.mean([d["scores"]["demographic"] for d in comparison_data]),
            "economic": np.mean([d["scores"]["economic"] for d in comparison_data]),
            "risk": np.mean([d["scores"]["risk"] for d in comparison_data])
        }
        
        avg_roi = np.mean([d["predicted_roi"] for d in comparison_data])
        
        return {
            "locations": location_list,
            "analysis_type": analysis_type,
            "comparison_data": comparison_data,
            "rankings": {
                "best_performer": best_location,
                "worst_performer": worst_location,
                "average_scores": {k: round(v, 3) for k, v in avg_scores.items()},
                "average_roi": round(avg_roi, 3)
            },
            "insights": {
                "recommended_location": best_location["location"],
                "avoid_location": worst_location["location"],
                "score_variance": round(np.var([d["scores"]["overall"] for d in comparison_data]), 3),
                "roi_variance": round(np.var([d["predicted_roi"] for d in comparison_data]), 3)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing comparative analysis: {str(e)}")


@router.get("/market-segmentation")
async def market_segmentation(
    region: str = Query(..., description="Region for market segmentation"),
    segmentation_criteria: str = Query("score", description="Segmentation criteria"),
    db: Session = Depends(get_db)
):
    """Perform market segmentation analysis"""
    try:
        analyzer = InvestmentAnalyzer()
        
        # Get opportunities in the region
        opportunities = analyzer.find_investment_opportunities(region, min_score=0.3, max_results=100)
        
        if len(opportunities) < 10:
            raise HTTPException(status_code=404, detail="Insufficient data for market segmentation")
        
        # Define segments based on criteria
        if segmentation_criteria == "score":
            segments = {
                "premium": [opp for opp in opportunities if opp.overall_score >= 0.8],
                "high_value": [opp for opp in opportunities if 0.6 <= opp.overall_score < 0.8],
                "moderate": [opp for opp in opportunities if 0.4 <= opp.overall_score < 0.6],
                "developing": [opp for opp in opportunities if opp.overall_score < 0.4]
            }
        elif segmentation_criteria == "roi":
            segments = {
                "high_roi": [opp for opp in opportunities if opp.predicted_roi >= 0.1],
                "medium_roi": [opp for opp in opportunities if 0.05 <= opp.predicted_roi < 0.1],
                "low_roi": [opp for opp in opportunities if opp.predicted_roi < 0.05]
            }
        elif segmentation_criteria == "risk":
            segments = {
                "low_risk": [opp for opp in opportunities if opp.risk_score < 0.3],
                "medium_risk": [opp for opp in opportunities if 0.3 <= opp.risk_score < 0.6],
                "high_risk": [opp for opp in opportunities if opp.risk_score >= 0.6]
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid segmentation criteria")
        
        # Analyze each segment
        segment_analysis = {}
        for segment_name, segment_opps in segments.items():
            if len(segment_opps) > 0:
                avg_scores = {
                    "overall": np.mean([opp.overall_score for opp in segment_opps]),
                    "traffic": np.mean([opp.traffic_score for opp in segment_opps]),
                    "demographic": np.mean([opp.demographic_score for opp in segment_opps]),
                    "economic": np.mean([opp.economic_score for opp in segment_opps]),
                    "risk": np.mean([opp.risk_score for opp in segment_opps])
                }
                
                avg_roi = np.mean([opp.predicted_roi for opp in segment_opps])
                
                segment_analysis[segment_name] = {
                    "count": len(segment_opps),
                    "percentage": round(len(segment_opps) / len(opportunities) * 100, 1),
                    "average_scores": {k: round(v, 3) for k, v in avg_scores.items()},
                    "average_roi": round(avg_roi, 3),
                    "top_locations": [
                        {
                            "location": opp.location,
                            "score": opp.overall_score,
                            "roi": opp.predicted_roi
                        }
                        for opp in sorted(segment_opps, key=lambda x: x.overall_score, reverse=True)[:3]
                    ]
                }
        
        return {
            "region": region,
            "segmentation_criteria": segmentation_criteria,
            "total_opportunities": len(opportunities),
            "segments": segment_analysis,
            "market_insights": {
                "largest_segment": max(segment_analysis.items(), key=lambda x: x[1]["count"])[0],
                "highest_roi_segment": max(segment_analysis.items(), key=lambda x: x[1]["average_roi"])[0],
                "lowest_risk_segment": min(segment_analysis.items(), key=lambda x: x[1]["average_scores"]["risk"])[0]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing market segmentation: {str(e)}") 