from classifier import detect_misinformation
import requests
import time
import datetime

# Mock function for testing (since snscrape has issues)
def scrape_tweets(keyword, since_days=1, max_results=20):
    """Mock function that creates test tweets for development"""
    print(f"🧪 Using mock data for testing (keyword: {keyword})")
    return [
        {
            'user': 'propaganda_user',
            'content': f'BREAKING SHOCKING NEWS about {keyword}! The mainstream media lies and they don\'t want you to know the truth! Share before they delete this! Wake up!',
            'date': datetime.datetime.utcnow().isoformat(),
            'url': 'https://twitter.com/test/status/1'
        },
        {
            'user': 'reliable_user', 
            'content': f'According to experts and peer-reviewed research, here are the verified facts about {keyword} from credible government sources.',
            'date': datetime.datetime.utcnow().isoformat(),
            'url': 'https://twitter.com/test/status/2'
        },
        {
            'user': 'toxic_user',
            'content': f'These idiots supporting {keyword} are stupid morons who should shut up and die. I hate all of them and they are worthless trash!',
            'date': datetime.datetime.utcnow().isoformat(),
            'url': 'https://twitter.com/test/status/3'
        },
        {
            'user': 'conspiracy_user',
            'content': f'The deep state conspiracy around {keyword} is being covered up! Hidden truth revealed! Secret agenda exposed! Must share urgently!',
            'date': datetime.datetime.utcnow().isoformat(),
            'url': 'https://twitter.com/test/status/4'
        },
        {
            'user': 'neutral_user',
            'content': f'Just heard some news about {keyword}. Interesting developments happening lately.',
            'date': datetime.datetime.utcnow().isoformat(),
            'url': 'https://twitter.com/test/status/5'
        }
    ]

# Replace with your Heroku app URL
APP_URL = "http://localhost:5000/add"  # Using localhost for testing
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
                label, score = detect_misinformation(tweet['content'])
                print(f"  Label: {label}, Score: {score:.3f}")

                # Flag both toxic content and propaganda
                should_flag = False
                if label.lower() == "propaganda" and score > 0.5:
                    should_flag = True
                    print(f"  🚩 Flagging as PROPAGANDA (confidence: {score:.3f})")
                elif label.lower() == "toxic" and score > 0.3:  # Lower threshold for toxic
                    should_flag = True  
                    print(f"  ☠️ Flagging as TOXIC (confidence: {score:.3f})")
                
                if should_flag:
                    payload = {
                        "content": tweet['content'],
                        "confidence": score,
                        "label": label,
                        "url": tweet['url'],
                        "source": "twitter"
                    }
                    
                    print(f"  🚩 Flagging post with confidence {score:.3f}")
                    
                    # Send to our API
                    response = requests.post(APP_URL, json=payload, timeout=10)
                    
                    if response.status_code == 201:
                        print("  ✅ Successfully flagged")
                        flagged_count += 1
                    else:
                        print(f"  ❌ Failed to flag: {response.status_code}")
                else:
                    print(f"  ℹ️  Not flagged (confidence too low or not propaganda)")
                
                # Small delay to be nice to the API
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Error analyzing tweet: {e}")
                continue
        
        print(f"\n📊 Summary: Flagged {flagged_count} out of {len(tweets)} tweets")
        print(f"🌐 Check results at: http://localhost:5000/flagged")
        
    except Exception as e:
        print(f"❌ Error in main process: {e}")

if __name__ == "__main__":
    main()