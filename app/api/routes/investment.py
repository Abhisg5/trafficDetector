from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from app.core.database import get_db, InvestmentOpportunity
from app.services.investment_analyzer import InvestmentAnalyzer

router = APIRouter()


@router.get("/opportunities")
async def find_investment_opportunities(
    region: str = Query(..., description="Region to search for opportunities"),
    min_score: float = Query(0.6, ge=0, le=1, description="Minimum investment score"),
    max_results: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    db: Session = Depends(get_db)
):
    """Find investment opportunities in a region"""
    try:
        analyzer = InvestmentAnalyzer()
        opportunities = analyzer.find_investment_opportunities(
            region=region,
            min_score=min_score,
            max_results=max_results
        )
        
        if not opportunities:
            raise HTTPException(status_code=404, detail="No investment opportunities found")
        
        # Filter by property type if specified
        if property_type:
            filtered_opportunities = []
            for opp in opportunities:
                recommended_types = analyzer._get_recommended_property_types(opp)
                if property_type.lower() in [t.lower() for t in recommended_types]:
                    filtered_opportunities.append(opp)
            opportunities = filtered_opportunities
        
        return {
            "region": region,
            "total_opportunities": len(opportunities),
            "min_score": min_score,
            "opportunities": [
                {
                    "location": opp.location,
                    "coordinates": {"lat": opp.latitude, "lng": opp.longitude},
                    "overall_score": opp.overall_score,
                    "traffic_score": opp.traffic_score,
                    "demographic_score": opp.demographic_score,
                    "economic_score": opp.economic_score,
                    "risk_score": opp.risk_score,
                    "predicted_roi": opp.predicted_roi,
                    "confidence": opp.confidence,
                    "recommended_property_types": analyzer._get_recommended_property_types(opp),
                    "key_factors": analyzer._get_key_factors(opp)
                }
                for opp in opportunities
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding opportunities: {str(e)}")


@router.get("/recommendations")
async def get_investment_recommendations(
    region: str = Query(..., description="Region for recommendations"),
    budget_range: str = Query("medium", description="Budget range (low, medium, high)"),
    db: Session = Depends(get_db)
):
    """Get detailed investment recommendations"""
    try:
        analyzer = InvestmentAnalyzer()
        recommendations = analyzer.get_investment_recommendations(
            region=region,
            budget_range=budget_range
        )
        
        if not recommendations:
            raise HTTPException(status_code=404, detail="No recommendations available")
        
        return {
            "region": region,
            "budget_range": budget_range,
            "total_recommendations": len(recommendations),
            "recommendations": recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")


@router.get("/analysis/{location}")
async def analyze_investment_potential(
    location: str,
    analysis_depth: str = Query("comprehensive", description="Analysis depth"),
    db: Session = Depends(get_db)
):
    """Analyze investment potential for a specific location"""
    try:
        analyzer = InvestmentAnalyzer()
        
        # Calculate all metrics
        traffic_score = analyzer.calculate_traffic_score(location)
        demographic_score = analyzer.calculate_demographic_score(location)
        economic_score = analyzer.calculate_economic_score(location)
        risk_score = analyzer.calculate_risk_score(location)
        
        # Calculate overall score
        overall_score = (
            traffic_score * 0.4 +
            demographic_score * 0.25 +
            economic_score * 0.25 +
            (1 - risk_score) * 0.1
        )
        
        # Get coordinates
        lat, lng = analyzer.traffic_collector._get_coordinates(location)
        
        # Create metrics object for ROI prediction
        from app.services.investment_analyzer import InvestmentMetrics
        metrics = InvestmentMetrics(
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
        
        # Predict ROI
        predicted_roi = analyzer.predict_roi(metrics)
        
        # Get historical traffic data for additional insights
        historical_data = analyzer.traffic_collector.get_historical_traffic_data(location, days=30)
        
        analysis_result = {
            "location": location,
            "coordinates": {"lat": lat, "lng": lng},
            "overall_score": overall_score,
            "predicted_roi": predicted_roi,
            "risk_level": "Low" if risk_score < 0.3 else "Medium" if risk_score < 0.6 else "High",
            "scores": {
                "traffic": traffic_score,
                "demographic": demographic_score,
                "economic": economic_score,
                "risk": risk_score
            },
            "recommended_property_types": analyzer._get_recommended_property_types(metrics),
            "key_factors": analyzer._get_key_factors(metrics),
            "traffic_insights": {
                "data_points": len(historical_data),
                "average_congestion": sum([d.congestion_score for d in historical_data]) / len(historical_data) if historical_data else 0,
                "traffic_consistency": analyzer._calculate_consistency_score(historical_data)
            },
            "investment_timeline": "6-12 months",
            "confidence": 0.8
        }
        
        return analysis_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing investment potential: {str(e)}")


@router.post("/save-opportunity")
async def save_investment_opportunity(
    location: str,
    property_type: str = Query("mixed", description="Property type"),
    notes: Optional[str] = Query(None, description="Additional notes"),
    db: Session = Depends(get_db)
):
    """Save an investment opportunity to the database"""
    try:
        analyzer = InvestmentAnalyzer()
        
        # Calculate metrics
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
        
        # Create metrics object
        from app.services.investment_analyzer import InvestmentMetrics
        metrics = InvestmentMetrics(
            location=location,
            latitude=lat,
            longitude=lng,
            traffic_score=traffic_score,
            demographic_score=demographic_score,
            economic_score=economic_score,
            risk_score=risk_score,
            overall_score=overall_score,
            predicted_roi=analyzer.predict_roi(InvestmentMetrics(
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
            )),
            confidence=0.8,
            factors={}
        )
        
        # Save to database
        opportunity_id = analyzer.save_investment_opportunity(metrics, property_type)
        
        if not opportunity_id:
            raise HTTPException(status_code=500, detail="Failed to save opportunity")
        
        return {
            "message": "Investment opportunity saved successfully",
            "opportunity_id": opportunity_id,
            "location": location,
            "overall_score": overall_score,
            "predicted_roi": metrics.predicted_roi
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving opportunity: {str(e)}")


@router.get("/saved-opportunities")
async def get_saved_opportunities(
    active_only: bool = Query(True, description="Show only active opportunities"),
    db: Session = Depends(get_db)
):
    """Get saved investment opportunities"""
    try:
        query = db.query(InvestmentOpportunity)
        
        if active_only:
            query = query.filter(InvestmentOpportunity.is_active == True)
        
        opportunities = query.order_by(InvestmentOpportunity.investment_score.desc()).all()
        
        return {
            "total_opportunities": len(opportunities),
            "opportunities": [
                {
                    "id": opp.id,
                    "location": opp.location,
                    "coordinates": {"lat": opp.latitude, "lng": opp.longitude},
                    "investment_score": opp.investment_score,
                    "traffic_score": opp.traffic_score,
                    "demographic_score": opp.demographic_score,
                    "economic_score": opp.economic_score,
                    "risk_score": opp.risk_score,
                    "predicted_roi": opp.predicted_roi,
                    "property_type": opp.property_type,
                    "price_range": opp.price_range,
                    "created_at": opp.created_at.isoformat(),
                    "updated_at": opp.updated_at.isoformat(),
                    "is_active": opp.is_active
                }
                for opp in opportunities
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving saved opportunities: {str(e)}")


@router.put("/opportunity/{opportunity_id}")
async def update_opportunity(
    opportunity_id: int,
    is_active: Optional[bool] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update an investment opportunity"""
    try:
        opportunity = db.query(InvestmentOpportunity).filter(
            InvestmentOpportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        if is_active is not None:
            opportunity.is_active = is_active
        
        if notes:
            # Store notes in a separate field or extend the model
            pass
        
        opportunity.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "message": "Opportunity updated successfully",
            "opportunity_id": opportunity_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating opportunity: {str(e)}")


@router.get("/market-analysis")
async def get_market_analysis(
    region: str = Query(..., description="Region for market analysis"),
    db: Session = Depends(get_db)
):
    """Get comprehensive market analysis for a region"""
    try:
        analyzer = InvestmentAnalyzer()
        
        # Get opportunities in the region
        opportunities = analyzer.find_investment_opportunities(region, min_score=0.3, max_results=50)
        
        if not opportunities:
            raise HTTPException(status_code=404, detail="No data available for market analysis")
        
        # Calculate market statistics
        scores = [opp.overall_score for opp in opportunities]
        rois = [opp.predicted_roi for opp in opportunities]
        
        market_stats = {
            "total_opportunities": len(opportunities),
            "average_score": sum(scores) / len(scores),
            "average_roi": sum(rois) / len(rois),
            "score_distribution": {
                "excellent": len([s for s in scores if s >= 0.8]),
                "good": len([s for s in scores if 0.6 <= s < 0.8]),
                "fair": len([s for s in scores if 0.4 <= s < 0.6]),
                "poor": len([s for s in scores if s < 0.4])
            },
            "roi_distribution": {
                "high": len([r for r in rois if r >= 0.1]),
                "medium": len([r for r in rois if 0.05 <= r < 0.1]),
                "low": len([r for r in rois if r < 0.05])
            }
        }
        
        # Property type recommendations
        property_types = {}
        for opp in opportunities:
            for prop_type in analyzer._get_recommended_property_types(opp):
                if prop_type not in property_types:
                    property_types[prop_type] = 0
                property_types[prop_type] += 1
        
        return {
            "region": region,
            "market_statistics": market_stats,
            "property_type_recommendations": property_types,
            "top_opportunities": [
                {
                    "location": opp.location,
                    "score": opp.overall_score,
                    "roi": opp.predicted_roi,
                    "risk_level": "Low" if opp.risk_score < 0.3 else "Medium" if opp.risk_score < 0.6 else "High"
                }
                for opp in opportunities[:5]
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing market analysis: {str(e)}") 