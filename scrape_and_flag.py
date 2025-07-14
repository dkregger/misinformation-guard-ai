from scraper import scrape_tweets
from classifier import detect_misinformation
import requests

# Replace with your Heroku app URL
APP_URL = "https://misinformation-guard-ai-bc66a4834fd0.herokuapp.com/"
KEYWORD = "Sherrod Brown"  # Change to your candidate or topic

def main():
    tweets = scrape_tweets(KEYWORD)

    for tweet in tweets:
        label, score = detect_misinformation(tweet['content'])

        # Only flag high-confidence propaganda
        if label.lower() == "propaganda" and score > 0.85:
            payload = {
                "content": tweet['content'],
                "confidence": score,
                "label": label,
                "url": tweet['url'],
                "source": "twitter"
            }
            print("Flagging post:", payload)
            requests.post(APP_URL, json=payload)

if __name__ == "__main__":
    main()