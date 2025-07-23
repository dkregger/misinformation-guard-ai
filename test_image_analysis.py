"""
Test script for image analysis functionality
Run this to verify that your image analysis setup is working correctly
"""

import requests
import json

def test_image_analysis_api():
    """Test the image analysis API endpoint"""
    print("🧪 Testing Image Analysis API")
    print("=" * 50)
    
    # Test image URLs (these are example URLs - replace with real ones)
    test_images = [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Vd-Orig.png/256px-Vd-Orig.png",  # Sample image
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Test.png/256px-Test.png"  # Another sample
    ]
    
    api_base = "http://localhost:5000"
    
    # Test 1: Check if API is running
    print("1. Testing API connection...")
    try:
        response = requests.get(f"{api_base}/")
        if response.status_code == 200:
            print("   ✅ API is running")
        else:
            print(f"   ❌ API returned status {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Cannot connect to API: {e}")
        print("   Make sure Flask is running with: python app.py")
        return
    
    # Test 2: Check image analysis endpoint
    print("\n2. Testing image analysis endpoint...")
    
    for i, image_url in enumerate(test_images, 1):
        print(f"\n   Testing image {i}: {image_url}")
        
        try:
            payload = {"image_url": image_url}
            response = requests.post(f"{api_base}/analyze-image", json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('analysis_result', {})
                
                print(f"   ✅ Analysis completed")
                print(f"   📊 Assessment: {analysis.get('assessment', 'Unknown')}")
                print(f"   🎯 Confidence: {analysis.get('overall_confidence', 0):.2f}")
                print(f"   🚨 Suspicious: {analysis.get('overall_suspicious', False)}")
                
                if analysis.get('primary_concerns'):
                    print(f"   ⚠️ Concerns: {', '.join(analysis.get('primary_concerns', []))}")
                
            elif response.status_code == 503:
                print("   ⚠️ Image analysis not available (dependencies missing)")
                break
            else:
                print(f"   ❌ Error: HTTP {response.status_code}")
                print(f"   📝 Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    # Test 3: Check image statistics
    print("\n3. Testing image statistics endpoint...")
    try:
        response = requests.get(f"{api_base}/image-stats")
        if response.status_code == 200:
            stats = response.json()
            print("   ✅ Image statistics retrieved:")
            print(f"   📊 Total analyzed: {stats.get('total_images_analyzed', 0)}")
            print(f"   🚨 Suspicious: {stats.get('suspicious_images', 0)}")
            print(f"   🎭 Deepfakes: {stats.get('deepfakes_detected', 0)}")
            print(f"   ✂️ Manipulated: {stats.get('manipulations_detected', 0)}")
        else:
            print(f"   ❌ Error getting stats: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Stats request failed: {e}")
    
    # Test 4: Enhanced stats endpoint
    print("\n4. Testing enhanced statistics...")
    try:
        response = requests.get(f"{api_base}/stats")
        if response.status_code == 200:
            stats = response.json()
            image_stats = stats.get('image_stats', {})
            print("   ✅ Enhanced statistics retrieved:")
            print(f"   📷 Posts with images: {image_stats.get('posts_with_images', 0)}")
            print(f"   🖼️ Images analyzed: {image_stats.get('total_images_analyzed', 0)}")
            print(f"   📈 Analysis rate: {image_stats.get('image_analysis_rate', 0):.1f}%")
        else:
            print(f"   ❌ Error getting enhanced stats: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Enhanced stats request failed: {e}")

def test_flagging_with_images():
    """Test adding flagged content with image analysis"""
    print("\n🚩 Testing Flagged Content with Image Analysis")
    print("=" * 50)
    
    api_base = "http://localhost:5000"
    
    # Test content with potential image URLs
    test_content = [
        {
            "content": "Breaking news! Check out this shocking image: https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Vd-Orig.png/256px-Vd-Orig.png",
            "label": "propaganda",
            "confidence": 0.8,
            "source": "test",
            "username": "test_user"
        },
        {
            "content": "Normal post without any images just text content",
            "label": "reliable", 
            "confidence": 0.3,
            "source": "test",
            "username": "normal_user"
        }
    ]
    
    for i, content in enumerate(test_content, 1):
        print(f"\n{i}. Testing content with potential images...")
        print(f"   Content: {content['content'][:60]}...")
        
        try:
            response = requests.post(f"{api_base}/add", json=content, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                print(f"   ✅ Content flagged successfully (ID: {result.get('id')})")
                print(f"   🖼️ Image analysis available: {result.get('image_analysis_available', False)}")
            else:
                print(f"   ❌ Error flagging content: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")

def test_dependencies():
    """Test if all required dependencies are installed"""
    print("📦 Testing Dependencies")
    print("=" * 50)
    
    required_packages = [
        ("opencv-python", "cv2"),
        ("Pillow", "PIL"),
        ("numpy", "numpy"),
        ("scikit-learn", "sklearn")
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} - installed")
        except ImportError:
            print(f"❌ {package_name} - missing")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    else:
        print("\n✅ All dependencies installed!")
        return True

if __name__ == "__main__":
    print("🧪 Image Analysis Test Suite")
    print("=" * 60)
    
    # Test 1: Check dependencies
    if not test_dependencies():
        print("\n❌ Cannot proceed - missing dependencies")
        exit(1)
    
    # Test 2: Test image analysis module directly
    print("\n🔍 Testing Image Analysis Module")
    print("=" * 50)
    
    try:
        from image_analyzer import ImageAnalyzer
        analyzer = ImageAnalyzer()
        print("✅ Image analyzer loaded successfully")
        
        # Quick test with a sample URL
        test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Vd-Orig.png/256px-Vd-Orig.png"
        print(f"🖼️ Testing with sample image: {test_url[:50]}...")
        
        # Note: This might take a moment
        result = analyzer.analyze_image(test_url)
        print(f"✅ Analysis completed: {result.get('assessment', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Image analyzer test failed: {e}")
    
    # Test 3: Test API endpoints
    test_image_analysis_api()
    
    # Test 4: Test flagging with images
    test_flagging_with_images()
    
    print("\n🎉 Testing Complete!")
    print("If all tests passed, your image analysis is ready to use!")
    print("Check your dashboard at: http://localhost:5000/dashboard")