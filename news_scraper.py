from newspaper import Article
import requests

def scrape_article(url):
    article = Article(url)

    try:
        article.download()
        article.parse()
        return {
            "title": article.title,
            "text": article.text,
            "authors": article.authors,
            "published_date": str(article.publish_date),
            "top_image": article.top_image,
            "url": url
        }
    except Exception as e:
        print(f"Failed to scrape article at {url}: {e}")
        return None