from classifier import detect_misinformation
from bot_detector import detect_bot_likelihood, create_mock_user_data
import requests
import time
import datetime
import json

def create_obvious_bot_data(username):
    """Create obviously bot-like user data for testing"""
    return {
        'username': f'{username}123456789',  # Numbers at end
        'display_name': f'{username}123456789',  # Same as username
        'bio': 'Crypto enthusiast follow me DM for promo',  # Generic bot bio
        'follower_count': 50,
        'following_count': 4000,  # High follow ratio
        'tweet_count': 5000,  # Lots of tweets
        'account_age_days': 30,  # New account
        'profile_image_url': 'default_profile.jpg',
        'verified': False
    }

def create_obvious_human_data(username):
    """Create obviously human-like user data for testing"""
    return {
        'username': username,
        'display_name': f'{username.title()} Smith',
        'bio': 'Local teacher and community volunteer. Sharing thoughts on education policy.',
        'follower_count': 800,
        'following_count': 300,  # Normal follow ratio
        'tweet_count': 400,
        'account_age_days': 800,  # Older account
        'profile_image_url': 'custom_profile.jpg',
        'verified': False
    }

def scrape_tweets(keyword, since_days=1, max_results=20):
    """Mock function that creates test tweets for development"""
    print(f"🧪 Using mock data for testing (keyword: {keyword})")
    return [
        {
            'user': 'propaganda_user',
            'content': f'BREAKING SHOCKING NEWS about {keyword}! The mainstream media lies and they don\'t want you to know the truth! Share before they delete this! Wake up!',
            'date': datetime.datetime.utcnow().isoformat(),
            'url': 'https://twitter.com/test/status/1',
            'user_data': create_obvious_bot_data("propaganda_bot")
        },
        {
            'user': 'reliable_user', 
            'content': f'According to experts and peer-reviewed research, here are the verified facts about {keyword} from credible government sources.',
            'date': datetime.datetime.utcnow().isoformat(),
            'url': 'https://twitter.com/test/status/2',
            'user_data': create_obvious_human_data("reliable_human")
        },
        {
            'user': 'toxic_user',
            'content': f'These idiots supporting {keyword} are stupid morons who should shut up and die. I hate all of them and they are worthless trash!',
            'date': datetime.datetime.utcnow().isoformat(),
            'url': 'https://twitter.com/test/status/3',
            'user_data': create_obvious_bot_data("toxic_bot")
        },
        {
            'user': 'conspiracy_user',
            'content': f'The deep state conspiracy around {keyword} is being covered up! Hidden truth revealed! Secret agenda exposed! Must share urgently!',
            'date': datetime.datetime.utcnow().isoformat(),
            'url': 'https://twitter.com/test/status/4',
            'user_data': create_obvious_bot_data("conspiracy_bot")
        },
        {
            'user': 'neutral_user',
            'content': f'Just heard some news about {keyword}. Interesting developments happening lately.',
            'date': datetime.datetime.utcnow().isoformat(),
            'url': 'https://twitter.com/test/status/5',
            'user_data': create_obvious_human_data("neutral_human")
        }
    ]

# Replace with your API URL
APP_URL = "http://localhost:5000/add"
KEYWORD = "Sherrod Brown"  # Change to your candidate or topic

