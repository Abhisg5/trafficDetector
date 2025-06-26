from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.routes import traffic, analysis, investment, dashboard, real_estate
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print("🚀 TrafficDetector started successfully!")
    print("📍 Focused on Atlanta metro area")
    print("🌐 API Documentation: http://localhost:8000/docs")
    print("📊 Dashboard: http://localhost:8000/dashboard")
    yield
    # Shutdown
    print("🛑 TrafficDetector shutting down...")


app = FastAPI(
    title="TrafficDetector - Atlanta Real Estate Investment Analysis",
    description="A comprehensive platform for traffic data analysis and real estate investment insights in the Atlanta metro area",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(traffic.router, prefix="/api/v1/traffic", tags=["Traffic Data"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(investment.router, prefix="/api/v1/investment", tags=["Investment"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(real_estate.router, prefix="/api/v1/real-estate", tags=["Real Estate"])

# Mount static files for dashboard
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root():
    return {
        "message": "TrafficDetector - Atlanta Real Estate Investment Analysis",
        "version": "1.0.0",
        "region": "Atlanta Metro Area",
        "features": [
            "Traffic data collection and analysis",
            "Real estate investment opportunities",
            "Market analysis and trends",
            "Historical data tracking",
            "Property recommendations"
        ],
        "endpoints": {
            "docs": "/docs",
            "dashboard": "/dashboard",
            "traffic": "/api/v1/traffic",
            "investment": "/api/v1/investment",
            "real_estate": "/api/v1/real-estate",
            "analysis": "/api/v1/analysis"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "traffic-detector", "region": "atlanta"}


@app.get("/atlanta-info")
async def atlanta_info():
    """Get information about Atlanta metro area coverage"""
    return {
        "region": "Atlanta Metro Area",
        "covered_areas": [
            "Atlanta (Downtown)",
            "Sandy Springs",
            "Roswell", 
            "Alpharetta",
            "Marietta",
            "Decatur",
            "Johns Creek",
            "Duluth",
            "Smyrna",
            "Norcross",
            "Peachtree Corners",
            "Brookhaven",
            "Dunwoody",
            "Kennesaw",
            "Woodstock",
            "Lawrenceville",
            "Stone Mountain",
            "College Park",
            "East Point",
            "Tucker"
        ],
        "data_sources": [
            "TomTom Traffic API",
            "Simulated traffic data",
            "Real estate market data",
            "Demographic information"
        ],
        "analysis_features": [
            "Traffic pattern analysis",
            "Investment opportunity scoring",
            "Property market analysis",
            "Historical trend tracking",
            "Hotspot identification"
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 