from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import asyncio

from app.core.config import settings

# Create database engine
engine = create_engine(settings.database_url, echo=settings.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


class TrafficData(Base):
    __tablename__ = "traffic_data"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    traffic_level = Column(String)  # low, medium, high, severe
    congestion_score = Column(Float)  # 0-1
    average_speed = Column(Float)  # km/h
    travel_time = Column(Float)  # minutes
    distance = Column(Float)  # km
    source = Column(String)  # google, tomtom, etc.
    raw_data = Column(Text)  # JSON string of raw API response


class InvestmentOpportunity(Base):
    __tablename__ = "investment_opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    investment_score = Column(Float)  # 0-1
    traffic_score = Column(Float)  # 0-1
    demographic_score = Column(Float)  # 0-1
    economic_score = Column(Float)  # 0-1
    risk_score = Column(Float)  # 0-1
    predicted_roi = Column(Float)  # percentage
    property_type = Column(String)  # residential, commercial, mixed
    price_range = Column(String)  # low, medium, high
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class TrafficHotspot(Base):
    __tablename__ = "traffic_hotspots"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    hotspot_score = Column(Float)  # 0-1
    peak_hours = Column(String)  # JSON string of peak hours
    average_congestion = Column(Float)  # 0-1
    frequency = Column(Integer)  # how often this area is congested
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String)  # traffic, investment, demographic
    location = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    result_data = Column(Text)  # JSON string of analysis results
    confidence_score = Column(Float)  # 0-1
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # when this analysis becomes stale


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database
async def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")


# Sync version for non-async contexts
def init_db_sync():
    """Synchronous database initialization"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully") 