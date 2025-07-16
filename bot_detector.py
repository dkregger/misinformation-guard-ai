"""
Bot detection system for identifying automated social media accounts.

This module analyzes user account characteristics to determine if an account
is likely operated by a bot rather than a human user.
"""

import re
from datetime import datetime, timedelta

def detect_bot_likelihood(user_data):
    """
    Main function to analyze user data and determine bot likelihood.
    
    Combines multiple analysis methods to calculate an overall bot score
    based on username patterns, profile characteristics, activity patterns,
    and network metrics.
    
    Args:
        user_data (dict): Dictionary containing user account information:
            - username: Account username
            - display_name: Display name shown on profile
            - bio: Profile biography/description
            - follower_count: Number of followers
            - following_count: Number of accounts followed
            - tweet_count: Total number of posts/tweets
            - account_age_days: Age of account in days
            - profile_image_url: URL of profile image (optional)
            - verified: Whether account is verified (optional)
    
    Returns:
        tuple: (is_bot, confidence_score, reasons)
            - is_bot: Boolean indicating if account is likely a bot
            - confidence_score: Float between 0.0-1.0 indicating confidence
            - reasons: List of specific indicators that triggered detection
    """
    bot_score = 0.0
    reasons = []
    
    # Run all analysis methods
    username_score, username_reasons = analyze_username(user_data.get('username', ''))
    bot_score += username_score
    reasons.extend(username_reasons)
    
    profile_score, profile_reasons = analyze_profile(user_data)
    bot_score += profile_score
    reasons.extend(profile_reasons)
    
    activity_score, activity_reasons = analyze_activity_patterns(user_data)
    bot_score += activity_score
    reasons.extend(activity_reasons)
    
    network_score, network_reasons = analyze_network_metrics(user_data)
    bot_score += network_score
    reasons.extend(network_reasons)
    
    # Normalize score to 0-1 range
    final_score = min(1.0, max(0.0, bot_score))
    
    # Determine if likely bot (threshold: 0.6)
    is_bot = final_score >= 0.6
    
    return is_bot, final_score, reasons

def analyze_username(username):
    """
    Analyze username patterns commonly found in bot accounts.
    
    Bots often use automatically generated usernames with predictable
    patterns like names followed by long number sequences.
    
    Args:
        username (str): Username to analyze
        
    Returns:
        tuple: (score, reasons) where score is 0.0-1.0 and reasons is list of strings
    """
    score = 0.0
    reasons = []
    
    if not username:
        return score, reasons
    
    # Pattern 1: Long numeric sequences (4+ consecutive digits)
    if re.search(r'\d{4,}', username):
        score += 0.3
        reasons.append("Username contains long numeric sequence")
    
    # Pattern 2: Name followed by many numbers (common bot pattern)
    if re.search(r'^[a-zA-Z]+\d{4,}$', username):
        score += 0.25
        reasons.append("Username follows name+numbers pattern")
    
    # Pattern 3: Random consonant clusters (unpronounceable combinations)
    consonant_clusters = re.findall(r'[bcdfghjklmnpqrstvwxyz]{4,}', username.lower())
    if consonant_clusters:
        score += 0.2
        reasons.append("Username has unusual consonant clusters")
    
    # Pattern 4: Very long usernames without separators
    if len(username) > 15 and not re.search(r'[_\-]', username):
        score += 0.15
        reasons.append("Username is unusually long without separators")
    
    return score, reasons

def analyze_profile(user_data):
    """
    Analyze profile information for bot indicators.
    
    Bots often have incomplete profiles, generic descriptions,
    or missing profile images.
    
    Args:
        user_data (dict): User account data
        
    Returns:
        tuple: (score, reasons)
    """
    score = 0.0
    reasons = []
    
    # Extract profile fields
    bio = user_data.get('bio', '').strip()
    display_name = user_data.get('display_name', '').strip()
    username = user_data.get('username', '')
    
    # Missing profile bio
    if not bio:
        score += 0.2
        reasons.append("Empty profile bio")
    
    # Missing or generic display name
    if not display_name or display_name == username:
        score += 0.15
        reasons.append("Missing or generic display name")
    
    # Generic bio phrases commonly used by bots
    if bio:
        generic_phrases = [
            'love life', 'living life', 'enjoying life', 'follow me',
            'dm for promo', 'crypto enthusiast', 'investor', 'entrepreneur'
        ]
        for phrase in generic_phrases:
            if phrase.lower() in bio.lower():
                score += 0.1
                reasons.append(f"Generic bio phrase: '{phrase}'")
                break  # Only count one generic phrase
    
    # Profile image analysis
    profile_image = user_data.get('profile_image_url', '')
    if not profile_image or 'default' in profile_image.lower():
        score += 0.1
        reasons.append("Default or missing profile image")
    
    # Verified accounts are less likely to be bots
    if user_data.get('verified', False):
        score -= 0.3  # Reduce bot score for verified accounts
        reasons.append("Verified account (reduces bot likelihood)")
    
    return score, reasons

