"""
Monitoring session manager for tracking performance metrics.

This module manages monitoring sessions, tracking performance statistics,
error rates, and processing metrics for the misinformation detection system.
"""

import json
import time
import requests
from datetime import datetime
from collections import defaultdict, Counter

class MonitoringSessionManager:
    """
    Manages a single monitoring session with comprehensive performance tracking.
    
    Tracks article processing, success rates, classifications, errors, and
    source performance for later analysis and dashboard display.
    """
    
    def __init__(self, session_type, use_real_data=False, api_base_url="http://localhost:5000"):
        """
        Initialize a new monitoring session manager.
        
        Args:
            session_type (str): Type of monitoring ("twitter", "news", or "both")
            use_real_data (bool): Whether using real data vs mock data
            api_base_url (str): Base URL for the API endpoints
        """
        self.session_type = session_type
        self.use_real_data = use_real_data
        self.api_base_url = api_base_url
        self.session_id = None
        
        # Time tracking
        self.start_time = None
        self.end_time = None
        
        # Content processing counters
        self.articles_attempted = 0
        self.articles_successfully_scraped = 0
        self.articles_analyzed = 0
        self.articles_flagged = 0
        
        # Source performance tracking (domain -> count)
        self.sources_attempted = defaultdict(int)
        self.sources_successful = defaultdict(int)
        
        # Classification results tracking
        self.classification_counts = Counter()  # label -> count
        self.flag_reasons = Counter()           # reason -> count
        
        # Error tracking
        self.errors = []
        
    def start_session(self):
        """
        Start a new monitoring session by creating a database record.
        
        Returns:
            int: Session ID if successful, None if failed
        """
        self.start_time = datetime.utcnow()
        
        try:
            # Create session record via API
            payload = {
                "session_type": self.session_type,
                "use_real_data": self.use_real_data
            }
            
            response = requests.post(f"{self.api_base_url}/monitoring/sessions", json=payload)
            if response.status_code == 201:
                self.session_id = response.json()["session_id"]
                print(f"📊 Started monitoring session {self.session_id} ({self.session_type})")
                return self.session_id
            else:
                print(f"Failed to create monitoring session: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error starting monitoring session: {e}")
            return None
    
    def log_article_attempt(self, source_url):
        """
        Log an attempt to scrape an article from a source.
        
        Args:
            source_url (str): URL of the source being scraped
        """
        self.articles_attempted += 1
        
        # Extract domain from URL for source tracking
        from urllib.parse import urlparse
        domain = urlparse(source_url).netloc
        self.sources_attempted[domain] += 1
    
    def log_article_success(self, source_url, article_data):
        """
        Log a successful article scrape.
        
        Args:
            source_url (str): URL that was successfully scraped
            article_data (dict): The scraped article data
        """
        self.articles_successfully_scraped += 1
        
        # Track successful source
        from urllib.parse import urlparse
        domain = urlparse(source_url).netloc
        self.sources_successful[domain] += 1
    
    def log_article_analysis(self, classification_label, confidence, flagged=False, flag_reason=None):
        """
        Log the results of analyzing an article.
        
        Args:
            classification_label (str): AI classification result ("propaganda", "toxic", "reliable")
            confidence (float): Classification confidence score
            flagged (bool): Whether the article was flagged as problematic
            flag_reason (str): Reason why article was flagged (if applicable)
        """
        self.articles_analyzed += 1
        self.classification_counts[classification_label] += 1
        
        if flagged:
            self.articles_flagged += 1
            if flag_reason:
                self.flag_reasons[flag_reason] += 1
    
    def log_error(self, error_message, context=""):
        """
        Log an error that occurred during monitoring.
        
        Args:
            error_message (str): Description of the error
            context (str): Additional context about when/where error occurred
        """
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": str(error_message),
            "context": context
        }
        self.errors.append(error_entry)
        print(f"⚠️ Error logged: {error_message}")
    
    def end_session(self):
        """
        End the monitoring session and save final metrics to database.
        
        Calculates derived metrics like success rates and duration,
        then updates the database record with final results.
        """
        self.end_time = datetime.utcnow()
        
        if not self.session_id:
            print("No session to end - session creation may have failed")
            return
        
        # Calculate derived metrics
        duration = (self.end_time - self.start_time).total_seconds()
        scraping_success_rate = (
            (self.articles_successfully_scraped / self.articles_attempted * 100) 
            if self.articles_attempted > 0 else 0
        )
        flagging_rate = (
            (self.articles_flagged / self.articles_analyzed * 100) 
            if self.articles_analyzed > 0 else 0
        )
        
        # Prepare update data for API
        update_data = {
            "end_time": self.end_time.isoformat(),
            "duration_seconds": duration,
            "total_articles_attempted": self.articles_attempted,
            "total_articles_successfully_scraped": self.articles_successfully_scraped,
            "total_articles_analyzed": self.articles_analyzed,
            "total_flagged": self.articles_flagged,
            "scraping_success_rate": scraping_success_rate,
            "flagging_rate": flagging_rate,
            "sources_attempted": json.dumps(dict(self.sources_attempted)),
            "sources_successful": json.dumps(dict(self.sources_successful)),
            "propaganda_count": self.classification_counts.get('propaganda', 0),
            "toxic_count": self.classification_counts.get('toxic', 0),
            "bot_count": sum(1 for reason in self.flag_reasons if 'bot' in reason.lower()),
            "reliable_count": self.classification_counts.get('reliable', 0),
            "flag_reasons": json.dumps(dict(self.flag_reasons)),
            "error_count": len(self.errors),
            "error_details": json.dumps(self.errors)
        }
        
        try:
            # Update session record via API
            response = requests.put(
                f"{self.api_base_url}/monitoring/sessions/{self.session_id}", 
                json=update_data
            )
            if response.status_code == 200:
                print(f"✅ Monitoring session {self.session_id} completed successfully")
                self.print_session_summary()
            else:
                print(f"Failed to update monitoring session: {response.status_code}")
                # Still print summary even if database update failed
                self.print_session_summary()
                
        except Exception as e:
            print(f"Error ending monitoring session: {e}")
            # Still print summary even if database update failed
            self.print_session_summary()
    
    def print_session_summary(self):
        """
        Print a comprehensive summary of the monitoring session performance.
        
        Displays processing statistics, performance metrics, source breakdown,
        classification results, and any errors encountered.
        """
        if not self.end_time:
            self.end_time = datetime.utcnow()
            
        duration = (self.end_time - self.start_time).total_seconds()
        
        print(f"\n📊 MONITORING SESSION SUMMARY")
        print(f"=" * 50)
        print(f"Session ID: {self.session_id}")
        print(f"Type: {self.session_type}")
        print(f"Duration: {duration:.1f} seconds")
        print(f"Data Source: {'Real' if self.use_real_data else 'Mock'}")
        print()
        
        print(f"📰 ARTICLE PROCESSING:")
        print(f"  Attempted: {self.articles_attempted}")
        print(f"  Successfully scraped: {self.articles_successfully_scraped}")
        print(f"  Analyzed: {self.articles_analyzed}")
        print(f"  Flagged: {self.articles_flagged}")
        print()
        
        print(f"📈 PERFORMANCE METRICS:")
        scraping_success = (
            (self.articles_successfully_scraped / self.articles_attempted * 100) 
            if self.articles_attempted > 0 else 0
        )
        flagging_rate = (
            (self.articles_flagged / self.articles_analyzed * 100) 
            if self.articles_analyzed > 0 else 0
        )
        print(f"  Scraping success rate: {scraping_success:.1f}%")
        print(f"  Flagging rate: {flagging_rate:.1f}%")
        print()
        
        # Source performance breakdown
        if self.sources_successful:
            print(f"🌐 SOURCES:")
            for source, count in self.sources_successful.items():
                attempted = self.sources_attempted.get(source, 0)
                success_rate = (count / attempted * 100) if attempted > 0 else 0
                print(f"  {source}: {count}/{attempted} ({success_rate:.1f}%)")
            print()
        
        # Classification breakdown
        if self.classification_counts:
            print(f"🏷️ CLASSIFICATIONS:")
            for label, count in self.classification_counts.items():
                print(f"  {label}: {count}")
            print()
        
        # Flag reasons breakdown
        if self.flag_reasons:
            print(f"🚩 FLAG REASONS:")
            for reason, count in self.flag_reasons.items():
                print(f"  {reason}: {count}")
            print()
        
        # Error summary
        if self.errors:
            print(f"⚠️ ERRORS: {len(self.errors)} total")
            # Show last 3 errors as examples
            for error in self.errors[-3:]:
                print(f"  {error['message']}")
            print()

    def get_session_id(self):
        """
        Get the current session ID for linking flagged posts.
        
        Returns:
            int: Session ID, or None if session not started
        """
        return self.session_id

# Example usage and testing
if __name__ == "__main__":
    print("Testing Monitoring Session Manager")
    print("=" * 40)
    
    # Create and test a monitoring session
    manager = MonitoringSessionManager("test", use_real_data=False)
    
    session_id = manager.start_session()
    if session_id:
        # Simulate some monitoring activity
        print("\nSimulating monitoring activity...")
        
        manager.log_article_attempt("https://example.com/article1")
        manager.log_article_success("https://example.com/article1", {"title": "Test Article 1"})
        manager.log_article_analysis("propaganda", 0.85, flagged=True, flag_reason="High-risk keywords")
        
        manager.log_article_attempt("https://example.com/article2") 
        manager.log_article_success("https://example.com/article2", {"title": "Test Article 2"})
        manager.log_article_analysis("reliable", 0.2, flagged=False)
        
        manager.log_error("Test error for demonstration", "Testing error logging functionality")
        
        # Simulate processing time
        time.sleep(1)
        
        # End session and show summary
        manager.end_session()
    else:
        print("Failed to start monitoring session")