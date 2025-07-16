"""
Multi-layered content classifier for detecting misinformation and toxic content.

This module combines machine learning models with keyword-based detection
to identify propaganda, toxic content, and potential misinformation.
"""

from transformers import pipeline

# Global classifier - loaded once when module is imported
toxic_classifier = None

def load_toxic_classifier():
    """
    Load the toxic comment detection model.
    
    Uses a pre-trained model to detect harmful language and harassment.
    Model is loaded globally to avoid repeated loading overhead.
    """
    global toxic_classifier
    
    if toxic_classifier is None:
        try:
            print("Loading toxic comment detection model...")
            toxic_classifier = pipeline("text-classification", model="martin-ha/toxic-comment-model")
            print("✅ Toxic comment model loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading toxic model: {e}")
            print("Will use keyword-based detection as fallback")
            toxic_classifier = None

# Load the model when module is imported
load_toxic_classifier()

def detect_misinformation(text):
    """
    Main function to detect misinformation and toxic content.
    
    Combines multiple detection methods and returns the highest-confidence
    problematic result, or the most confident reliable result if no issues found.
    
    Args:
        text (str): Content to analyze
        
    Returns:
        tuple: (label, confidence_score)
            - label: "propaganda", "toxic", or "reliable"
            - confidence_score: Float between 0.0 and 1.0
    """
    # Run all detection methods
    toxic_result = detect_toxic_content(text)
    propaganda_result = detect_propaganda_keywords(text)
    keyword_toxic_result = detect_toxic_keywords(text)
    
    # Debug output for development
    print(f"    Toxic model result: {toxic_result}")
    print(f"    Propaganda result: {propaganda_result}")
    print(f"    Keyword toxic result: {keyword_toxic_result}")
    
    # Collect all results
    results = [toxic_result, propaganda_result, keyword_toxic_result]
    
    # Find problematic content (not 'reliable')
    problematic_results = [r for r in results if r[0] != 'reliable']
    
    if problematic_results:
        # Return the highest confidence problematic result
        return max(problematic_results, key=lambda x: x[1])
    else:
        # Return the most confident reliable result
        return max(results, key=lambda x: x[1])

def detect_toxic_content(text):
    """
    Use machine learning model to detect toxic/harmful content.
    
    Args:
        text (str): Content to analyze (will be truncated if too long)
        
    Returns:
        tuple: (label, confidence_score)
    """
    if toxic_classifier is None:
        return 'reliable', 0.0
    
    try:
        # Truncate text to avoid model length errors (max ~400 chars for safety)
        truncated_text = text[:400] if len(text) > 400 else text
        
        result = toxic_classifier(truncated_text)[0]
        print(f"    Toxic model raw result: {result}")
        
        if result['label'] == 'TOXIC':
            confidence = float(result['score'])
            print(f"    Toxic detection: confidence={confidence:.3f}")
            return 'toxic', confidence
        else:
            confidence = float(result['score'])  # Confidence in "NOT TOXIC"
            print(f"    Non-toxic detection: confidence={confidence:.3f}")
            return 'reliable', confidence
            
    except Exception as e:
        print(f"Error in toxic classification: {e}")
        return 'reliable', 0.0

def detect_propaganda_keywords(text):
    """
    Detect propaganda and misinformation using keyword analysis.
    
    Looks for patterns commonly found in conspiracy theories,
    unverified claims, and misinformation campaigns.
    
    Args:
        text (str): Content to analyze
        
    Returns:
        tuple: (label, confidence_score)
    """
    text_lower = text.lower()
    
    # Propaganda and misinformation indicators
    propaganda_keywords = [
        # Urgency and sharing pressure
        'breaking', 'shocking', 'unverified', 'share before', 'they delete',
        'trust me', 'no sources', 'without fact-checking', 'propaganda',
        'wake up', 'they don\'t want you to know', 'mainstream media lies',
        
        # Conspiracy language
        'cover up', 'conspiracy', 'deep state', 'fake news media',
        'urgent', 'must share', 'before it\'s too late', 'exclusive leak',
        'banned', 'censored', 'hidden truth', 'secret agenda'
    ]
    
    # Reliable source indicators
    reliable_keywords = [
        'official', 'verified', 'government sources', 'credible', 
        'journalists', 'fact-checked', 'confirmed', 'peer-reviewed',
        'according to experts', 'research shows', 'study finds',
        'reuters', 'ap news', 'bbc', 'npr', 'fact check'
    ]
    
    # Strong propaganda indicators (higher weight)
    strong_propaganda = [
        'share before they delete', 'they don\'t want you to know',
        'mainstream media lies', 'wake up sheeple', 'deep state',
        'hidden truth', 'secret agenda', 'cover up'
    ]
    
    # Count keyword matches
    propaganda_count = sum(1 for keyword in propaganda_keywords if keyword in text_lower)
    reliable_count = sum(1 for keyword in reliable_keywords if keyword in text_lower)
    strong_propaganda_count = sum(1 for keyword in strong_propaganda if keyword in text_lower)
    
    # Calculate weighted scores
    propaganda_score = propaganda_count * 0.15 + strong_propaganda_count * 0.25
    reliable_score = reliable_count * 0.15
    
    # Check for suspicious text patterns
    if has_suspicious_patterns(text):
        propaganda_score += 0.2
    
    # Determine result based on scores
    if propaganda_score > reliable_score and propaganda_score > 0.3:
        confidence = min(0.95, 0.5 + propaganda_score)
        return 'propaganda', confidence
    else:
        confidence = min(0.9, 0.4 + reliable_score)
        return 'reliable', confidence

