"""
Comprehensive misinformation monitoring system
Monitors both social media (Twitter) and news articles for misinformation
"""

import argparse
import time
from datetime import datetime

def monitor_twitter():
    """Monitor Twitter for misinformation"""
    print("🐦 Starting Twitter Monitoring")
    print("=" * 30)
    
    # Import and run your existing Twitter scraper
    from scrape_and_flag import main as twitter_main
    twitter_main()

def monitor_news_with_options(use_mock=False):
    """Monitor news articles with option for mock or real data"""
    print("\n🗞️  Starting News Monitoring") 
    print("=" * 40)
    
    # Import and run the news monitor
    from news_monitor import monitor_news_for_misinformation
    monitor_news_for_misinformation(use_real_data=not use_mock)

def run_comprehensive_monitoring_with_options(use_mock=False):
    """Run both Twitter and news monitoring"""
    print("🚀 Starting Comprehensive Misinformation Monitoring")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'Mock data' if use_mock else 'Real data (5 articles PoC)'}")
    print()
    
    try:
        # Monitor Twitter (always uses mock data)
        monitor_twitter()
        
        print("\n" + "="*60)
        
        # Monitor News (real or mock based on option)
        monitor_news_with_options(use_mock=use_mock)
        
        print("\n" + "="*60)
        print("✅ Comprehensive monitoring completed successfully!")
        print("🌐 View all results at: http://localhost:5000/flagged")
        print("📊 Check statistics at: http://localhost:5000/stats")
        
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")

def main():
    parser = argparse.ArgumentParser(description='Misinformation Monitoring System')
    parser.add_argument('--mode', choices=['twitter', 'news', 'both'], default='both',
                       help='What to monitor: twitter, news (5 articles PoC), or both (default: both)')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously with specified interval')
    parser.add_argument('--interval', type=int, default=600, 
                       help='Interval in seconds for continuous monitoring (default: 600 for real data)')
    parser.add_argument('--mock', action='store_true',
                       help='Use mock data instead of real scraping (faster for testing)')
    
    args = parser.parse_args()
    
    if args.continuous:
        print(f"🔄 Starting continuous monitoring (every {args.interval} seconds)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                if args.mode == 'twitter':
                    monitor_twitter()
                elif args.mode == 'news':
                    monitor_news_with_options(use_mock=args.mock)
                else:
                    monitor_twitter()
                    monitor_news_with_options(use_mock=args.mock)
                
                print(f"\n💤 Waiting {args.interval} seconds until next scan...")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
    else:
        # Single run
        if args.mode == 'twitter':
            monitor_twitter()
        elif args.mode == 'news':
            monitor_news_with_options(use_mock=args.mock)
        else:
            run_comprehensive_monitoring_with_options(use_mock=args.mock)

if __name__ == "__main__":
    main()