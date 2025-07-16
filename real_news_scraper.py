"""
Real news scraper targeting specific news websites
Focuses on sites likely to contain our target keywords
"""

import requests
from bs4 import BeautifulSoup
from newspaper import Article
from misinformation_config import (
    get_keyword_risk_level,
    is_questionable_source,
    is_reliable_source
)
import time
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse

# Target news sites with different reliability levels (removed Reuters due to blocking)
TARGET_SITES = {
    "reliable": [
        "https://apnews.com", 
        "https://www.bbc.com/news",
        "https://www.npr.org",
        "https://www.pbs.org/newshour"
    ],
    "mainstream": [
        "https://www.cnn.com",
        "https://www.foxnews.com", 
        "https://www.msnbc.com",
        "https://www.cbsnews.com",
        "https://abcnews.go.com"
    ],
    "alternative": [
        "https://www.breitbart.com",
        "https://www.dailywire.com",
        "https://www.theblaze.com",
        "https://www.newsmax.com"
    ]
}

def get_article_links_from_homepage(base_url, max_links=5):
    """
    Scrape article links from a news site's homepage
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        domain = urlparse(base_url).netloc
        
        # Find article links
        links = []
        
        # Common link selectors for news sites
        link_selectors = [
            'a[href*="/article/"]',
            'a[href*="/news/"]', 
            'a[href*="/story/"]',
            'a[href*="/politics/"]',
            'a[href*="/health/"]',
            'h2 a', 'h3 a', 'h4 a',  # Headlines
            '.headline a', '.story-headline a',
            '.article-title a', '.post-title a'
        ]
        
        for selector in link_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        url = urljoin(base_url, href)
                    elif href.startswith('http'):
                        url = href
                    else:
                        continue
                    
                    # Only include links from the same domain
                    if domain in url and url not in links:
                        links.append(url)
                        
                        if len(links) >= max_links:
                            break
            
            if len(links) >= max_links:
                break
        
        return links[:max_links]
        
    except Exception as e:
        print(f"Error getting links from {base_url}: {e}")
        return []

def scrape_article_with_newspaper(url):
    """
    Use newspaper3k to scrape article content
    """
    try:
        article = Article(url)
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
            risk_score += 0.3
        elif is_reliable_source(url):
            source_type = "reliable"
            risk_score = max(0.0, risk_score - 0.2)
        
        return {
            "title": article.title or "No title",
            "text": article.text or "No content",
            "authors": article.authors,
            "published_date": str(article.publish_date) if article.publish_date else datetime.now().isoformat(),
            "top_image": article.top_image,
            "url": url,
            "source": urlparse(url).netloc,  # Extract domain as source
            "risk_assessment": {
                "risk_level": risk_level,
                "risk_score": min(1.0, risk_score),
                "matching_keywords": matching_keywords,
                "source_type": source_type
            }
        }
        
    except Exception as e:
        print(f"  Failed to scrape {url}: {e}")
        return None

def filter_articles_by_keywords(articles, target_keywords):
    """
    Filter articles to only include those containing target keywords
    """
    filtered_articles = []
    
    for article in articles:
        if article is None:
            continue
            
        full_text = f"{article['title']} {article['text']}".lower()
        
        # Check if article contains any target keywords
        contains_keywords = any(keyword.lower() in full_text for keyword in target_keywords)
        
        if contains_keywords:
            filtered_articles.append(article)
    
    return filtered_articles

def scrape_news_site(site_url, site_category, max_articles=2, target_keywords=None):
    """
    Scrape articles from a specific news site
    """
    print(f"🌐 Scraping {site_url} ({site_category}) - looking for {max_articles} articles")
    
    # Get article links from homepage
    article_links = get_article_links_from_homepage(site_url, max_articles * 3)  # Get extra in case some fail
    
    if not article_links:
        print(f"  No article links found on {site_url}")
        return []
    
    print(f"  Found {len(article_links)} potential articles")
    
    # Scrape each article
    articles = []
    for i, link in enumerate(article_links):
        if len(articles) >= max_articles:
            break
            
        print(f"  Scraping article {i+1}: {link[:80]}...")
        
        article_data = scrape_article_with_newspaper(link)
        if article_data:
            articles.append(article_data)
            
        # Shorter delay for PoC
        time.sleep(1)
    
    # Filter by keywords if specified
    if target_keywords:
        original_count = len(articles)
        articles = filter_articles_by_keywords(articles, target_keywords)
        print(f"  Filtered to {len(articles)} articles containing target keywords (from {original_count})")
    
    return articles

def scan_multiple_news_sites(site_categories=None, target_keywords=None, max_total_articles=5):
    """
    Scan multiple news sites for articles containing target keywords
    """
    if site_categories is None:
        site_categories = ["reliable"]  # Start with just reliable sources for PoC
    
    if target_keywords is None:
        target_keywords = [
            "Trump", "Biden", "election", "vaccine", "COVID", 
            "politics", "health", "government"  # Broader terms more likely to be found
        ]
    
    print(f"🔍 Scanning news sites for keywords: {', '.join(target_keywords[:5])}...")
    print(f"Target: {max_total_articles} articles total")
    print(f"Categories: {', '.join(site_categories)}")
    print()
    
    all_articles = []
    
    for category in site_categories:
        if category in TARGET_SITES and len(all_articles) < max_total_articles:
            print(f"📰 Scanning {category.upper()} news sites:")
            
            for site_url in TARGET_SITES[category]:
                if len(all_articles) >= max_total_articles:
                    break
                    
                try:
                    remaining_articles = max_total_articles - len(all_articles)
                    articles = scrape_news_site(
                        site_url, 
                        category, 
                        min(remaining_articles, 2),  # Max 2 per site
                        target_keywords
                    )
                    all_articles.extend(articles)
                    
                    print(f"  ✅ Got {len(articles)} relevant articles from {site_url}")
                    print(f"  📊 Total so far: {len(all_articles)}/{max_total_articles}")
                    
                    if len(all_articles) >= max_total_articles:
                        print(f"  🎯 Reached target of {max_total_articles} articles!")
                        break
                    
                except Exception as e:
                    print(f"  ❌ Error scraping {site_url}: {e}")
                
                # Shorter delay for PoC
                time.sleep(1)
            
            print()
    
    return all_articles[:max_total_articles]  # Ensure we don't exceed the limit

# Example usage and testing
if __name__ == "__main__":
    print("Real News Scraper - Testing")
    print("=" * 50)
    
    # Test with specific keywords that are likely to be found
    test_keywords = [
        "Trump", "Biden", "election", "vaccine", "COVID", 
        "CDC", "politics", "health", "government"
    ]
    
    # Start with reliable and mainstream sources
    test_categories = ["reliable", "mainstream"]
    
    print("Starting real news scraping...")
    print("This should take about 1-2 minutes for 5 articles")
    print()
    
    articles = scan_multiple_news_sites(
        site_categories=["reliable"],  # Just reliable sources for PoC
        target_keywords=test_keywords,
        max_total_articles=5  # Total limit of 5 articles
    )
    
    print(f"📊 RESULTS:")
    print(f"Total articles found: {len(articles)}")
    print()
    
    # Show flaggable articles
    flaggable_articles = []
    for article in articles:
        risk_assessment = article['risk_assessment']
        if (risk_assessment['risk_level'] in ['HIGH', 'MEDIUM'] or 
            len(risk_assessment['matching_keywords']) >= 2):
            flaggable_articles.append(article)
    
    print(f"Articles that would be flagged: {len(flaggable_articles)}")
    
    for article in flaggable_articles[:3]:  # Show first 3
        print(f"\n📰 {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   Risk: {article['risk_assessment']['risk_level']}")
        print(f"   Keywords: {article['risk_assessment']['matching_keywords']}")
    
    if len(flaggable_articles) > 3:
        print(f"   ... and {len(flaggable_articles) - 3} more")