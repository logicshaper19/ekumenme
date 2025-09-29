"""
Test script to verify weather API credentials and functionality
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_weatherapi_com():
    """Test WeatherAPI.com (the key in .env)"""
    print("\n" + "="*80)
    print("TEST 1: WeatherAPI.com")
    print("="*80)
    
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        print("❌ WEATHER_API_KEY not found in .env")
        return False
    
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Test API call
    location = "Dourdan"
    url = f"http://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": api_key,
        "q": location,
        "days": 7,
        "lang": "fr"
    }
    
    try:
        print(f"\n📡 Testing API call for {location}...")
        response = requests.get(url, params=params, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API call successful!")
            print(f"\n📍 Location: {data['location']['name']}, {data['location']['country']}")
            print(f"   Coordinates: {data['location']['lat']}, {data['location']['lon']}")
            print(f"\n🌤️  Current Weather:")
            print(f"   Temperature: {data['current']['temp_c']}°C")
            print(f"   Condition: {data['current']['condition']['text']}")
            print(f"   Humidity: {data['current']['humidity']}%")
            print(f"   Wind: {data['current']['wind_kph']} km/h {data['current']['wind_dir']}")
            
            print(f"\n📅 Forecast ({len(data['forecast']['forecastday'])} days):")
            for day in data['forecast']['forecastday'][:3]:
                print(f"   {day['date']}: {day['day']['mintemp_c']}°C - {day['day']['maxtemp_c']}°C, {day['day']['condition']['text']}")
            
            return True
        else:
            print(f"   ❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_openweathermap():
    """Test OpenWeatherMap API (if configured)"""
    print("\n" + "="*80)
    print("TEST 2: OpenWeatherMap API")
    print("="*80)
    
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        print("⚠️  OPENWEATHER_API_KEY not found in .env (optional)")
        return None
    
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Test API call
    lat, lon = 48.53, 2.05  # Dourdan coordinates
    url = f"https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
        "lang": "fr"
    }
    
    try:
        print(f"\n📡 Testing API call for Dourdan ({lat}, {lon})...")
        response = requests.get(url, params=params, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API call successful!")
            print(f"\n📍 Location: {data['city']['name']}, {data['city']['country']}")
            print(f"   Coordinates: {data['city']['coord']['lat']}, {data['city']['coord']['lon']}")
            
            print(f"\n📅 Forecast ({len(data['list'])} entries):")
            for item in data['list'][:3]:
                dt = item['dt_txt']
                temp = item['main']['temp']
                desc = item['weather'][0]['description']
                print(f"   {dt}: {temp}°C, {desc}")
            
            return True
        else:
            print(f"   ❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_weather_tool():
    """Test the GetWeatherDataTool"""
    print("\n" + "="*80)
    print("TEST 3: GetWeatherDataTool")
    print("="*80)
    
    try:
        from app.tools.weather_agent.get_weather_data_tool import GetWeatherDataTool
        
        tool = GetWeatherDataTool()
        print("✓ Tool imported successfully")
        
        # Test with mock data first
        print("\n📊 Testing with mock data...")
        result = tool._run(location="Dourdan", days=3, use_real_api=False)
        data = json.loads(result)
        
        if "error" in data:
            print(f"   ❌ Error: {data['error']}")
            return False
        
        print(f"   ✅ Mock data retrieved successfully")
        print(f"   Location: {data['location']}")
        print(f"   Data source: {data['data_source']}")
        print(f"   Days: {data['total_days']}")
        
        # Test with real API
        print("\n📡 Testing with real API...")
        result = tool._run(location="Dourdan", days=3, use_real_api=True)
        data = json.loads(result)
        
        if "error" in data:
            print(f"   ⚠️  Real API failed (falling back to mock): {data['error']}")
        else:
            print(f"   ✅ Real API data retrieved successfully")
            print(f"   Location: {data['location']}")
            print(f"   Data source: {data['data_source']}")
            print(f"   Days: {data['total_days']}")
            
            if data['data_source'] == 'mock_data':
                print(f"   ⚠️  Note: Fell back to mock data (API key may not be configured)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("WEATHER API CREDENTIALS & FUNCTIONALITY TEST")
    print("="*80)
    
    results = {
        "WeatherAPI.com": test_weatherapi_com(),
        "OpenWeatherMap": test_openweathermap(),
        "GetWeatherDataTool": test_weather_tool()
    }
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASSED"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⚠️  SKIPPED"
        print(f"{status} - {test_name}")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    if results["WeatherAPI.com"]:
        print("✅ WeatherAPI.com is working! This is your primary weather data source.")
        print("   To use it in GetWeatherDataTool, we need to add support for it.")
    else:
        print("❌ WeatherAPI.com is not working. Check your API key.")
    
    if results["OpenWeatherMap"] is None:
        print("\n⚠️  OpenWeatherMap is not configured.")
        print("   To add it, get a free API key from: https://openweathermap.org/api")
        print("   Then add to .env: OPENWEATHER_API_KEY=your_key_here")
    elif results["OpenWeatherMap"]:
        print("\n✅ OpenWeatherMap is working!")
    
    if results["GetWeatherDataTool"]:
        print("\n✅ GetWeatherDataTool is functional (using mock data as fallback)")
    
    print("\n" + "="*80)
    
    return all(r for r in results.values() if r is not None)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