def detect_toxic_keywords(text):
    """
    Keyword-based toxic content detection as fallback/supplement to ML model.
    
    Detects hate speech, harassment, and harmful language patterns.
    
    Args:
        text (str): Content to analyze
        
    Returns:
        tuple: (label, confidence_score)
    """
    text_lower = text.lower()
    
    # Strong toxic language indicators
    toxic_keywords = [
        'idiots', 'stupid', 'morons', 'shut up', 'die', 'hate', 'kill',
        'retard', 'dumb', 'pathetic', 'worthless', 'scum', 'trash',
        'loser', 'disgusting', 'sicko', 'creep', 'freak'
    ]
    
    # Hate speech patterns (more severe)
    hate_patterns = [
        'should die', 'hate all', 'kill them', 'deserve to die',
        'are trash', 'are scum', 'piece of shit'
    ]
    
    # Count matches
    toxic_count = sum(1 for keyword in toxic_keywords if keyword in text_lower)
    hate_count = sum(1 for pattern in hate_patterns if pattern in text_lower)
    
    # Calculate total toxicity score
    total_toxic_score = toxic_count * 0.2 + hate_count * 0.4
    
    if total_toxic_score > 0.3:
        confidence = min(0.95, 0.6 + total_toxic_score)
        return 'toxic', confidence
    else:
        return 'reliable', 0.1

def has_suspicious_patterns(text):
    """
    Check for text patterns that might indicate misinformation.
    
    Looks for formatting and language patterns commonly used
    in viral misinformation posts.
    
    Args:
        text (str): Content to analyze
        
    Returns:
        bool: True if suspicious patterns found
    """
    import re
    
    text_lower = text.lower()
    
    patterns = [
        r'!{3,}',  # Multiple exclamation marks (!!!)
        r'[A-Z]{10,}',  # Long sequences of capital letters
        r'\b(urgent|breaking|shocking)\b.*\b(share|retweet)\b',  # Urgent sharing requests
        r'\b(they|government|media)\b.*\b(hide|cover|ban|delete)\b',  # Cover-up language
    ]
    
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def get_detection_summary(text):
    """
    Get detailed breakdown of all detection methods for debugging.
    
    Args:
        text (str): Content to analyze
        
    Returns:
        dict: Detailed results from all detection methods
    """
    toxic_result = detect_toxic_content(text)
    propaganda_result = detect_propaganda_keywords(text)
    
    return {
        'toxic': {
            'label': toxic_result[0],
            'confidence': toxic_result[1]
        },
        'propaganda': {
            'label': propaganda_result[0], 
            'confidence': propaganda_result[1]
        },
        'has_suspicious_patterns': has_suspicious_patterns(text)
    }

# Example usage and testing
if __name__ == "__main__":
    print("Testing Content Classifier")
    print("=" * 40)
    
    test_texts = [
        "BREAKING! Election fraud discovered! Share before they delete this! The deep state doesn't want you to know!",
        "These idiots are stupid morons who should shut up and die. I hate all of them!",
        "According to Reuters and fact-checked by experts, the new policy has been implemented successfully.",
        "Beautiful weather today, enjoying a nice walk in the park."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text[:60]}...")
        label, confidence = detect_misinformation(text)
        print(f"Final Result: {label} (confidence: {confidence:.3f})")