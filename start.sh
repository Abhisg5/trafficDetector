#!/bin/bash
echo "🚀 Starting TrafficDetector..."
echo "📍 Port: $PORT"
echo "🌍 Host: 0.0.0.0"

# Wait a moment for the environment to be ready
sleep 2

# Start the application
python3 -m app.main 