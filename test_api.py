import requests

print("🧪 Testing API connection...")

try:
    # Test basic connection
    response = requests.get("http://localhost:5000")
    print(f"✅ Connection successful: {response.status_code}")
    print(f"Response: {response.text}")
    
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Flask app!")
    print("Make sure 'python app.py' is running in another terminal")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("Test complete.")