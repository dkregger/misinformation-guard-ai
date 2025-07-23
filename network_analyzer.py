"""
Network Analysis Module for Detecting Coordinated Behavior

This module analyzes patterns across multiple users and posts to detect:
1. Bot networks (groups of fake accounts working together)
2. Coordinated campaigns (organized misinformation efforts)
3. Suspicious posting patterns and user behaviors

For beginners: Think of this as looking at the "big picture" - instead of 
analyzing just one post, we look at how many accounts are posting similar 
content at the same time, which often reveals organized misinformation campaigns.
"""

import networkx as nx
import pandas as pd
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
import numpy as np
import json
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class NetworkAnalyzer:
    """
    Main class for analyzing user networks and detecting coordinated behavior.
    
    This looks for patterns like:
    - Multiple accounts posting identical content
    - Accounts that always interact with each other
    - Suspicious timing patterns in posts
    - Network structures typical of bot farms
    """
    
    def __init__(self):
        """Initialize the network analyzer"""
        print("🕸️ Initializing Network Analyzer...")
        
        # Configuration
        self.similarity_threshold = 0.8  # How similar posts need to be to be considered coordinated
        self.time_window_hours = 24      # Look for coordination within 24 hours
        self.min_cluster_size = 3        # Minimum accounts needed to be considered a network
        
        # Data storage for analysis
        self.user_posts = defaultdict(list)      # user_id -> [posts]
        self.user_interactions = defaultdict(list)  # user_id -> [interactions]
        self.posting_timeline = []               # [(timestamp, user_id, content)]
        self.user_profiles = {}                  # user_id -> profile_data
        
        print("✅ Network Analyzer ready!")
    
    def add_user_data(self, user_id, profile_data, posts, interactions=None):
        """
        Add data about a user for network analysis
        
        Args:
            user_id (str): Unique identifier for the user
            profile_data (dict): User profile information (follower count, etc.)
            posts (list): List of posts by this user
            interactions (list): List of interactions (likes, retweets, etc.)
        
        For beginners: This is like adding a person's information to our 
        investigation database so we can look for patterns later.
        """
        try:
            # Store user profile
            self.user_profiles[user_id] = {
                'user_id': user_id,
                'follower_count': profile_data.get('follower_count', 0),
                'following_count': profile_data.get('following_count', 0),
                'account_age_days': profile_data.get('account_age_days', 0),
                'username': profile_data.get('username', user_id),
                'bio': profile_data.get('bio', ''),
                'verified': profile_data.get('verified', False),
                'added_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Store posts with metadata
            for post in posts:
                post_data = {
                    'content': post.get('content', ''),
                    'timestamp': post.get('timestamp', datetime.now(timezone.utc).isoformat()),
                    'url': post.get('url', ''),
                    'likes': post.get('likes', 0),
                    'shares': post.get('shares', 0),
                    'hashtags': post.get('hashtags', []),
                    'mentions': post.get('mentions', [])
                }
                
                self.user_posts[user_id].append(post_data)
                
                # Add to timeline for temporal analysis
                self.posting_timeline.append({
                    'timestamp': post_data['timestamp'],
                    'user_id': user_id,
                    'content': post_data['content'],
                    'hashtags': post_data['hashtags']
                })
            
            # Store interactions if provided
            if interactions:
                self.user_interactions[user_id] = interactions
            
            print(f"📊 Added data for user {user_id}: {len(posts)} posts")
            
        except Exception as e:
            print(f"❌ Error adding user data: {e}")
    
    def analyze_network(self):
        """
        Perform comprehensive network analysis to detect coordinated behavior
        
        Returns:
            dict: Complete analysis results including detected networks,
                  suspicious patterns, and coordination scores
        
        For beginners: This is the main function that looks at all the data
        we've collected and finds suspicious patterns.
        """
        try:
            print("🔍 Starting comprehensive network analysis...")
            print(f"📊 Data to analyze: {len(self.user_profiles)} users, {sum(len(posts) for posts in self.user_posts.values())} posts")
            
            # Show progress bar setup
            total_steps = 5
            current_step = 0
            
            def show_progress(step_name, current, total):
                current_step_progress = (current / total) * 100 if total > 0 else 100
                print(f"   📈 {step_name}: {current}/{total} ({current_step_progress:.1f}%)")
            
            # Run all analysis methods
            results = {
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                'total_users': len(self.user_profiles),
                'total_posts': sum(len(posts) for posts in self.user_posts.values()),
                'analysis_methods': {}
            }
            
            # 1. Content Similarity Analysis
            current_step += 1
            print(f"\n📝 Step {current_step}/{total_steps}: Analyzing content similarity...")
            content_analysis = self._analyze_content_similarity()
            results['analysis_methods']['content_similarity'] = content_analysis
            print(f"   ✅ Found {content_analysis.get('total_groups_found', 0)} similar content groups")
            
            # 2. Temporal Pattern Analysis
            current_step += 1
            print(f"\n⏰ Step {current_step}/{total_steps}: Analyzing posting patterns...")
            temporal_analysis = self._analyze_temporal_patterns()
            results['analysis_methods']['temporal_patterns'] = temporal_analysis
            print(f"   ✅ Found {temporal_analysis.get('suspicious_time_clusters', 0)} time clusters")
            
            # 3. User Behavior Analysis
            current_step += 1
            print(f"\n👤 Step {current_step}/{total_steps}: Analyzing user behaviors...")
            behavior_analysis = self._analyze_user_behaviors()
            results['analysis_methods']['user_behaviors'] = behavior_analysis
            print(f"   ✅ Found {behavior_analysis.get('total_suspicious', 0)} suspicious users")
            
            # 4. Network Structure Analysis
            current_step += 1
            print(f"\n🕸️ Step {current_step}/{total_steps}: Analyzing network structures...")
            network_analysis = self._analyze_network_structure()
            results['analysis_methods']['network_structure'] = network_analysis
            print(f"   ✅ Found {len(network_analysis.get('suspicious_components', []))} network clusters")
            
            # 5. Calculate Overall Coordination Score
            current_step += 1
            print(f"\n🎯 Step {current_step}/{total_steps}: Calculating coordination scores...")
            coordination_analysis = self._calculate_coordination_scores(results['analysis_methods'])
            results['coordination_analysis'] = coordination_analysis
            print(f"   ✅ Final coordination score: {coordination_analysis.get('overall_coordination_score', 0):.2f}")
            
            print(f"\n✅ Network analysis completed! ({current_step}/{total_steps} steps finished)")
            return results
            
        except Exception as e:
            print(f"❌ Error in network analysis: {e}")
            return {
                'error': str(e),
                'analysis_timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _analyze_content_similarity(self):
        """
        Find groups of users posting very similar content
        
        For beginners: This looks for accounts posting nearly identical messages,
        which is a common sign of bot networks or coordinated campaigns.
        """
        try:
            # Collect all posts with metadata
            all_posts = []
            for user_id, posts in self.user_posts.items():
                for post in posts:
                    all_posts.append({
                        'user_id': user_id,
                        'content': post['content'],
                        'timestamp': post['timestamp']
                    })
            
            if len(all_posts) < 2:
                return {'status': 'insufficient_data', 'similar_content_groups': []}
            
            # Create text similarity matrix using simple approach
            similar_groups = self._simple_content_similarity(all_posts)
            
            return similar_groups
            
        except Exception as e:
            print(f"❌ Error in content similarity analysis: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _simple_content_similarity(self, all_posts):
        """Fallback method for content similarity using simple text comparison"""
        try:
            similar_groups = []
            processed_posts = set()
            
            print(f"   🔍 Comparing {len(all_posts)} posts for similarity...")
            
            for i, post1 in enumerate(all_posts):
                if i in processed_posts:
                    continue
                
                # Show progress every 10 posts or on small datasets
                if i % max(1, len(all_posts) // 10) == 0:
                    progress = (i / len(all_posts)) * 100
                    print(f"      📈 Content analysis progress: {i}/{len(all_posts)} ({progress:.1f}%)")
                
                similar_posts = [i]
                content1 = post1['content'].lower().strip()
                
                for j, post2 in enumerate(all_posts[i+1:], i+1):
                    if j in processed_posts:
                        continue
                    
                    content2 = post2['content'].lower().strip()
                    
                    # Simple similarity check
                    if len(content1) > 0 and len(content2) > 0:
                        # Check for exact matches or very high overlap
                        if content1 == content2 or self._text_overlap_ratio(content1, content2) > 0.8:
                            similar_posts.append(j)
                
                if len(similar_posts) >= self.min_cluster_size:
                    group_users = [all_posts[idx]['user_id'] for idx in similar_posts]
                    similar_groups.append({
                        'users': list(set(group_users)),
                        'post_count': len(similar_posts),
                        'sample_content': all_posts[similar_posts[0]]['content'][:200],
                        'user_count': len(set(group_users))
                    })
                    processed_posts.update(similar_posts)
                    print(f"      🎯 Found similar content group: {len(set(group_users))} users, {len(similar_posts)} posts")
            
            print(f"   ✅ Content similarity analysis complete: {len(similar_groups)} groups found")
            
            return {
                'status': 'analyzed',
                'similar_content_groups': similar_groups,
                'total_groups_found': len(similar_groups),
                'method': 'simple_text_comparison'
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _text_overlap_ratio(self, text1, text2):
        """Calculate overlap ratio between two texts"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0.0
    
    def _analyze_temporal_patterns(self):
        """
        Analyze timing patterns in posts to detect coordination
        
        For beginners: Bot networks often post at suspiciously similar times,
        like all posting within minutes of each other about the same topic.
        """
        try:
            if len(self.posting_timeline) < 2:
                return {'status': 'insufficient_data'}
            
            # Sort timeline by timestamp
            sorted_timeline = sorted(self.posting_timeline, key=lambda x: x['timestamp'])
            
            # Group posts by time windows
            time_clusters = []
            current_cluster = []
            
            for i, post in enumerate(sorted_timeline):
                try:
                    current_time = datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00'))
                except:
                    current_time = datetime.now(timezone.utc)  # Fallback
                
                if not current_cluster:
                    current_cluster.append({'post': post, 'timestamp': current_time})
                else:
                    last_time = current_cluster[-1]['timestamp']
                    time_diff = (current_time - last_time).total_seconds() / 3600  # Hours
                    
                    if time_diff <= 1:  # Within 1 hour
                        current_cluster.append({'post': post, 'timestamp': current_time})
                    else:
                        # Process current cluster if it has multiple users
                        if len(current_cluster) >= self.min_cluster_size:
                            cluster_users = list(set([item['post']['user_id'] for item in current_cluster]))
                            if len(cluster_users) >= self.min_cluster_size:
                                time_clusters.append({
                                    'start_time': current_cluster[0]['timestamp'].isoformat(),
                                    'end_time': current_cluster[-1]['timestamp'].isoformat(),
                                    'post_count': len(current_cluster),
                                    'unique_users': len(cluster_users),
                                    'users': cluster_users,
                                    'duration_minutes': (current_cluster[-1]['timestamp'] - current_cluster[0]['timestamp']).total_seconds() / 60
                                })
                        
                        # Start new cluster
                        current_cluster = [{'post': post, 'timestamp': current_time}]
            
            # Don't forget the last cluster
            if len(current_cluster) >= self.min_cluster_size:
                cluster_users = list(set([item['post']['user_id'] for item in current_cluster]))
                if len(cluster_users) >= self.min_cluster_size:
                    time_clusters.append({
                        'start_time': current_cluster[0]['timestamp'].isoformat(),
                        'end_time': current_cluster[-1]['timestamp'].isoformat(),
                        'post_count': len(current_cluster),
                        'unique_users': len(cluster_users),
                        'users': cluster_users,
                        'duration_minutes': (current_cluster[-1]['timestamp'] - current_cluster[0]['timestamp']).total_seconds() / 60
                    })
            
            # Analyze posting frequency patterns
            user_posting_times = defaultdict(list)
            for post in sorted_timeline:
                try:
                    post_time = datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00'))
                    user_posting_times[post['user_id']].append(post_time)
                except:
                    continue
            
            # Find users with suspiciously regular posting patterns
            regular_posters = []
            for user_id, times in user_posting_times.items():
                if len(times) >= 3:
                    intervals = []
                    for i in range(1, len(times)):
                        interval = (times[i] - times[i-1]).total_seconds() / 3600  # Hours
                        intervals.append(interval)
                    
                    # Check if posting intervals are suspiciously regular
                    if len(intervals) > 1:
                        interval_std = np.std(intervals)
                        avg_interval = np.mean(intervals)
                        
                        # Very regular posting (low variance) can indicate automation
                        if interval_std < 0.5 and avg_interval < 24:  # Posting every few hours with low variance
                            regular_posters.append({
                                'user_id': user_id,
                                'avg_interval_hours': avg_interval,
                                'interval_variance': interval_std,
                                'post_count': len(times)
                            })
            
            return {
                'status': 'analyzed',
                'temporal_clusters': time_clusters,
                'suspicious_time_clusters': len(time_clusters),
                'regular_posting_patterns': regular_posters,
                'method': 'time_window_clustering'
            }
            
        except Exception as e:
            print(f"❌ Error in temporal analysis: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _analyze_user_behaviors(self):
        """
        Analyze individual user behaviors for bot-like characteristics
        
        For beginners: This looks at each user's individual behavior patterns
        to see if they act like bots (posting too frequently, unusual follower ratios, etc.).
        """
        try:
            suspicious_users = []
            behavior_patterns = {}
            
            total_users = len(self.user_profiles)
            print(f"   🔍 Analyzing behavior patterns for {total_users} users...")
            
            for idx, (user_id, profile) in enumerate(self.user_profiles.items()):
                # Show progress
                if idx % max(1, total_users // 5) == 0 or idx == total_users - 1:
                    progress = ((idx + 1) / total_users) * 100
                    print(f"      📈 User behavior analysis: {idx + 1}/{total_users} ({progress:.1f}%)")
                
                user_posts = self.user_posts.get(user_id, [])
                
                # Calculate behavior metrics
                behavior_score = 0.0
                flags = []
                
                # 1. Posting frequency analysis
                if len(user_posts) > 0:
                    account_age = max(1, profile.get('account_age_days', 1))
                    posts_per_day = len(user_posts) / account_age
                    
                    if posts_per_day > 50:  # More than 50 posts per day
                        behavior_score += 0.3
                        flags.append(f"Extremely high posting rate: {posts_per_day:.1f} posts/day")
                    elif posts_per_day > 20:
                        behavior_score += 0.2
                        flags.append(f"High posting rate: {posts_per_day:.1f} posts/day")
                
                # 2. Follower/following ratio analysis
                followers = profile.get('follower_count', 0)
                following = profile.get('following_count', 0)
                
                if followers > 0:
                    follow_ratio = following / followers
                    if follow_ratio > 10:  # Following way more than followers
                        behavior_score += 0.2
                        flags.append(f"Suspicious follow ratio: {follow_ratio:.1f}")
                
                # 3. Account age vs activity
                if account_age < 30 and len(user_posts) > 100:  # New account, high activity
                    behavior_score += 0.25
                    flags.append("New account with high activity")
                
                # 4. Bio analysis
                bio = profile.get('bio', '').lower()
                if not bio:
                    behavior_score += 0.1
                    flags.append("Empty profile bio")
                elif any(phrase in bio for phrase in ['follow me', 'dm for promo', 'crypto', 'investment']):
                    behavior_score += 0.15
                    flags.append("Generic promotional bio")
                
                # Store behavior analysis
                behavior_patterns[user_id] = {
                    'behavior_score': behavior_score,
                    'flags': flags,
                    'posts_per_day': len(user_posts) / max(1, account_age),
                    'follow_ratio': following / max(1, followers),
                    'account_age_days': account_age
                }
                
                # Mark as suspicious if score is high
                if behavior_score > 0.5:
                    suspicious_users.append({
                        'user_id': user_id,
                        'username': profile.get('username', user_id),
                        'behavior_score': behavior_score,
                        'primary_flags': flags[:3],  # Top 3 flags
                        'post_count': len(user_posts)
                    })
                    print(f"      🚨 Suspicious user detected: {user_id} (score: {behavior_score:.2f})")
            
            print(f"   ✅ User behavior analysis complete: {len(suspicious_users)} suspicious users found")
            
            return {
                'status': 'analyzed',
                'suspicious_users': suspicious_users,
                'total_suspicious': len(suspicious_users),
                'behavior_patterns': behavior_patterns,
                'method': 'multi_factor_behavior_analysis'
            }
            
        except Exception as e:
            print(f"❌ Error in behavior analysis: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _analyze_network_structure(self):
        """
        Analyze the overall network structure to find coordinated groups
        
        For beginners: This creates a "map" of who interacts with whom and
        looks for suspicious patterns like isolated clusters that might be bot networks.
        """
        try:
            # For now, we'll do a simplified network analysis since we don't have interaction data
            # We'll create connections based on content similarity
            
            similar_content_groups = []
            
            # Get content similarity groups from our previous analysis
            if hasattr(self, '_last_content_analysis'):
                similar_content_groups = self._last_content_analysis.get('similar_content_groups', [])
            
            suspicious_components = []
            
            # Analyze each content similarity group as a potential network
            for group in similar_content_groups:
                if len(group.get('users', [])) >= self.min_cluster_size:
                    suspicious_components.append({
                        'users': group['users'],
                        'size': len(group['users']),
                        'density': 1.0,  # Simplified - all users in group are connected by similar content
                        'clustering_coefficient': 1.0,  # Simplified
                        'suspicion_score': len(group['users']) / 10.0  # Simple scoring
                    })
            
            return {
                'status': 'analyzed',
                'total_users_in_network': len(self.user_profiles),
                'total_connections': sum(len(comp['users']) for comp in suspicious_components),
                'connected_components': len(suspicious_components),
                'suspicious_components': suspicious_components,
                'network_density': len(suspicious_components) / max(1, len(self.user_profiles)),
                'method': 'content_similarity_based'
            }
            
        except Exception as e:
            print(f"❌ Error in network structure analysis: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _calculate_coordination_scores(self, analysis_results):
        """
        Calculate overall coordination scores based on all analysis methods
        
        For beginners: This combines all our different analysis results into
        a final "how coordinated/suspicious is this network" score.
        """
        try:
            coordination_score = 0.0
            evidence = []
            
            # Weight different types of evidence
            weights = {
                'content_similarity': 0.3,
                'temporal_patterns': 0.25,
                'user_behaviors': 0.25,
                'network_structure': 0.2
            }
            
            # Content similarity evidence
            content_analysis = analysis_results.get('content_similarity', {})
            if content_analysis.get('status') == 'analyzed':
                similar_groups = content_analysis.get('total_groups_found', 0)
                if similar_groups > 0:
                    content_score = min(1.0, similar_groups / 3.0)  # Normalize
                    coordination_score += content_score * weights['content_similarity']
                    evidence.append(f"{similar_groups} groups posting similar content")
            
            # Temporal pattern evidence
            temporal_analysis = analysis_results.get('temporal_patterns', {})
            if temporal_analysis.get('status') == 'analyzed':
                time_clusters = temporal_analysis.get('suspicious_time_clusters', 0)
                regular_posters = len(temporal_analysis.get('regular_posting_patterns', []))
                
                if time_clusters > 0 or regular_posters > 0:
                    temporal_score = min(1.0, (time_clusters + regular_posters) / 5.0)
                    coordination_score += temporal_score * weights['temporal_patterns']
                    if time_clusters > 0:
                        evidence.append(f"{time_clusters} coordinated posting time periods")
                    if regular_posters > 0:
                        evidence.append(f"{regular_posters} users with automated posting patterns")
            
            # User behavior evidence
            behavior_analysis = analysis_results.get('user_behaviors', {})
            if behavior_analysis.get('status') == 'analyzed':
                suspicious_users = behavior_analysis.get('total_suspicious', 0)
                total_users = len(self.user_profiles)
                
                if suspicious_users > 0 and total_users > 0:
                    behavior_score = suspicious_users / total_users
                    coordination_score += behavior_score * weights['user_behaviors']
                    evidence.append(f"{suspicious_users} users with bot-like behavior")
            
            # Network structure evidence
            network_analysis = analysis_results.get('network_structure', {})
            if network_analysis.get('status') == 'analyzed':
                suspicious_components = len(network_analysis.get('suspicious_components', []))
                if suspicious_components > 0:
                    network_score = min(1.0, suspicious_components / 2.0)
                    coordination_score += network_score * weights['network_structure']
                    evidence.append(f"{suspicious_components} suspicious network clusters")
            
            # Determine overall assessment
            if coordination_score > 0.8:
                assessment = "Highly coordinated network detected"
                risk_level = "HIGH"
            elif coordination_score > 0.6:
                assessment = "Likely coordinated behavior"
                risk_level = "MEDIUM"
            elif coordination_score > 0.4:
                assessment = "Some coordination indicators present"
                risk_level = "LOW"
            else:
                assessment = "No significant coordination detected"
                risk_level = "MINIMAL"
            
            return {
                'overall_coordination_score': coordination_score,
                'risk_level': risk_level,
                'assessment': assessment,
                'evidence_summary': evidence,
                'confidence': min(1.0, coordination_score + 0.1),  # Slight confidence boost
                'recommendation': self._get_recommendation(risk_level, evidence)
            }
            
        except Exception as e:
            print(f"❌ Error calculating coordination scores: {e}")
            return {
                'overall_coordination_score': 0.0,
                'risk_level': 'UNKNOWN',
                'assessment': f'Analysis error: {str(e)}',
                'evidence_summary': [],
                'error': str(e)
            }
    
    def _get_recommendation(self, risk_level, evidence):
        """Generate recommendations based on analysis results"""
        if risk_level == "HIGH":
            return "Immediate investigation recommended. Strong evidence of coordinated manipulation."
        elif risk_level == "MEDIUM":
            return "Enhanced monitoring recommended. Multiple coordination indicators detected."
        elif risk_level == "LOW":
            return "Continued observation suggested. Some suspicious patterns identified."
        else:
            return "No immediate action required. Network appears organic."

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Network Analysis Module")
    print("=" * 50)
    
    analyzer = NetworkAnalyzer()
    
    # Add sample user data for testing
    sample_users = [
        {
            'user_id': 'user1',
            'profile': {'username': 'bot_user1', 'follower_count': 50, 'following_count': 2000, 'account_age_days': 30},
            'posts': [
                {'content': 'Breaking news! This is urgent! Share now!', 'timestamp': '2025-01-01T10:00:00'},
                {'content': 'Everyone must see this! The truth is here!', 'timestamp': '2025-01-01T14:00:00'}
            ]
        },
        {
            'user_id': 'user2', 
            'profile': {'username': 'bot_user2', 'follower_count': 45, 'following_count': 2100, 'account_age_days': 25},
            'posts': [
                {'content': 'Breaking news! This is urgent! Share now!', 'timestamp': '2025-01-01T10:05:00'},
                {'content': 'Everyone must see this! The truth is here!', 'timestamp': '2025-01-01T14:05:00'}
            ]
        }
    ]
    
    # Add users to analyzer
    for user_data in sample_users:
        analyzer.add_user_data(
            user_data['user_id'],
            user_data['profile'],
            user_data['posts']
        )
    
    # Run analysis
    results = analyzer.analyze_network()
    
    print(f"\n📊 Analysis Results:")
    print(f"Risk Level: {results.get('coordination_analysis', {}).get('risk_level', 'Unknown')}")
    print(f"Assessment: {results.get('coordination_analysis', {}).get('assessment', 'Unknown')}")
    print(f"Coordination Score: {results.get('coordination_analysis', {}).get('overall_coordination_score', 0):.2f}")
    
    evidence = results.get('coordination_analysis', {}).get('evidence_summary', [])
    if evidence:
        print("Evidence:")
        for item in evidence:
            print(f"  - {item}")