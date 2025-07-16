from newspaper import Article
import requests
from misinformation_config import (
    get_all_monitoring_keywords, 
    get_keyword_risk_level,
    is_questionable_source,
    is_reliable_source
)
import time

def scrape_article(url):
    """Enhanced article scraping with misinformation risk assessment"""
    article = Article(url)

    try:
        article.download()
        article.parse()
        
        # Get the full text for analysis
        full_text = f"{article.title} {article.text}"
        
        # Assess misinformation risk based on keywords
        risk_level, matching_keywords, risk_score = get_keyword_risk_level(full_text)
        
        # Check source reliability
        source_type = "unknown"
        if is_questionable_source(url):
            source_type = "questionable"
            risk_score += 0.3  # Increase risk for questionable sources
        elif is_reliable_source(url):
            source_type = "reliable"
            risk_score = max(0.0, risk_score - 0.2)  # Decrease risk for reliable sources
        
        return {
            "title": article.title,
            "text": article.text,
            "authors": article.authors,
            "published_date": str(article.publish_date),
            "top_image": article.top_image,
            "url": url,
            "risk_assessment": {
                "risk_level": risk_level,
                "risk_score": min(1.0, risk_score),
                "matching_keywords": matching_keywords,
                "source_type": source_type
            }
        }
    except Exception as e:
        print(f"Failed to scrape article at {url}: {e}")
        return None

def search_news_for_keywords(keywords, max_articles_per_keyword=5):
    """
    Search for news articles containing specific keywords
    This is a mock function - in production you'd use Google News API, NewsAPI, etc.
    """
    print(f"🔍 Searching for articles about: {', '.join(keywords[:3])}...")
    
    # Mock news URLs for testing - replace with real news API
    mock_articles = [
        {
            "url": "https://example.com/news/election-fraud-claims-2024",
            "title": f"Investigation into {keywords[0]} election fraud claims continues",
            "description": f"New developments in ongoing investigation of alleged election fraud involving {keywords[0]}",
            "source": "Mock News Network"
        },
        {
            "url": "https://example.com/news/vaccine-conspiracy-theory", 
            "title": f"Health officials debunk {keywords[0]} vaccine conspiracy theories",
            "description": f"Medical experts respond to misinformation about {keywords[0]} and vaccine safety",
            "source": "Health News Today"
        },
        {
            "url": "https://example.com/news/political-update",
            "title": f"{keywords[0]} announces new policy initiative", 
            "description": f"Latest policy announcement from {keywords[0]} draws mixed reactions",
            "source": "Political Wire"
        }
    ]
    
    return mock_articles

def scan_articles_for_misinformation(article_urls, keyword_filter=None):
    """
    Scan a list of article URLs for potential misinformation
    """
    flagged_articles = []
    
    for url in article_urls:
        print(f"📰 Scanning: {url}")
        
        # Add delay to be respectful to websites
        time.sleep(1)
        
        article_data = scrape_article(url)
        
        if article_data:
            risk_assessment = article_data["risk_assessment"]
            
            # Flag articles based on risk level and keywords
            should_flag = False
            flag_reason = ""
            
            if risk_assessment["risk_level"] in ["HIGH", "MEDIUM"]:
                should_flag = True
                flag_reason = f"High misinformation risk ({risk_assessment['risk_level']})"
            elif risk_assessment["source_type"] == "questionable":
                should_flag = True
                flag_reason = "Questionable news source"
            elif len(risk_assessment["matching_keywords"]) >= 2:
                should_flag = True
                flag_reason = "Multiple misinformation keywords detected"
            
            # Apply keyword filter if specified
            if keyword_filter:
                article_text_lower = f"{article_data['title']} {article_data['text']}".lower()
                if not any(keyword.lower() in article_text_lower for keyword in keyword_filter):
                    should_flag = False
                    flag_reason = "Filtered out - doesn't match target keywords"
            
            if should_flag:
                article_data["flag_reason"] = flag_reason
                flagged_articles.append(article_data)
                print(f"  🚩 FLAGGED: {flag_reason}")
                print(f"  Keywords: {risk_assessment['matching_keywords']}")
            else:
                print(f"  ✅ Not flagged (risk: {risk_assessment['risk_level']})")
    
    return flagged_articles

# Example usage for testing
if __name__ == "__main__":
    print("Testing Enhanced News Scraper")
    print("=" * 40)
    
    # Test with sample URLs (replace with real URLs)
    test_urls = [
        "https://example.com/election-fraud-story",
        "https://example.com/vaccine-misinformation", 
        "https://example.com/regular-news-story"
    ]
    
    # Keywords to focus on
    target_keywords = ["election fraud", "Donald Trump", "vaccine safety"]
    
    flagged = scan_articles_for_misinformation(test_urls, keyword_filter=target_keywords)
    
    print(f"\n📊 Results: {len(flagged)} articles flagged out of {len(test_urls)} scanned")
    for article in flagged:
        print(f"  - {article['title']}")
        print(f"    Reason: {article['flag_reason']}")