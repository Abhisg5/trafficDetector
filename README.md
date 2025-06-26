# TrafficDetector - Atlanta Real Estate Investment Analysis

A comprehensive platform for traffic data analysis and real estate investment insights in the Atlanta metro area. This application collects traffic data, analyzes patterns, and identifies investment opportunities based on traffic hotspots and market trends.

## 🌟 Features

### Traffic Analysis
- **Real-time traffic data collection** from multiple sources (TomTom, HERE, INRIX)
- **Historical data tracking** (up to 1 year of data)
- **Traffic pattern analysis** and hotspot identification
- **Congestion scoring** and trend analysis

### Real Estate Integration
- **Property listings** from Zillow and other sources
- **Market data analysis** for Atlanta metro areas
- **Investment opportunity scoring** based on traffic patterns
- **Property recommendations** near traffic hotspots

### Investment Analysis
- **Multi-factor scoring** for investment potential
- **Market trend analysis** and predictions
- **ROI calculations** and risk assessment
- **Comparative market analysis**

### Data Collection
- **Continuous data collection** with configurable schedules
- **Rate limiting** and API management
- **Data export** in multiple formats (JSON, CSV)
- **Historical data backfill** capabilities

## 🗺️ Atlanta Metro Coverage

The application focuses on the Atlanta metro area, covering:

**Core Areas:**
- Atlanta (Downtown)
- Sandy Springs
- Alpharetta
- Marietta
- Decatur

**Suburban Areas:**
- Johns Creek, Duluth, Smyrna
- Norcross, Peachtree Corners
- Brookhaven, Dunwoody
- Kennesaw, Woodstock
- Lawrenceville, Stone Mountain
- College Park, East Point, Tucker

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd trafficDetector
```

### 2. Set Up Environment
```bash
# Copy the environment template
cp env_template.txt .env

# Edit .env with your API keys
nano .env
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 5. Run the Application
```bash
python -m app.main
```

The application will be available at:
- **API Documentation**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8000/dashboard
- **Health Check**: http://localhost:8000/health

## 🔑 API Keys Required

### Required APIs (for full functionality)

#### Traffic Data APIs
- **TomTom API** (Free tier available)
  - Get key: https://developer.tomtom.com/
  - Provides real-time and historical traffic data
  - Rate limit: 60 requests/minute (free tier)

- **HERE Traffic API** (Alternative)
  - Get key: https://developer.here.com/
  - Comprehensive traffic data
  - Rate limit: Varies by plan

- **INRIX Traffic API** (Professional)
  - Get key: https://developer.inrix.com/
  - High-quality traffic data
  - Rate limit: Varies by plan

#### Real Estate APIs
- **Zillow API** (Limited access)
  - Get key: https://www.zillow.com/developers/
  - Property listings and market data
  - Note: Requires partnership for full access

- **Realtor.com API** (Alternative)
  - Get key: https://developer.realtor.com/
  - Property data and market trends

- **Redfin API** (Alternative)
  - Get key: https://www.redfin.com/developers
  - Property listings and market data

#### Demographic & Economic Data
- **US Census Bureau API** (Free)
  - Get key: https://api.census.gov/data/key_signup.html
  - Demographic and economic data

- **Bureau of Labor Statistics API** (Free)
  - Get key: https://www.bls.gov/developers/
  - Employment and economic data

- **Federal Reserve Economic Data (FRED) API** (Free)
  - Get key: https://fred.stlouisfed.org/docs/api/api_key.html
  - Economic indicators

### Optional APIs (for enhanced features)

#### Mapping & Geocoding
- **Google Maps API** (Optional)
  - Get key: https://developers.google.com/maps/documentation/javascript/get-api-key
  - Geocoding and mapping features

- **Mapbox API** (Alternative)
  - Get key: https://account.mapbox.com/access-tokens/
  - Mapping and geocoding

#### Weather Data
- **OpenWeatherMap API** (Free tier available)
  - Get key: https://openweathermap.org/api
  - Weather data for traffic correlation

- **WeatherAPI** (Alternative)
  - Get key: https://www.weatherapi.com/
  - Weather data

## 📊 Usage Examples

### 1. Get Traffic Data
```bash
# Get current traffic data for Atlanta
curl "http://localhost:8000/api/v1/traffic/current?location=Atlanta,GA"

# Get traffic hotspots
curl "http://localhost:8000/api/v1/traffic/hotspots?radius=5000"
```

