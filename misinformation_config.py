"""
Configuration file for misinformation monitoring targets.

This file defines the keywords, sources, and risk assessment logic
for detecting potential misinformation in social media and news content.
"""

# Political candidates frequently mentioned in misinformation
POLITICAL_CANDIDATES = [
    "Donald Trump",
    "Kamala Harris", 
    "Ron DeSantis",
    "Gavin Newsom",
    "Joe Biden",
    "Sherrod Brown",
    "JD Vance",
    "Alexandria Ocasio-Cortez",
    "Ted Cruz",
    "Bernie Sanders"
]

# Government organizations often targeted in conspiracy theories
ORGANIZATIONS = [
    "CDC",           # Centers for Disease Control
    "WHO",           # World Health Organization
    "FDA",           # Food and Drug Administration
    "FBI",           # Federal Bureau of Investigation
    "CIA",           # Central Intelligence Agency
    "NATO",          # North Atlantic Treaty Organization
    "UN",            # United Nations
    "World Economic Forum",
    "Federal Reserve",
    "Supreme Court",
    "Department of Justice",
    "Homeland Security"
]

# Topics with high misinformation risk
MISINFORMATION_TOPICS = [
    # Election-related misinformation
    "election fraud",
    "voter fraud", 
    "election integrity",
    "mail-in voting",
    "voting machines",
    
    # Health misinformation
    "vaccine safety",
    "COVID-19 origins",
    "lab leak theory",
    "gain of function",
    "lockdown effectiveness",
    "mask mandates",
    "hydroxychloroquine",
    "ivermectin COVID",
    "vaccine mandates",
    "vaccine passport",
    
    # Conspiracy theories
    "deep state",
    "QAnon",
    "conspiracy theory",
    "great reset",
    "new world order",
    "climate change hoax",
    
    # Political events
    "January 6th",
    "Hunter Biden laptop",
    
    # Border and immigration
    "border crisis"
]

# News sources known for spreading misinformation
QUESTIONABLE_SOURCES = [
    "infowars.com",
    "breitbart.com", 
    "naturalnews.com",
    "zerohedge.com",
    "beforeitsnews.com",
    "activistpost.com",
    "thegatewayproject.com",
    "rumormillnews.com"
]

# Generally reliable news sources
RELIABLE_SOURCES = [
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "npr.org",
    "pbs.org",
    "factcheck.org",
    "snopes.com",
    "politifact.com",
    "washingtonpost.com",
    "nytimes.com",
    "wsj.com",
    "cnn.com",
    "abcnews.go.com",
    "nbcnews.com",
    "cbsnews.com"
]

def get_all_monitoring_keywords():
    """
    Get complete list of all keywords we monitor for misinformation.
    
    Returns:
        list: Combined list of candidates, organizations, and topics
    """
    all_keywords = []
    all_keywords.extend(POLITICAL_CANDIDATES)
    all_keywords.extend(ORGANIZATIONS) 
    all_keywords.extend(MISINFORMATION_TOPICS)
    return all_keywords

def get_high_risk_keywords():
    """
    Get keywords most strongly associated with misinformation.
    
    Returns:
        list: High-risk misinformation topics
    """
    return MISINFORMATION_TOPICS

def is_questionable_source(url):
    """
    Check if a URL comes from a source known for misinformation.
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if source is questionable, False otherwise
    """
    url_lower = url.lower()
    return any(source in url_lower for source in QUESTIONABLE_SOURCES)

def is_reliable_source(url):
    """
    Check if a URL comes from a generally reliable news source.
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if source is reliable, False otherwise
    """
    url_lower = url.lower()
    return any(source in url_lower for source in RELIABLE_SOURCES)

def get_keyword_risk_level(text):
    """
    Analyze text to determine misinformation risk based on keywords.
    
    Uses context-aware matching to reduce false positives when
    common organizations (WHO, CIA, etc.) are mentioned in
    legitimate news contexts.
    
    Args:
        text (str): Text content to analyze
        
    Returns:
        tuple: (risk_level, matching_keywords, risk_score)
            - risk_level: "HIGH", "MEDIUM", "LOW", or "MINIMAL"
            - matching_keywords: List of detected keywords
            - risk_score: Float between 0.0 and 1.0
    """
    text_lower = text.lower()
    
    # Check for high-risk misinformation topics with context awareness
    high_risk_matches = []
    for keyword in MISINFORMATION_TOPICS:
        if keyword.lower() in text_lower:
            # For short keywords that might have false positives,
            # check if they appear in suspicious context
            if keyword.lower() in ["who", "cia", "un"] and len(text) > 200:
                # Look for conspiracy-related context words
                suspicious_context = any(phrase in text_lower for phrase in [
                    "conspiracy", "cover up", "secret", "hidden", "deep state", 
                    "they don't want you to know", "mainstream media lies"
                ])
                if suspicious_context:
                    high_risk_matches.append(keyword)
            else:
                # For longer, more specific keywords, include directly
                high_risk_matches.append(keyword)
    
    # Check for political candidates (medium risk in misinformation context)
    candidate_matches = [
        candidate for candidate in POLITICAL_CANDIDATES 
        if candidate.lower() in text_lower
    ]
    
    # Check for organizations with context awareness
    org_matches = []
    for org in ORGANIZATIONS:
        if org.lower() in text_lower:
            # For very common organization names, require suspicious context
            if org.lower() in ["who", "un", "fda", "cdc"] and len(text) > 200:
                # Check if mentioned in potential misinformation context
                misinfo_context = any(phrase in text_lower for phrase in [
                    "conspiracy", "hoax", "lies", "cover up", "corruption", 
                    "agenda", "control", "manipulation"
                ])
                if misinfo_context:
                    org_matches.append(org)
            else:
                # For less common orgs or shorter text, include directly
                org_matches.append(org)
    
    # Calculate weighted risk score
    risk_score = 0.0
    risk_score += len(high_risk_matches) * 0.4  # High weight for misinformation topics
    risk_score += len(candidate_matches) * 0.2   # Medium weight for political figures
    risk_score += len(org_matches) * 0.1         # Lower weight for organizations
    
    # Determine risk level based on score
    if risk_score >= 0.8:
        risk_level = "HIGH"
    elif risk_score >= 0.4:
        risk_level = "MEDIUM" 
    elif risk_score >= 0.1:
        risk_level = "LOW"
    else:
        risk_level = "MINIMAL"
    
    # Combine all matches
    all_matches = high_risk_matches + candidate_matches + org_matches
    
    return risk_level, all_matches, min(1.0, risk_score)

# Test function for development
if __name__ == "__main__":
    print("Misinformation Configuration Test")
    print("=" * 50)
    
    print(f"Monitoring {len(POLITICAL_CANDIDATES)} political candidates")
    print(f"Monitoring {len(ORGANIZATIONS)} organizations") 
    print(f"Monitoring {len(MISINFORMATION_TOPICS)} high-risk topics")
    
    # Test risk assessment with sample texts
    test_texts = [
        "Breaking news about election fraud and voting machines being hacked by the deep state",
        "Donald Trump announces new campaign strategy for upcoming election",
        "CDC releases new health guidelines based on latest research",
        "Local weather forecast shows sunny skies for the weekend"
    ]
    
    print("\nTesting risk assessment:")
    for text in test_texts:
        risk_level, matches, score = get_keyword_risk_level(text)
        print(f"\nText: {text[:50]}...")
        print(f"Risk Level: {risk_level} (Score: {score:.2f})")
        print(f"Keywords: {matches}")