"""
Detailed test of GetWeatherDataTool with real API data
"""

import json
from app.tools.weather_agent.get_weather_data_tool import GetWeatherDataTool

def test_weather_tool_detailed():
    """Test weather tool with detailed output"""
    
    print("\n" + "="*80)
    print("DETAILED WEATHER TOOL TEST - Real API Data")
    print("="*80)
    
    tool = GetWeatherDataTool()
    
    # Test for Dourdan
    print("\n📍 Testing: Dourdan (Coffee planting location)")
    print("-" * 80)
    
    result = tool._run(location="Dourdan", days=7, use_real_api=True)
    data = json.loads(result)
    
    if "error" in data:
        print(f"❌ Error: {data['error']}")
        return False
    
    print(f"\n✅ Weather data retrieved successfully!")
    print(f"   Location: {data['location']}")
    print(f"   Coordinates: {data['coordinates']['lat']}, {data['coordinates']['lon']}")
    print(f"   Data Source: {data['data_source']}")
    print(f"   Retrieved: {data['retrieved_at']}")
    print(f"   Forecast Days: {data['total_days']}")
    
    print(f"\n🌤️  7-Day Weather Forecast:")
    print("-" * 80)
    
    for condition in data['weather_conditions']:
        print(f"\n📅 {condition['date']}")
        print(f"   🌡️  Temperature: {condition['temperature_min']}°C - {condition['temperature_max']}°C")
        print(f"   💧 Humidity: {condition['humidity']}%")
        print(f"   💨 Wind: {condition['wind_speed']} km/h {condition['wind_direction']}")
        print(f"   🌧️  Precipitation: {condition['precipitation']} mm")
        print(f"   ☁️  Cloud Cover: {condition['cloud_cover']}")
        print(f"   ☀️  UV Index: {condition['uv_index']}")
        
        # Agricultural insights
        if condition['temperature_min'] < 10:
            print(f"   ⚠️  Cold warning: Min temp below 10°C (not suitable for coffee)")
        if condition['precipitation'] > 10:
            print(f"   ⚠️  Heavy rain: {condition['precipitation']}mm (avoid interventions)")
        if condition['wind_speed'] > 30:
            print(f"   ⚠️  Strong wind: {condition['wind_speed']} km/h (avoid spraying)")
    
    # Analysis for coffee cultivation
    print("\n" + "="*80)
    print("COFFEE CULTIVATION ANALYSIS (Based on Weather Data)")
    print("="*80)
    
    temps = [c['temperature_min'] for c in data['weather_conditions']]
    avg_min_temp = sum(temps) / len(temps)
    
    print(f"\n📊 Temperature Analysis:")
    print(f"   Average Min Temperature: {avg_min_temp:.1f}°C")
    print(f"   Lowest Temperature: {min(temps)}°C")
    print(f"   Highest Min Temperature: {max(temps)}°C")
    
    if avg_min_temp < 15:
        print(f"\n❌ Coffee Feasibility: NOT SUITABLE")
        print(f"   Coffee requires minimum 15°C, current average is {avg_min_temp:.1f}°C")
        print(f"   Recommendation: Indoor/greenhouse cultivation only")
    else:
        print(f"\n✅ Coffee Feasibility: POSSIBLE")
        print(f"   Temperature range is suitable for coffee cultivation")
    
    # Test for other locations
    print("\n" + "="*80)
    print("COMPARISON: Other French Locations")
    print("="*80)
    
    locations = ["Paris", "Lyon", "Marseille", "Normandie"]
    
    for loc in locations:
        result = tool._run(location=loc, days=3, use_real_api=True)
        data = json.loads(result)
        
        if "error" not in data:
            temps = [c['temperature_min'] for c in data['weather_conditions']]
            avg_temp = sum(temps) / len(temps)
            print(f"\n📍 {data['location']}: Avg min temp {avg_temp:.1f}°C")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)
    
    return True

if __name__ == "__main__":
    test_weather_tool_detailed()