### 2. Find Investment Opportunities
```bash
# Get investment opportunities in Sandy Springs
curl "http://localhost:8000/api/v1/real-estate/investment-opportunities?location=Sandy%20Springs,GA&investment_type=residential"

# Get properties near traffic hotspots
curl "http://localhost:8000/api/v1/real-estate/properties/near-hotspot?hotspot_location=Atlanta,GA&radius_miles=2.0"
```

### 3. Market Analysis
```bash
# Get market data for Alpharetta
curl "http://localhost:8000/api/v1/real-estate/market-data/Alpharetta,GA"

# Get Atlanta area information
curl "http://localhost:8000/api/v1/real-estate/atlanta-areas"
```

### 4. Historical Data Analysis
```bash
# Get traffic trends
curl "http://localhost:8000/api/v1/analysis/trends?location=Atlanta,GA&days=30"

# Get investment analysis
curl "http://localhost:8000/api/v1/investment/analyze?location=Marietta,GA"
```

## 🔄 Data Collection

### Continuous Collection
The application can run continuous data collection in the background:

```python
from app.services.historical_data_collector import start_background_collection

# Start background collection
collection_thread = start_background_collection()
```

### Historical Data Backfill
```python
from app.services.historical_data_collector import HistoricalDataCollector

async with HistoricalDataCollector() as collector:
    # Collect 1 year of historical data
    await collector.collect_historical_data(days=365)
```

### Data Export
```python
# Export data in JSON format
filename = collector.export_data(format="json", location="Atlanta,GA", days=30)

# Export data in CSV format
filename = collector.export_data(format="csv", location="Atlanta,GA", days=30)
```

## 📈 Investment Analysis Features

### Scoring Factors
The investment analysis considers multiple factors:

1. **Traffic Patterns**
   - Congestion levels
   - Traffic flow consistency
   - Peak hour analysis

2. **Market Conditions**
   - Price trends
   - Inventory levels
   - Days on market

3. **Property Characteristics**
   - Price per square foot
   - Property age
   - Location desirability

4. **Economic Indicators**
   - Employment data
   - Economic growth
   - Demographic trends

### Investment Recommendations
- **High Potential**: Score ≥ 0.6
- **Monitor**: Score 0.4-0.6
- **Pass**: Score < 0.4

## 🛠️ Configuration

### Environment Variables
Key configuration options in `.env`:

```bash
# Data Collection Settings
HISTORICAL_DATA_DAYS=365
DATA_COLLECTION_INTERVAL_HOURS=1
MAX_CONCURRENT_REQUESTS=10

# Investment Analysis Settings
MIN_INVESTMENT_SCORE=0.3
MAX_INVESTMENT_SCORE=1.0
DEFAULT_ROI_THRESHOLD=0.08

# Atlanta-specific Settings
ATLANTA_ANALYSIS_RADIUS=50
ATLANTA_PROPERTY_TYPES=residential,commercial,mixed-use
```

### Rate Limiting
Configure API rate limits to avoid hitting limits:

```bash
TOMTOM_RATE_LIMIT=60
ZILLOW_RATE_LIMIT=30
CENSUS_RATE_LIMIT=100
```

## 📊 Dashboard Features

The web dashboard provides:

- **Real-time traffic maps** with congestion visualization
- **Investment opportunity heatmaps**
- **Market trend charts**
- **Property listing browser**
- **Historical data analysis**
- **Export capabilities**

## 🔧 Development

### Project Structure
```
trafficDetector/
├── app/
│   ├── api/routes/          # API endpoints
│   ├── core/               # Configuration and database
│   ├── data/               # Data collection
│   ├── services/           # Business logic
│   └── main.py            # FastAPI application
├── requirements.txt        # Dependencies
├── env_template.txt       # Environment template
└── README.md             # This file
```

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black app/
flake8 app/
```

## 📝 API Documentation

Full API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the API documentation
- Review the logs in `logs/traffic_detector.log`
- Open an issue on GitHub

## 🔮 Future Enhancements

- Machine learning predictions for traffic patterns
- Advanced property valuation models
- Integration with more real estate platforms
- Mobile application
- Real-time alerts and notifications
- Advanced visualization and reporting 