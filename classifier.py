from transformers import pipeline
import re

# Load models for different types of detection
try:
    print("Loading toxic comment detection model...")
    toxic_classifier = pipeline("text-classification", model="martin-ha/toxic-comment-model")
    print("✅ Toxic comment model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading toxic model: {e}")
    toxic_classifier = None

# You could add more models here in the future
# propaganda_classifier = pipeline("text-classification", model="some-propaganda-model")

def detect_misinformation(text):
    """
    Detect both toxic content and propaganda in text.
    Returns: (label, confidence_score)
    """
    
    # Run multiple detection methods
    toxic_result = detect_toxic_content(text)
    propaganda_result = detect_propaganda_keywords(text)
    keyword_toxic_result = detect_toxic_keywords(text)
    
    print(f"    Toxic model result: {toxic_result}")
    print(f"    Propaganda result: {propaganda_result}")
    print(f"    Keyword toxic result: {keyword_toxic_result}")
    
    # Find the highest confidence problematic content
    results = [toxic_result, propaganda_result, keyword_toxic_result]
    
    # Filter to only problematic content (not 'reliable')
    problematic_results = [r for r in results if r[0] != 'reliable']
    
    if problematic_results:
        # Return the highest confidence problematic result
        return max(problematic_results, key=lambda x: x[1])
    else:
        # Return the most confident reliable result
        return max(results, key=lambda x: x[1])

def detect_toxic_keywords(text):
    """
    Keyword-based toxic content detection as fallback
    """
    text_lower = text.lower()
    
    # Strong toxic indicators
    toxic_keywords = [
        'idiots', 'stupid', 'morons', 'shut up', 'die', 'hate', 'kill',
        'retard', 'dumb', 'pathetic', 'worthless', 'scum', 'trash',
        'loser', 'disgusting', 'sicko', 'creep', 'freak'
    ]
    
    # Hate speech patterns
    hate_patterns = [
        'should die', 'hate all', 'kill them', 'deserve to die',
        'are trash', 'are scum', 'piece of shit'
    ]
    
    toxic_count = sum(1 for keyword in toxic_keywords if keyword in text_lower)
    hate_count = sum(1 for pattern in hate_patterns if pattern in text_lower)
    
    total_toxic_score = toxic_count * 0.2 + hate_count * 0.4
    
    if total_toxic_score > 0.3:
        confidence = min(0.95, 0.6 + total_toxic_score)
        return 'toxic', confidence
    else:
        return 'reliable', 0.1

def detect_toxic_content(text):
    """
    Use the toxic comment model to detect harmful content
    """
    if toxic_classifier is None:
        return 'reliable', 0.0
    
    try:
        result = toxic_classifier(text)[0]
        print(f"    Toxic model raw result: {result}")
        
        if result['label'] == 'TOXIC':
            confidence = float(result['score'])
            print(f"    Toxic detection: confidence={confidence:.3f}")
            return 'toxic', confidence
        else:
            confidence = float(result['score'])  # This is confidence in "NOT TOXIC"
            print(f"    Non-toxic detection: confidence={confidence:.3f}")
            return 'reliable', confidence
            
    except Exception as e:
        print(f"Error in toxic classification: {e}")
        return 'reliable', 0.0

def detect_propaganda_keywords(text):
    """
    Enhanced keyword detection for propaganda and misinformation
    """
    text_lower = text.lower()
    
    # Propaganda and misinformation indicators
    propaganda_keywords = [
        'breaking', 'shocking', 'unverified', 'share before', 'they delete',
        'trust me', 'no sources', 'without fact-checking', 'propaganda',
        'wake up', 'they don\'t want you to know', 'mainstream media lies',
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
    
    # Count matches
    propaganda_count = sum(1 for keyword in propaganda_keywords if keyword in text_lower)
    reliable_count = sum(1 for keyword in reliable_keywords if keyword in text_lower)
    strong_propaganda_count = sum(1 for keyword in strong_propaganda if keyword in text_lower)
    
    # Calculate scores
    propaganda_score = propaganda_count * 0.15 + strong_propaganda_count * 0.25
    reliable_score = reliable_count * 0.15
    
    # Additional checks for suspicious patterns
    if has_suspicious_patterns(text):
        propaganda_score += 0.2
    
    if propaganda_score > reliable_score and propaganda_score > 0.3:
        confidence = min(0.95, 0.5 + propaganda_score)
        return 'propaganda', confidence
    else:
        confidence = min(0.9, 0.4 + reliable_score)
        return 'reliable', confidence

def has_suspicious_patterns(text):
    """
    Check for suspicious text patterns that might indicate misinformation
    """
    text_lower = text.lower()
    
    patterns = [
        r'!{3,}',  # Multiple exclamation marks
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
    Get a detailed summary of what was detected
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