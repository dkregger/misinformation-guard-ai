from classifier import detect_misinformation
from bot_detector import detect_bot_likelihood

def test_classification():
    print("🧪 Testing Classification System")
    print("=" * 50)
    
    test_texts = [
        "BREAKING SHOCKING NEWS! The mainstream media lies and they don't want you to know the truth! Share before they delete this! Wake up!",
        "These idiots are stupid morons who should shut up and die. I hate all of them and they are worthless trash!",
        "According to experts and peer-reviewed research, here are the verified facts from credible government sources."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text[:50]}...")
        label, score = detect_misinformation(text)
        print(f"Result: {label} (confidence: {score:.3f})")

def test_bot_detection():
    print("\n🤖 Testing Bot Detection System")
    print("=" * 50)
    
    # Obvious bot data
    bot_data = {
        'username': 'user123456789',
        'display_name': 'user123456789',
        'bio': 'Crypto enthusiast follow me DM for promo',
        'follower_count': 50,
        'following_count': 4000,
        'tweet_count': 5000,
        'account_age_days': 30,
        'profile_image_url': 'default_profile.jpg',
        'verified': False
    }
    
    # Human data
    human_data = {
        'username': 'john_teacher',
        'display_name': 'John Smith',
        'bio': 'Local teacher and community volunteer. Sharing thoughts on education policy.',
        'follower_count': 800,
        'following_count': 300,
        'tweet_count': 400,
        'account_age_days': 800,
        'profile_image_url': 'custom_profile.jpg',
        'verified': False
    }
    
    print("\nTesting Bot-like Account:")
    is_bot, score, reasons = detect_bot_likelihood(bot_data)
    print(f"Result: {'BOT' if is_bot else 'HUMAN'} (confidence: {score:.3f})")
    print(f"Reasons: {reasons}")
    
    print("\nTesting Human-like Account:")
    is_bot, score, reasons = detect_bot_likelihood(human_data)
    print(f"Result: {'BOT' if is_bot else 'HUMAN'} (confidence: {score:.3f})")
    print(f"Reasons: {reasons}")

if __name__ == "__main__":
    test_classification()
    test_bot_detection()