def analyze_activity_patterns(user_data):
    """
    Analyze posting frequency and activity patterns.
    
    Bots often have extremely high posting rates or unusual
    activity patterns that humans wouldn't maintain.
    
    Args:
        user_data (dict): User account data
        
    Returns:
        tuple: (score, reasons)
    """
    score = 0.0
    reasons = []
    
    tweet_count = user_data.get('tweet_count', 0)
    account_age_days = user_data.get('account_age_days', 1)
    
    # Calculate daily posting rate
    if account_age_days > 0:
        tweets_per_day = tweet_count / account_age_days
        
        # Extremely high posting frequency (inhuman levels)
        if tweets_per_day > 50:
            score += 0.4
            reasons.append(f"Extremely high posting rate: {tweets_per_day:.1f} tweets/day")
        elif tweets_per_day > 25:
            score += 0.2
            reasons.append(f"High posting rate: {tweets_per_day:.1f} tweets/day")
    
    # New accounts with lots of activity (possible bot farm activation)
    if account_age_days < 30 and tweet_count > 100:
        score += 0.3
        reasons.append("New account with high activity")
    
    # Dormant accounts (possible future bot activation)
    if tweet_count == 0:
        score += 0.1
        reasons.append("No tweets posted")
    
    return score, reasons

def analyze_network_metrics(user_data):
    """
    Analyze follower/following patterns for bot indicators.
    
    Bots often have unusual follow ratios or participate in
    follow-for-follow schemes to inflate their numbers.
    
    Args:
        user_data (dict): User account data
        
    Returns:
        tuple: (score, reasons)
    """
    score = 0.0
    reasons = []
    
    followers = user_data.get('follower_count', 0)
    following = user_data.get('following_count', 0)
    
    # Calculate follow ratio (following/followers)
    if followers > 0:
        follow_ratio = following / followers
        
        # Extremely high follow ratio (following way more than followers)
        if follow_ratio > 10:
            score += 0.3
            reasons.append(f"High follow ratio: following {following}, followers {followers}")
        elif follow_ratio > 5:
            score += 0.2
            reasons.append(f"Elevated follow ratio: {follow_ratio:.1f}")
    
    # Following excessive accounts (possible follow-for-follow bot)
    if following > 5000:
        score += 0.2
        reasons.append(f"Following excessive accounts: {following}")
    
    # Very low followers but high following count
    if followers < 50 and following > 1000:
        score += 0.25
        reasons.append("Low followers but high following count")
    
    # Suspicious round numbers (some bots have artificially inflated counts)
    if followers > 0 and followers % 1000 == 0:
        score += 0.1
        reasons.append("Suspiciously round follower count")
    
    return score, reasons

def create_mock_user_data(username, is_bot_example=False):
    """
    Create mock user data for testing bot detection.
    
    Args:
        username (str): Base username to use
        is_bot_example (bool): Whether to create bot-like or human-like data
        
    Returns:
        dict: Mock user data for testing
    """
    if is_bot_example:
        # Create obviously bot-like characteristics
        return {
            'username': f'user{12345}crypto',
            'display_name': f'User{12345}',
            'bio': 'Crypto enthusiast. Follow me for tips! DM for promo.',
            'follower_count': 150,
            'following_count': 4800,  # Very high follow ratio
            'tweet_count': 2000,      # High activity
            'account_age_days': 45,   # New account
            'profile_image_url': 'default_profile.jpg',
            'verified': False
        }
    else:
        # Create human-like characteristics
        return {
            'username': 'john_doe_writer',
            'display_name': 'John Doe',
            'bio': 'Journalist at Local News. Reporting on politics and community events since 2015.',
            'follower_count': 1200,
            'following_count': 400,   # Normal follow ratio
            'tweet_count': 800,
            'account_age_days': 1500, # Older account
            'profile_image_url': 'custom_profile.jpg',
            'verified': True
        }

# Test and example usage
if __name__ == "__main__":
    print("Testing Bot Detection System")
    print("=" * 40)
    
    # Test with bot-like account
    print("\n🤖 Testing Bot-like Account:")
    bot_user = create_mock_user_data("test", is_bot_example=True)
    is_bot, score, reasons = detect_bot_likelihood(bot_user)
    
    print(f"Username: {bot_user['username']}")
    print(f"Bot Likelihood: {score:.2f} ({'BOT' if is_bot else 'HUMAN'})")
    print("Detection Reasons:")
    for reason in reasons:
        print(f"  - {reason}")
    
    # Test with human-like account  
    print(f"\n👤 Testing Human-like Account:")
    human_user = create_mock_user_data("test", is_bot_example=False)
    is_bot, score, reasons = detect_bot_likelihood(human_user)
    
    print(f"Username: {human_user['username']}")
    print(f"Bot Likelihood: {score:.2f} ({'BOT' if is_bot else 'HUMAN'})")
    print("Detection Reasons:")
    for reason in reasons:
        print(f"  - {reason}")