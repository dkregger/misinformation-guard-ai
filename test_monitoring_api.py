import requests
import json
from datetime import datetime

API_BASE = "http://localhost:5000"

def test_monitoring_endpoints():
    print("🧪 Testing Monitoring API Endpoints")
    print("=" * 40)
    
    # Test 1: Create a monitoring session
    print("1. Testing POST /monitoring/sessions...")
    session_data = {
        "session_type": "test",
        "use_real_data": False
    }
    
    try:
        response = requests.post(f"{API_BASE}/monitoring/sessions", json=session_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 201:
            session_id = response.json().get("session_id")
            print(f"   ✅ Session created with ID: {session_id}")
            
            # Test 2: Update the session
            print(f"\n2. Testing PUT /monitoring/sessions/{session_id}...")
            update_data = {
                "end_time": datetime.utcnow().isoformat(),
                "duration_seconds": 30.5,
                "total_articles_attempted": 5,
                "total_articles_successfully_scraped": 4,
                "total_articles_analyzed": 4,
                "total_flagged": 2,
                "scraping_success_rate": 80.0,
                "flagging_rate": 50.0,
                "sources_attempted": json.dumps({"test.com": 2, "example.com": 3}),
                "sources_successful": json.dumps({"test.com": 1, "example.com": 3}),
                "propaganda_count": 1,
                "toxic_count": 1,
                "bot_count": 0,
                "reliable_count": 2,
                "flag_reasons": json.dumps({"propaganda": 1, "toxic": 1}),
                "error_count": 1,
                "error_details": json.dumps([{"error": "test error", "timestamp": "2025-01-01T00:00:00"}])
            }
            
            try:
                response = requests.put(f"{API_BASE}/monitoring/sessions/{session_id}", json=update_data)
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
                if response.status_code == 200:
                    print(f"   ✅ Session updated successfully")
                else:
                    print(f"   ❌ Failed to update session")
                    
            except Exception as e:
                print(f"   ❌ Error updating session: {e}")
            
            # Test 3: Get sessions
            print(f"\n3. Testing GET /monitoring/sessions...")
            try:
                response = requests.get(f"{API_BASE}/monitoring/sessions")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    sessions = response.json()
                    print(f"   ✅ Retrieved {len(sessions)} sessions")
                    if sessions:
                        print(f"   Latest session: {sessions[0].get('session_type', 'unknown')}")
                else:
                    print(f"   ❌ Failed to get sessions: {response.text}")
            except Exception as e:
                print(f"   ❌ Error getting sessions: {e}")
            
            # Test 4: Get summary stats
            print(f"\n4. Testing GET /monitoring/stats/summary...")
            try:
                response = requests.get(f"{API_BASE}/monitoring/stats/summary")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    summary = response.json()
                    print(f"   ✅ Retrieved summary stats")
                    print(f"   Total sessions: {summary.get('total_sessions', 0)}")
                    print(f"   Total articles processed: {summary.get('total_articles_processed', 0)}")
                else:
                    print(f"   ❌ Failed to get summary: {response.text}")
            except Exception as e:
                print(f"   ❌ Error getting summary: {e}")
        
        else:
            print(f"   ❌ Failed to create session")
            
    except Exception as e:
        print(f"   ❌ Error creating session: {e}")

if __name__ == "__main__":
    test_monitoring_endpoints()