def main():
    print(f"Starting to scrape tweets for keyword: {KEYWORD}")
    
    try:
        tweets = scrape_tweets(KEYWORD)
        print(f"Found {len(tweets)} tweets to analyze")

        flagged_count = 0
        
        for i, tweet in enumerate(tweets):
            print(f"\nAnalyzing tweet {i+1}/{len(tweets)}")
            print(f"Content: {tweet['content'][:80]}...")
            
            try:
                print(f"Content preview: {tweet['content'][:100]}...")
                
                # Analyze content for misinformation
                label, score = detect_misinformation(tweet['content'])
                print(f"  Content Label: {label}, Score: {score:.3f}")
                
                # Analyze user for bot likelihood
                user_data = tweet.get('user_data', {})
                print(f"  User data keys: {list(user_data.keys())}")
                
                is_bot, bot_score, bot_reasons = detect_bot_likelihood(user_data)
                print(f"  Bot Analysis: {'BOT' if is_bot else 'HUMAN'} (confidence: {bot_score:.3f})")
                
                if bot_reasons:
                    print(f"  Bot Indicators ({len(bot_reasons)}): {bot_reasons}")

                # Debug thresholds
                print(f"  Checking thresholds:")
                print(f"    Propaganda: {label.lower() == 'propaganda'} and {score} > 0.5 = {label.lower() == 'propaganda' and score > 0.5}")
                print(f"    Toxic: {label.lower() == 'toxic'} and {score} > 0.3 = {label.lower() == 'toxic' and score > 0.3}")
                print(f"    Bot: {is_bot} and {bot_score} > 0.6 = {is_bot and bot_score > 0.6}")

                # Flag both toxic content and propaganda, or bot accounts
                should_flag = False
                flag_reason = ""
                
                # Lower thresholds for testing
                if label.lower() == "propaganda" and score > 0.3:  # Lowered from 0.5
                    should_flag = True
                    flag_reason = f"PROPAGANDA (confidence: {score:.3f})"
                elif label.lower() == "toxic" and score > 0.2:  # Lowered from 0.3
                    should_flag = True  
                    flag_reason = f"TOXIC (confidence: {score:.3f})"
                elif is_bot and bot_score > 0.4:  # Lowered from 0.6
                    should_flag = True
                    flag_reason = f"BOT ACCOUNT (confidence: {bot_score:.3f})"
                
                if should_flag:
                    # UPDATED PAYLOAD - includes all required fields but review fields default to False/None
                    payload = {
                        "content": tweet['content'],
                        "confidence": score,
                        "label": label,
                        "url": tweet['url'],
                        "source": "twitter",
                        "username": tweet['user'],
                        "is_bot": is_bot,
                        "bot_confidence": bot_score,
                        "bot_reasons": json.dumps(bot_reasons),  # Convert list to JSON string
                        # NOTE: is_reviewed and reviewed_at will be set to default values by the database
                        # is_reviewed defaults to False, reviewed_at defaults to None
                    }
                    
                    print(f"  🚩 Flagging as {flag_reason}")
                    print(f"  📡 Sending payload with {len(payload)} fields")
                    
                    # Send to our API
                    try:
                        response = requests.post(APP_URL, json=payload, timeout=10)
                        
                        print(f"  📊 API Response Status: {response.status_code}")
                        
                        if response.status_code == 201:
                            response_data = response.json()
                            print(f"  ✅ Successfully flagged (ID: {response_data.get('id', 'unknown')})")
                            flagged_count += 1
                        else:
                            print(f"  ❌ Failed to flag: HTTP {response.status_code}")
                            try:
                                error_data = response.json()
                                print(f"  📋 Error details: {error_data}")
                            except:
                                print(f"  📋 Error response: {response.text}")
                                
                    except requests.exceptions.RequestException as req_error:
                        print(f"  🔌 Request error: {req_error}")
                    except Exception as api_error:
                        print(f"  ⚠️ API error: {api_error}")
                        
                else:
                    print(f"  ℹ️  Not flagged (below thresholds)")
                
                # Small delay to be nice to the API
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Error analyzing tweet: {e}")
                import traceback
                print(f"  📋 Full error: {traceback.format_exc()}")
                continue
        
        print(f"\n📊 Summary: Flagged {flagged_count} out of {len(tweets)} tweets")
        print(f"🌐 Check results at: http://localhost:5000/dashboard")
        
    except Exception as e:
        print(f"❌ Error in main process: {e}")
        import traceback
        print(f"📋 Full error: {traceback.format_exc()}")

if __name__ == "__main__":
    main()