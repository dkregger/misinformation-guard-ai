import snscrape.modules.twitter as sntwitter
import datetime

def scrape_tweets(keyword, since_days=1, max_results=20):
    since_date = (datetime.datetime.utcnow() - datetime.timedelta(days=since_days)).strftime('%Y-%m-%d')
    query = f'{keyword} since:{since_date}'
    tweets = []

    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i >= max_results:
            break
        tweets.append({
            'user': tweet.user.username,
            'content': tweet.content,
            'date': tweet.date.isoformat(),
            'url': tweet.url
        })
    
    return tweets