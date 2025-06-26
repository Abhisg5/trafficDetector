import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import math

from app.core.database import (
    TrafficData, InvestmentOpportunity, TrafficHotspot, 
    AnalysisResult, SessionLocal
)
from app.data.traffic_collector import TrafficCollector


@dataclass
class InvestmentMetrics:
    location: str
    latitude: float
    longitude: float
    traffic_score: float
    demographic_score: float
    economic_score: float
    risk_score: float
    overall_score: float
    predicted_roi: float
    confidence: float
    factors: Dict[str, float]


class InvestmentAnalyzer:
    def __init__(self):
        self.traffic_collector = TrafficCollector()
        self.scaler = StandardScaler()
        self.ml_model = None
        
    def calculate_traffic_score(self, location: str, days: int = 30) -> float:
        """Calculate traffic-based investment score"""
        try:
            db = SessionLocal()
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get historical traffic data
            traffic_data = db.query(TrafficData).filter(
                TrafficData.location == location,
                TrafficData.timestamp >= cutoff_date
            ).all()
            
            if not traffic_data:
                return 0.5  # Neutral score if no data
            
            # Calculate traffic metrics
            congestion_scores = [data.congestion_score for data in traffic_data]
            avg_congestion = np.mean(congestion_scores)
            
            # Traffic patterns analysis
            peak_hours = self._analyze_peak_hours(traffic_data)
            consistency_score = self._calculate_consistency_score(traffic_data)
            
            # Traffic score calculation (higher congestion = better for commercial)
            # For commercial properties, high traffic is good
            # For residential, moderate traffic is preferred
            if avg_congestion > 0.7:
                traffic_score = 0.9  # High traffic - great for commercial
            elif avg_congestion > 0.5:
                traffic_score = 0.7  # Moderate traffic - good for mixed use
            elif avg_congestion > 0.3:
                traffic_score = 0.6  # Low-moderate traffic - good for residential
            else:
                traffic_score = 0.4  # Low traffic - limited potential
            
            # Adjust based on consistency
            traffic_score *= consistency_score
            
            db.close()
            return min(traffic_score, 1.0)
            
        except Exception as e:
            print(f"Error calculating traffic score: {e}")
            return 0.5
    
    def _analyze_peak_hours(self, traffic_data: List[TrafficData]) -> Dict[str, float]:
        """Analyze peak traffic hours"""
        hourly_congestion = {}
        
        for data in traffic_data:
            hour = data.timestamp.hour
            if hour not in hourly_congestion:
                hourly_congestion[hour] = []
            hourly_congestion[hour].append(data.congestion_score)
        
        # Calculate average congestion by hour
        peak_hours = {}
        for hour, scores in hourly_congestion.items():
            peak_hours[hour] = np.mean(scores)
        
        return peak_hours
    
    def _calculate_consistency_score(self, traffic_data: List[TrafficData]) -> float:
        """Calculate how consistent the traffic patterns are"""
        if len(traffic_data) < 2:
            return 0.5
        
        # Group by day of week
        daily_congestion = {}
        for data in traffic_data:
            day = data.timestamp.weekday()
            if day not in daily_congestion:
                daily_congestion[day] = []
            daily_congestion[day].append(data.congestion_score)
        
        # Calculate standard deviation of daily averages
        daily_averages = [np.mean(scores) for scores in daily_congestion.values()]
        if len(daily_averages) > 1:
            std_dev = np.std(daily_averages)
            # Lower std dev = more consistent = higher score
            consistency_score = max(0.1, 1.0 - std_dev)
        else:
            consistency_score = 0.5
        
        return consistency_score
    
    def calculate_demographic_score(self, location: str) -> float:
        """Calculate demographic-based investment score"""
        # This would typically integrate with demographic APIs
        # For now, using simplified scoring based on location patterns
        
        location_lower = location.lower()
        
        # Simplified demographic scoring based on city characteristics
        demographic_scores = {
            "san francisco": 0.8,  # High income, tech workers
            "new york": 0.9,       # High income, diverse economy
            "los angeles": 0.7,    # High income, entertainment
            "chicago": 0.6,        # Good income, diverse economy
            "miami": 0.5,          # Moderate income, tourism
            "seattle": 0.8,        # High income, tech workers
            "austin": 0.7,         # Growing tech scene
            "denver": 0.6,         # Growing city, good income
            "atlanta": 0.6,        # Moderate income, growing
            "boston": 0.8,         # High income, education
        }
        
        for city, score in demographic_scores.items():
            if city in location_lower:
                return score
        
        return 0.5  # Default score
    
    def calculate_economic_score(self, location: str) -> float:
        """Calculate economic indicators score"""
        # This would integrate with economic data APIs
        # For now, using simplified scoring
        
        location_lower = location.lower()
        
        # Simplified economic scoring
        economic_scores = {
            "san francisco": 0.9,  # Strong tech economy
            "new york": 0.9,       # Financial center
            "los angeles": 0.8,    # Entertainment, trade
            "chicago": 0.7,        # Manufacturing, finance
            "miami": 0.6,          # Tourism, trade
            "seattle": 0.8,        # Tech, aerospace
            "austin": 0.7,         # Growing tech
            "denver": 0.6,         # Energy, tech
            "atlanta": 0.6,        # Transportation, finance
            "boston": 0.8,         # Education, biotech
        }
        
        for city, score in economic_scores.items():
            if city in location_lower:
                return score
        
        return 0.5
    
    def calculate_risk_score(self, location: str) -> float:
        """Calculate investment risk score (lower is better)"""
        # This would integrate with various risk assessment APIs
        # For now, using simplified scoring
        
        location_lower = location.lower()
        
        # Simplified risk scoring (lower = less risk)
        risk_scores = {
            "san francisco": 0.3,  # Low risk, stable market
            "new york": 0.2,       # Very low risk
            "los angeles": 0.4,    # Moderate risk
            "chicago": 0.5,        # Moderate risk
            "miami": 0.6,          # Higher risk (climate)
            "seattle": 0.3,        # Low risk
            "austin": 0.4,         # Moderate risk
            "denver": 0.4,         # Moderate risk
            "atlanta": 0.5,        # Moderate risk
            "boston": 0.3,         # Low risk
        }
        
        for city, score in risk_scores.items():
            if city in location_lower:
                return score
        
        return 0.5
    
    def predict_roi(self, metrics: InvestmentMetrics) -> float:
        """Predict ROI based on investment metrics"""
        # Simplified ROI prediction model
        # In a real implementation, this would use ML models trained on historical data
        
        base_roi = 0.05  # 5% base ROI
        
        # Adjust based on scores
        traffic_multiplier = 1 + (metrics.traffic_score - 0.5) * 0.4
        demographic_multiplier = 1 + (metrics.demographic_score - 0.5) * 0.3
        economic_multiplier = 1 + (metrics.economic_score - 0.5) * 0.3
        risk_adjustment = 1 - metrics.risk_score * 0.2
        
        predicted_roi = base_roi * traffic_multiplier * demographic_multiplier * economic_multiplier * risk_adjustment
        
        return max(0.02, min(0.15, predicted_roi))  # Between 2% and 15%
    
    def find_investment_opportunities(
        self, 
        region: str, 
        min_score: float = 0.6,
        max_results: int = 10
    ) -> List[InvestmentMetrics]:
        """Find investment opportunities in a region"""
        opportunities = []
        
        # Define search areas within the region
        search_locations = self._get_search_locations(region)
        
        for location in search_locations:
            # Calculate all metrics
            traffic_score = self.calculate_traffic_score(location)
            demographic_score = self.calculate_demographic_score(location)
            economic_score = self.calculate_economic_score(location)
            risk_score = self.calculate_risk_score(location)
            
            # Calculate overall score (weighted average)
            overall_score = (
                traffic_score * 0.4 +
                demographic_score * 0.25 +
                economic_score * 0.25 +
                (1 - risk_score) * 0.1
            )
            
            if overall_score >= min_score:
                # Get coordinates
                lat, lng = self.traffic_collector._get_coordinates(location)
                
                metrics = InvestmentMetrics(
                    location=location,
                    latitude=lat,
                    longitude=lng,
                    traffic_score=traffic_score,
                    demographic_score=demographic_score,
                    economic_score=economic_score,
                    risk_score=risk_score,
                    overall_score=overall_score,
                    predicted_roi=0.0,  # Will be calculated below
                    confidence=0.8,
                    factors={
                        "traffic_consistency": self._calculate_consistency_score(
                            self.traffic_collector.get_historical_traffic_data(location)
                        ),
                        "peak_hours": len(self._analyze_peak_hours(
                            self.traffic_collector.get_historical_traffic_data(location)
                        )),
                        "data_points": len(self.traffic_collector.get_historical_traffic_data(location))
                    }
                )
                
                # Predict ROI
                metrics.predicted_roi = self.predict_roi(metrics)
                opportunities.append(metrics)
        
        # Sort by overall score and limit results
        opportunities.sort(key=lambda x: x.overall_score, reverse=True)
        return opportunities[:max_results]
    
    def _get_search_locations(self, region: str) -> List[str]:
        """Get list of locations to search within a region"""
        region_locations = {
            "atlanta": [
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
        }
        
        region_lower = region.lower()
        for key, locations in region_locations.items():
            if key in region_lower:
                return locations
        
        # Default to Atlanta and its surrounding areas
        return region_locations["atlanta"]
    
    def save_investment_opportunity(self, metrics: InvestmentMetrics, property_type: str = "mixed") -> int:
        """Save investment opportunity to database"""
        try:
            db = SessionLocal()
            
            opportunity = InvestmentOpportunity(
                location=metrics.location,
                latitude=metrics.latitude,
                longitude=metrics.longitude,
                investment_score=metrics.overall_score,
                traffic_score=metrics.traffic_score,
                demographic_score=metrics.demographic_score,
                economic_score=metrics.economic_score,
                risk_score=metrics.risk_score,
                predicted_roi=metrics.predicted_roi,
                property_type=property_type,
                price_range="medium"  # Would be determined by market analysis
            )
            
            db.add(opportunity)
            db.commit()
            db.refresh(opportunity)
            db.close()
            
            return opportunity.id
            
        except Exception as e:
            print(f"Error saving investment opportunity: {e}")
            return None
    
    def get_investment_recommendations(self, region: str, budget_range: str = "medium") -> List[Dict]:
        """Get investment recommendations with detailed analysis"""
        opportunities = self.find_investment_opportunities(region)
        recommendations = []
        
        for opp in opportunities:
            recommendation = {
                "location": opp.location,
                "coordinates": {"lat": opp.latitude, "lng": opp.longitude},
                "overall_score": opp.overall_score,
                "predicted_roi": opp.predicted_roi,
                "risk_level": "Low" if opp.risk_score < 0.3 else "Medium" if opp.risk_score < 0.6 else "High",
                "recommended_property_types": self._get_recommended_property_types(opp),
                "key_factors": self._get_key_factors(opp),
                "investment_timeline": "6-12 months",
                "confidence": opp.confidence
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _get_recommended_property_types(self, metrics: InvestmentMetrics) -> List[str]:
        """Get recommended property types based on metrics"""
        recommendations = []
        
        if metrics.traffic_score > 0.7:
            recommendations.append("Commercial")
            recommendations.append("Mixed-use")
        
        if metrics.demographic_score > 0.7:
            recommendations.append("Residential")
            recommendations.append("Luxury")
        
        if metrics.economic_score > 0.7:
            recommendations.append("Office")
            recommendations.append("Retail")
        
        if not recommendations:
            recommendations = ["Mixed-use", "Residential"]
        
        return recommendations
    
    def _get_key_factors(self, metrics: InvestmentMetrics) -> List[str]:
        """Get key factors that make this location attractive"""
        factors = []
        
        if metrics.traffic_score > 0.7:
            factors.append("High traffic volume")
        elif metrics.traffic_score > 0.5:
            factors.append("Moderate traffic flow")
        
        if metrics.demographic_score > 0.7:
            factors.append("High-income demographic")
        elif metrics.demographic_score > 0.5:
            factors.append("Growing population")
        
        if metrics.economic_score > 0.7:
            factors.append("Strong local economy")
        elif metrics.economic_score > 0.5:
            factors.append("Economic growth potential")
        
        if metrics.risk_score < 0.3:
            factors.append("Low investment risk")
        elif metrics.risk_score < 0.5:
            factors.append("Moderate risk profile")
        
        return factors 