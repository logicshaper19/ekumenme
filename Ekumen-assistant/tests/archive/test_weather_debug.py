"""
Debug test to see why weather API isn't being called
"""

import os
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load environment
load_dotenv()

print("\n" + "="*80)
print("WEATHER API DEBUG TEST")
print("="*80)

# Check environment variables
print("\n📋 Environment Variables:")
print(f"   WEATHER_API_KEY: {os.getenv('WEATHER_API_KEY')[:10] if os.getenv('WEATHER_API_KEY') else 'NOT SET'}...")
print(f"   OPENWEATHER_API_KEY: {os.getenv('OPENWEATHER_API_KEY') or 'NOT SET'}")

# Import and test tool
from app.tools.weather_agent.get_weather_data_tool import GetWeatherDataTool

tool = GetWeatherDataTool()

print("\n🔧 Testing tool with use_real_api=True...")
result = tool._run(location="Dourdan", days=3, use_real_api=True)

print("\n📊 Result:")
print(result[:500])  # First 500 chars

import json
data = json.loads(result)
print(f"\n✅ Data source: {data.get('data_source', 'UNKNOWN')}")
print(f"✅ Location: {data.get('location', 'UNKNOWN')}")

