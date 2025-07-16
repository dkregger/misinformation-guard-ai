"""
Comprehensive news monitoring for misinformation detection
Monitors news articles for specific candidates, organizations, and topics
"""

from real_news_scraper import scan_multiple_news_sites
from classifier import detect_misinformation
from monitoring_manager import MonitoringSessionManager
from misinformation_config import get_high_risk_keywords
import requests
import json
import time
from datetime import datetime

# Configuration
APP_URL = "http://localhost:5000/add"

def flag_article_if_needed(article, analysis, session_manager=None):
    """
    Determine if article should be flagged and send to API
    """
    should_flag = False
    flag_reasons = []
    
    # Only flag if content classification indicates problems
    content_is_problematic = (
        analysis["label"] in ["propaganda", "toxic"] and analysis["confidence"] > 0.4
    )
    
    # Flag based on content classification
    if analysis["label"] == "propaganda" and analysis["confidence"] > 0.4:
        should_flag = True
        flag_reasons.append(f"Propaganda content (confidence: {analysis['confidence']:.2f})")
    elif analysis["label"] == "toxic" and analysis["confidence"] > 0.4:
        should_flag = True
        flag_reasons.append(f"Toxic content (confidence: {analysis['confidence']:.2f})")
    
    # Only flag for keywords if content is already problematic OR high-risk keywords present
    high_risk_keywords = get_high_risk_keywords()
    high_risk_matches = [kw for kw in analysis["matching_keywords"] 
                        if any(risk_kw.lower() in kw.lower() for risk_kw in high_risk_keywords)]
    
    if high_risk_matches and len(high_risk_matches) >= 2:
        should_flag = True
        flag_reasons.append(f"Multiple high-risk keywords: {high_risk_matches}")
    elif content_is_problematic and analysis["keyword_count"] >= 2:
        # Only flag for multiple keywords if content is already problematic
        flag_reasons.append(f"Multiple target keywords: {analysis['matching_keywords']}")
    
    # Don't flag reliable content just because it mentions organizations in normal context
    if analysis["label"] == "reliable" and analysis["confidence"] > 0.7 and not high_risk_matches:
        should_flag = False
        flag_reasons = []
    
    # Log the analysis result if session manager available
    if session_manager:
        primary_flag_reason = flag_reasons[0] if flag_reasons else None
        session_manager.log_article_analysis(
            analysis["label"], 
            analysis["confidence"], 
            flagged=should_flag,
            flag_reason=primary_flag_reason
        )
    
    if should_flag:
        session_id = session_manager.get_session_id() if session_manager else None
        
        payload = {
            "content": f"{article['title']}\n\n{article['text'][:500]}...",  # Truncate long articles
            "confidence": analysis["confidence"],
            "label": analysis["label"],
            "url": article["url"],  # Make sure URL is included
            "source": "news",
            "username": article.get("source", "Unknown"),
            "is_bot": False,  # News articles aren't from bots
            "bot_confidence": 0.0,
            "bot_reasons": json.dumps([]),
            "session_id": session_id  # Link to monitoring session
        }
        
        try:
            response = requests.post(APP_URL, json=payload, timeout=10)
            if response.status_code == 201:
                return True, flag_reasons
            else:
                error_msg = f"Failed to flag article: {response.status_code}"
                if session_manager:
                    session_manager.log_error(error_msg, f"Article: {article['title']}")
                else:
                    print(error_msg)
                return False, flag_reasons
        except Exception as e:
            error_msg = f"Error flagging article: {e}"
            if session_manager:
                session_manager.log_error(error_msg, f"Article: {article['title']}")
            else:
                print(error_msg)
            return False, flag_reasons
    
    return False, []

