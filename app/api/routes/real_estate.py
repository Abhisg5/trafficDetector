from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from app.core.database import get_db
from app.services.real_estate_service import RealEstateService

router = APIRouter()


@router.get("/properties")
async def get_properties(
    location: str = Query(..., description="Location to search for properties"),
    max_results: int = Query(20, ge=1, le=100, description="Maximum number of properties"),
    min_price: Optional[int] = Query(None, description="Minimum price filter"),
    max_price: Optional[int] = Query(None, description="Maximum price filter"),
    property_type: Optional[str] = Query(None, description="Property type filter"),
    bedrooms: Optional[int] = Query(None, description="Minimum number of bedrooms"),
    db: Session = Depends(get_db)
):
    """Get property listings for a location"""
    try:
        async with RealEstateService() as service:
            # Get properties
            properties = await service.get_simulated_properties(location, max_results)
            
            # Apply filters
            filtered_properties = []
            for prop in properties:
                # Price filter
                if min_price and prop.price and prop.price < min_price:
                    continue
                if max_price and prop.price and prop.price > max_price:
                    continue
                
                # Property type filter
                if property_type and property_type.lower() not in prop.property_type.lower():
                    continue
                
                # Bedrooms filter
                if bedrooms and prop.bedrooms and prop.bedrooms < bedrooms:
                    continue
                
                filtered_properties.append(prop)
            
            return {
                "location": location,
                "total_properties": len(filtered_properties),
                "filters_applied": {
                    "min_price": min_price,
                    "max_price": max_price,
                    "property_type": property_type,
                    "bedrooms": bedrooms
                },
                "properties": [
                    {
                        "id": prop.id,
                        "address": prop.address,
                        "city": prop.city,
                        "state": prop.state,
                        "zip_code": prop.zip_code,
                        "coordinates": {"lat": prop.latitude, "lng": prop.longitude},
                        "price": prop.price,
                        "bedrooms": prop.bedrooms,
                        "bathrooms": prop.bathrooms,
                        "square_feet": prop.square_feet,
                        "property_type": prop.property_type,
                        "price_per_sqft": prop.price_per_sqft,
                        "lot_size": prop.lot_size,
                        "year_built": prop.year_built,
                        "days_on_market": prop.days_on_market,
                        "listing_date": prop.listing_date.isoformat(),
                        "source": prop.source,
                        "url": prop.url,
                        "description": prop.description,
                        "features": prop.features
                    }
                    for prop in filtered_properties
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting properties: {str(e)}")


@router.get("/properties/near-hotspot")
async def get_properties_near_hotspot(
    hotspot_location: str = Query(..., description="Traffic hotspot location"),
    radius_miles: float = Query(2.0, ge=0.1, le=10.0, description="Search radius in miles"),
    max_results: int = Query(20, ge=1, le=50, description="Maximum number of properties"),
    db: Session = Depends(get_db)
):
    """Get properties near a traffic hotspot"""
    try:
        async with RealEstateService() as service:
            properties = await service.get_properties_near_traffic_hotspot(
                hotspot_location, radius_miles, max_results
            )
            
            return {
                "hotspot_location": hotspot_location,
                "search_radius_miles": radius_miles,
                "total_properties": len(properties),
                "properties": [
                    {
                        "id": prop.id,
                        "address": prop.address,
                        "coordinates": {"lat": prop.latitude, "lng": prop.longitude},
                        "price": prop.price,
                        "bedrooms": prop.bedrooms,
                        "bathrooms": prop.bathrooms,
                        "square_feet": prop.square_feet,
                        "property_type": prop.property_type,
                        "price_per_sqft": prop.price_per_sqft,
                        "source": prop.source,
                        "url": prop.url
                    }
                    for prop in properties
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting properties near hotspot: {str(e)}")


@router.get("/market-data/{location}")
async def get_market_data(
    location: str,
    db: Session = Depends(get_db)
):
    """Get real estate market data for a location"""
    try:
        async with RealEstateService() as service:
            market_data = await service.get_market_data(location)
            
            return {
                "location": market_data.location,
                "median_price": market_data.median_price,
                "avg_price_per_sqft": market_data.avg_price_per_sqft,
                "avg_days_on_market": market_data.avg_days_on_market,
                "total_listings": market_data.total_listings,
                "price_trend": market_data.price_trend,
                "inventory_level": market_data.inventory_level,
                "market_health_score": market_data.market_health_score,
                "last_updated": market_data.last_updated.isoformat(),
                "market_insights": {
                    "trend_description": f"Prices are {market_data.price_trend} in {location}",
                    "inventory_status": f"Inventory is {market_data.inventory_level}",
                    "market_health": "Strong" if market_data.market_health_score > 0.8 else "Good" if market_data.market_health_score > 0.6 else "Fair"
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting market data: {str(e)}")


@router.get("/investment-opportunities")
async def get_investment_opportunities(
    location: str = Query(..., description="Location to analyze"),
    investment_type: str = Query("residential", description="Type of investment (residential, commercial, rental)"),
    budget_range: str = Query("medium", description="Budget range (low, medium, high)"),
    db: Session = Depends(get_db)
):
    """Get investment opportunities based on traffic and market data"""
    try:
        async with RealEstateService() as service:
            # Get properties
            properties = await service.get_simulated_properties(location, max_results=50)
            
            # Get market data
            market_data = await service.get_market_data(location)
            
            # Score properties for investment potential
            investment_opportunities = []
            
            for prop in properties:
                # Calculate investment score based on various factors
                score = 0.0
                factors = []
                
                # Price factor (lower price = higher score for investment)
                if prop.price and market_data.median_price:
                    price_ratio = prop.price / market_data.median_price
                    if price_ratio < 0.8:
                        score += 0.3
                        factors.append("Below market price")
                    elif price_ratio < 1.0:
                        score += 0.2
                        factors.append("Market price")
                
                # Price per sqft factor
                if prop.price_per_sqft and market_data.avg_price_per_sqft:
                    sqft_ratio = prop.price_per_sqft / market_data.avg_price_per_sqft
                    if sqft_ratio < 0.9:
                        score += 0.2
                        factors.append("Good price per sqft")
                
                # Days on market factor
                if prop.days_on_market:
                    if prop.days_on_market > 60:
                        score += 0.2
                        factors.append("Long time on market - potential negotiation")
                    elif prop.days_on_market < 30:
                        score += 0.1
                        factors.append("Recent listing")
                
                # Property type factor
                if investment_type == "rental" and prop.property_type in ["Single Family", "Townhouse"]:
                    score += 0.1
                    factors.append("Good for rental")
                elif investment_type == "commercial" and prop.property_type in ["Commercial", "Multi-Family"]:
                    score += 0.1
                    factors.append("Commercial potential")
                
                # Year built factor
                if prop.year_built:
                    if 1990 <= prop.year_built <= 2010:
                        score += 0.1
                        factors.append("Good age for investment")
                
                # Only include properties with decent scores
                if score >= 0.3:
                    investment_opportunities.append({
                        "property": {
                            "id": prop.id,
                            "address": prop.address,
                            "coordinates": {"lat": prop.latitude, "lng": prop.longitude},
                            "price": prop.price,
                            "bedrooms": prop.bedrooms,
                            "bathrooms": prop.bathrooms,
                            "square_feet": prop.square_feet,
                            "property_type": prop.property_type,
                            "price_per_sqft": prop.price_per_sqft,
                            "days_on_market": prop.days_on_market,
                            "year_built": prop.year_built,
                            "source": prop.source,
                            "url": prop.url
                        },
                        "investment_score": round(score, 3),
                        "investment_factors": factors,
                        "recommended_action": "Consider" if score >= 0.6 else "Monitor" if score >= 0.4 else "Pass"
                    })
            
            # Sort by investment score
            investment_opportunities.sort(key=lambda x: x["investment_score"], reverse=True)
            
            return {
                "location": location,
                "investment_type": investment_type,
                "budget_range": budget_range,
                "market_context": {
                    "median_price": market_data.median_price,
                    "avg_price_per_sqft": market_data.avg_price_per_sqft,
                    "market_health": market_data.market_health_score
                },
                "total_opportunities": len(investment_opportunities),
                "opportunities": investment_opportunities[:10]  # Top 10
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting investment opportunities: {str(e)}")


@router.get("/atlanta-areas")
async def get_atlanta_areas():
    """Get list of Atlanta metro areas with basic info"""
    atlanta_areas = [
        {
            "name": "Atlanta",
            "type": "Downtown",
            "avg_price": 450000,
            "avg_price_per_sqft": 225,
            "traffic_level": "high",
            "investment_potential": "high"
        },
        {
            "name": "Sandy Springs",
            "type": "Suburban",
            "avg_price": 550000,
            "avg_price_per_sqft": 250,
            "traffic_level": "medium",
            "investment_potential": "high"
        },
        {
            "name": "Alpharetta",
            "type": "Suburban",
            "avg_price": 520000,
            "avg_price_per_sqft": 230,
            "traffic_level": "medium",
            "investment_potential": "high"
        },
        {
            "name": "Marietta",
            "type": "Suburban",
            "avg_price": 420000,
            "avg_price_per_sqft": 200,
            "traffic_level": "medium",
            "investment_potential": "medium"
        },
        {
            "name": "Decatur",
            "type": "Urban",
            "avg_price": 380000,
            "avg_price_per_sqft": 190,
            "traffic_level": "medium",
            "investment_potential": "high"
        },
        {
            "name": "Johns Creek",
            "type": "Suburban",
            "avg_price": 580000,
            "avg_price_per_sqft": 260,
            "traffic_level": "low",
            "investment_potential": "high"
        },
        {
            "name": "Duluth",
            "type": "Suburban",
            "avg_price": 450000,
            "avg_price_per_sqft": 200,
            "traffic_level": "medium",
            "investment_potential": "medium"
        },
        {
            "name": "Smyrna",
            "type": "Suburban",
            "avg_price": 400000,
            "avg_price_per_sqft": 190,
            "traffic_level": "medium",
            "investment_potential": "medium"
        },
        {
            "name": "Brookhaven",
            "type": "Urban",
            "avg_price": 480000,
            "avg_price_per_sqft": 200,
            "traffic_level": "medium",
            "investment_potential": "high"
        },
        {
            "name": "Dunwoody",
            "type": "Suburban",
            "avg_price": 520000,
            "avg_price_per_sqft": 220,
            "traffic_level": "medium",
            "investment_potential": "high"
        }
    ]
    
    return {
        "total_areas": len(atlanta_areas),
        "areas": atlanta_areas
    }


@router.post("/analyze-property")
async def analyze_property(
    property_id: str = Query(..., description="Property ID to analyze"),
    analysis_type: str = Query("comprehensive", description="Type of analysis"),
    db: Session = Depends(get_db)
):
    """Analyze a specific property for investment potential"""
    try:
        async with RealEstateService() as service:
            # Get property details (simulated)
            properties = await service.get_simulated_properties("Atlanta, GA", max_results=1)
            
            if not properties:
                raise HTTPException(status_code=404, detail="Property not found")
            
            property_data = properties[0]
            property_data.id = property_id  # Override with requested ID
            
            # Get market data
            market_data = await service.get_market_data(property_data.city)
            
            # Perform comprehensive analysis
            analysis = {
                "property_info": {
                    "id": property_data.id,
                    "address": property_data.address,
                    "price": property_data.price,
                    "property_type": property_data.property_type,
                    "square_feet": property_data.square_feet,
                    "bedrooms": property_data.bedrooms,
                    "bathrooms": property_data.bathrooms,
                    "year_built": property_data.year_built
                },
                "market_analysis": {
                    "median_price": market_data.median_price,
                    "price_comparison": "Below market" if property_data.price < market_data.median_price else "Above market",
                    "price_difference": property_data.price - market_data.median_price if property_data.price else 0,
                    "price_percentile": "25th" if property_data.price and property_data.price < market_data.median_price * 0.75 else "50th" if property_data.price and property_data.price < market_data.median_price else "75th"
                },
                "investment_metrics": {
                    "price_per_sqft": property_data.price_per_sqft,
                    "market_price_per_sqft": market_data.avg_price_per_sqft,
                    "sqft_efficiency": "Good" if property_data.price_per_sqft and property_data.price_per_sqft < market_data.avg_price_per_sqft else "Average",
                    "days_on_market": property_data.days_on_market,
                    "market_velocity": "Slow" if property_data.days_on_market > 60 else "Normal" if property_data.days_on_market > 30 else "Fast"
                },
                "recommendations": {
                    "investment_potential": "High" if property_data.price and property_data.price < market_data.median_price * 0.9 else "Medium",
                    "suggested_actions": [
                        "Consider for investment if price is negotiable",
                        "Monitor price changes over next 30 days",
                        "Compare with similar properties in area"
                    ],
                    "risk_factors": [
                        "Market volatility",
                        "Property condition unknown",
                        "Neighborhood changes"
                    ]
                }
            }
            
            return analysis
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing property: {str(e)}") 