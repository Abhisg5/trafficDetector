# Real Traffic Data Setup Guide

## 🚀 Getting Real Traffic Data

This guide will help you set up real traffic data collection using TomTom and HERE APIs.

### 1. Get API Keys

#### TomTom API (Recommended)
1. Go to [TomTom Developer Portal](https://developer.tomtom.com/)
2. Create a free account
3. Create a new application
4. Get your API key
5. Add to `.env`: `TOMTOM_API_KEY=your_key_here`

#### HERE API (Alternative)
1. Go to [HERE Developer Portal](https://developer.here.com/)
2. Create a free account
3. Create a new project
4. Get your API key
5. Add to `.env`: `HERE_API_KEY=your_key_here`

### 2. Set Up Environment

Create a `.env` file in your project root:

```bash
# Copy the template
cp env_template.txt .env

# Edit the .env file and add your API keys
nano .env
```

Add your API keys:
```env
TOMTOM_API_KEY=your_tomtom_api_key_here
HERE_API_KEY=your_here_api_key_here
```

### 3. Test Real Traffic Data

Start the server:
```bash
python3 -m app.main
```

Test traffic collection:
```bash
curl -X GET "http://localhost:8000/api/v1/traffic/collect/Atlanta" -H "accept: application/json"
```

## 🔥 Traffic Hotspots API

### 90-Day Hotspots Analysis

Get traffic hotspots based on 90 days of data:

```bash
curl -X GET "http://localhost:8000/api/v1/traffic/hotspots/90days?region=Atlanta&min_congestion=0.4" -H "accept: application/json"
```

**Parameters:**
- `region`: Area to analyze (e.g., "Atlanta", "Georgia")
- `min_congestion`: Minimum congestion score (0.0-1.0, default: 0.4)

**Response includes:**
- Top 20 traffic hotspots
- Average congestion scores
- Data consistency metrics
- Traffic level distribution
- Regional summary statistics

### Custom Period Hotspots

Get hotspots for any time period:

```bash
curl -X GET "http://localhost:8000/api/v1/traffic/hotspots?region=Atlanta&min_congestion=0.5&days=30" -H "accept: application/json"
```

**Parameters:**
- `region`: Area to analyze
- `min_congestion`: Minimum congestion score
- `days`: Number of days to analyze (1-365)

## 📊 Building Traffic Data Database

### Collect Data for Multiple Locations

Use the provided script to collect data for Atlanta metro area:

```bash
python3 collect_traffic_data.py
```

This script will:
- Collect traffic data for 20 Atlanta locations
- Process in batches to respect API limits
- Test the hotspots endpoint
- Provide collection summary

### Manual Data Collection

Collect data for specific locations:

```bash
# Single location
curl -X GET "http://localhost:8000/api/v1/traffic/collect/Atlanta" -H "accept: application/json"

# Multiple locations
curl -X POST "http://localhost:8000/api/v1/traffic/bulk-collect" \
  -H "Content-Type: application/json" \
  -d '["Atlanta, GA", "Sandy Springs, GA", "Marietta, GA"]'
```

## 🏆 Hotspot Analysis Examples

### 1. High Congestion Hotspots (90 days)
```bash
curl -X GET "http://localhost:8000/api/v1/traffic/hotspots/90days?region=Atlanta&min_congestion=0.7"
```

### 2. All Traffic Hotspots (30 days)
```bash
curl -X GET "http://localhost:8000/api/v1/traffic/hotspots?region=Atlanta&min_congestion=0.3&days=30"
```

### 3. Regional Analysis
```bash
curl -X GET "http://localhost:8000/api/v1/traffic/hotspots/90days?region=Georgia&min_congestion=0.5"
```

## 📈 Understanding Hotspot Scores

**Hotspot Score Calculation:**
- Based on average congestion and data consistency
- Higher scores = worse traffic conditions
- Range: 0.0 (no congestion) to 1.0 (severe congestion)

**Traffic Levels:**
- `low`: Congestion score < 0.3
- `medium`: Congestion score 0.3-0.5
- `high`: Congestion score 0.5-0.7
- `severe`: Congestion score > 0.7

**Data Consistency:**
- Measures how frequently data was collected
- Higher consistency = more reliable hotspot score

## 🔧 Troubleshooting

### No Traffic Data Available

1. **Check API Keys:**
   ```bash
   # Verify keys are loaded
   python3 -c "from app.core.config import settings; print('TomTom:', bool(settings.tomtom_api_key)); print('HERE:', bool(settings.here_api_key))"
   ```

2. **Test API Keys:**
   ```bash
   # Test TomTom API directly
   curl "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key=YOUR_KEY&point=33.7490,-84.3880&unit=KMPH"
   ```

3. **Check Location Support:**
   - Not all locations have traffic data
   - Try major cities and highways
   - Use coordinates near major roads

### API Rate Limits

- TomTom: 60 requests/minute (free tier)
- HERE: 250,000 requests/month (free tier)
- Use batch collection with delays

### Data Quality Issues

- Collect data over multiple days
- Use multiple data sources
- Focus on major traffic corridors

## 🎯 Investment Analysis

Use hotspot data for real estate investment decisions:

1. **High Congestion Areas:**
   - Potential for commercial development
   - Transit-oriented development opportunities
   - Higher property values near major roads

2. **Low Congestion Areas:**
   - Residential development opportunities
   - Lower property values
   - Better quality of life

3. **Trending Hotspots:**
   - Areas with increasing congestion
   - Emerging development opportunities
   - Future investment potential

## 📱 API Documentation

Full API documentation available at:
```
http://localhost:8000/docs
```

## 🚀 Next Steps

1. Set up your API keys
2. Collect 90 days of traffic data
3. Analyze hotspots for investment opportunities
4. Integrate with real estate data
5. Build predictive models

For questions or issues, check the logs or API documentation. 