def monitor_news_for_misinformation(use_real_data=False):
    """
    Main function to monitor news for misinformation
    """
    print("🗞️  Starting News Misinformation Monitoring")
    print("=" * 50)
    
    # Start monitoring session
    session_manager = None
    try:
        session_manager = MonitoringSessionManager("news", use_real_data=use_real_data)
        session_id = session_manager.start_session()
        
        if not session_id:
            print("⚠️ Failed to start monitoring session, continuing without tracking...")
            session_manager = None
    except Exception as e:
        print(f"⚠️ Error starting session manager: {e}, continuing without tracking...")
        session_manager = None
    
    articles = []
    
    if use_real_data:
        print("Using REAL news data from live websites")
        print("This may take several minutes...")
        
        # Define target keywords for real scraping
        target_keywords = [
            "Trump", "Biden", "election", "fraud", "vaccine", "COVID", 
            "CDC", "conspiracy", "deep state", "QAnon"
        ]
        
        print(f"Target keywords: {', '.join(target_keywords)}")
        print()
        
        # Get real articles from news sites
        try:
            articles = scan_multiple_news_sites(
                site_categories=["reliable"],  # Just reliable sources for PoC
                target_keywords=target_keywords,
                max_total_articles=5  # Limit to 5 articles total
            )
            
            if not articles:
                print("No articles found with target keywords. Using mock data as fallback.")
                use_real_data = False
        except Exception as e:
            error_msg = f"Error during news scraping: {e}"
            if session_manager:
                session_manager.log_error(error_msg, "Real data collection")
            print(f"❌ {error_msg}")
            print("Falling back to mock data...")
            use_real_data = False
    
    if not use_real_data:
        print("Using mock data for testing")
        
        # Fallback to mock data
        try:
            from simple_news_scraper import create_mock_articles_with_content
            articles = create_mock_articles_with_content()
        except Exception as e:
            print(f"❌ Error loading mock data: {e}")
            articles = []
    
    if not articles:
        print("❌ No articles to analyze")
        if session_manager:
            session_manager.end_session()
        return
    
    flagged_count = 0
    total_articles = len(articles)
    
    print(f"📊 Analyzing {total_articles} articles...")
    print()
    
    for i, article in enumerate(articles, 1):
        print(f"📰 Analyzing article {i}/{total_articles}")
        print(f"Title: {article['title']}")
        print(f"Source: {article.get('source', 'Unknown')}")
        
        try:
            # Use the risk assessment that's already calculated
            risk_assessment = article.get('risk_assessment', {})
            analysis = {
                "label": "unknown",
                "confidence": 0.0,
                "matching_keywords": risk_assessment.get('matching_keywords', []),
                "keyword_count": len(risk_assessment.get('matching_keywords', []))
            }
            
            # Run content through classifier (with length limit)
            full_text = f"{article['title']} {article['text'][:800]}"  # Limit text length
            label, confidence = detect_misinformation(full_text)
            analysis["label"] = label
            analysis["confidence"] = confidence
            
            print(f"  Classification: {analysis['label']} (confidence: {analysis['confidence']:.2f})")
            print(f"  Keywords found: {analysis['matching_keywords']}")
            print(f"  URL: {article['url']}")
            
            # Flag if necessary
            was_flagged, flag_reasons = flag_article_if_needed(article, analysis, session_manager)
            
            if was_flagged:
                print(f"  🚩 FLAGGED: {'; '.join(flag_reasons)}")
                print(f"  📎 Article URL: {article['url']}")
                flagged_count += 1
            else:
                print(f"  ✅ Not flagged (reliable content or insufficient risk indicators)")
            
            print()
            time.sleep(0.5)  # Small delay between articles
            
        except Exception as e:
            error_msg = f"Error analyzing article: {e}"
            if session_manager:
                session_manager.log_error(error_msg, f"Article: {article.get('title', 'Unknown')}")
            print(f"  ❌ {error_msg}")
            continue
    
    # End monitoring session and show summary
    if session_manager:
        try:
            session_manager.end_session()
        except Exception as e:
            print(f"⚠️ Error ending session: {e}")
            # Print basic summary as fallback
            print_basic_summary(total_articles, flagged_count)
    else:
        # Print basic summary without session tracking
        print_basic_summary(total_articles, flagged_count)

def print_basic_summary(total_articles, flagged_count):
    """Print basic summary when session tracking isn't available"""
    print(f"📊 Monitoring Complete")
    print(f"Total articles analyzed: {total_articles}")
    print(f"Articles flagged: {flagged_count}")
    if total_articles > 0:
        print(f"Flag rate: {(flagged_count/total_articles)*100:.1f}%")
    print()
    print("🌐 Check results at: http://localhost:5000/flagged")
    print("📈 View statistics at: http://localhost:5000/stats")
    print("📊 View monitoring stats at: http://localhost:5000/monitoring/stats/summary")

if __name__ == "__main__":
    # Test the news monitor
    monitor_news_for_misinformation(use_real_data=True)