"""
Test script for IRCTC API integration
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.irctc_service import irctc_service

async def test_irctc_integration():
    """Test the IRCTC API integration"""
    
    print("🚂 Testing IRCTC API Integration")
    print("=" * 50)
    
    # Test train number from the screenshot
    test_train_number = "12936"
    
    print(f"📡 Fetching schedule for train {test_train_number}...")
    
    try:
        # Test single train fetch
        result = await irctc_service.get_train_schedule(test_train_number)
        
        print(f"✅ API Response received")
        print(f"📊 Success: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"🚆 Train Name: {result.get('train_name', 'N/A')}")
            print(f"🏁 Source: {result.get('source_station', {}).get('station_name', 'N/A')}")
            print(f"🎯 Destination: {result.get('destination_station', {}).get('station_name', 'N/A')}")
            print(f"🚉 Total Stations: {result.get('total_stations', 0)}")
            print(f"📍 Current Status: {result.get('current_status', {}).get('status', 'N/A')}")
            print(f"⏰ Last Updated: {result.get('last_updated', 'N/A')}")
            
            # Show first few stations
            stations = result.get('stations', [])
            if stations:
                print(f"\n🗺️  First 3 stations:")
                for i, station in enumerate(stations[:3]):
                    print(f"   {i+1}. {station.get('station_name', 'N/A')} ({station.get('station_code', 'N/A')})")
                    print(f"      Arr: {station.get('arrival_time', 'N/A')} | Dep: {station.get('departure_time', 'N/A')}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        # Test cache functionality
        print(f"\n🗄️  Testing cache...")
        cache_stats = irctc_service.get_cache_stats()
        print(f"📈 Cache Stats: {cache_stats}")
        
        # Test multiple trains
        print(f"\n🔄 Testing multiple trains fetch...")
        multiple_results = await irctc_service.get_multiple_trains(["12936", "12937"])
        print(f"📊 Fetched {len(multiple_results)} train schedules")
        
        print(f"\n✅ Integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_irctc_integration())
