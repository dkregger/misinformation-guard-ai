"""
Image Analysis Module for Detecting Deepfakes and Manipulation

This module analyzes images to detect:
1. Deepfake faces (AI-generated or manipulated faces)
2. Image manipulation (photoshopped, edited content)
3. Suspicious visual patterns that indicate misinformation

For beginners: This works by using AI models that have been trained 
to recognize the subtle patterns that human eyes can't easily detect.
"""

import cv2
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import hashlib
import json
from datetime import datetime
import os

class ImageAnalyzer:
    """
    Main class for analyzing images for manipulation and deepfakes.
    
    This uses multiple detection methods:
    - Facial analysis for deepfakes
    - Pixel analysis for manipulation
    - Metadata analysis for authenticity
    """
    
    def __init__(self):
        """Initialize the image analyzer with detection models"""
        self.confidence_threshold = 0.6  # How confident we need to be to flag something
        print("🖼️ Initializing Image Analyzer...")
        
        # Try to load advanced models (optional - will use basic detection if not available)
        self.deepfake_model = self._load_deepfake_model()
        self.manipulation_detector = self._load_manipulation_detector()
        
        print("✅ Image Analyzer ready!")
    
    def _load_deepfake_model(self):
        """
        Load deepfake detection model
        
        For beginners: This tries to load a pre-trained AI model that can detect
        fake faces. If the model isn't available, we'll use simpler detection methods.
        """
        try:
            # In a production system, you'd load a real deepfake detection model here
            # For now, we'll simulate this with basic face detection
            print("📁 Loading deepfake detection model...")
            
            # OpenCV's built-in face detector (not a deepfake detector, but a starting point)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            print("✅ Basic face detection loaded")
            return face_cascade
            
        except Exception as e:
            print(f"⚠️ Could not load deepfake model: {e}")
            print("ℹ️ Will use basic image analysis instead")
            return None
    
    def _load_manipulation_detector(self):
        """
        Load image manipulation detection capabilities
        
        For beginners: This sets up tools to detect if an image has been edited,
        like checking for inconsistent lighting or compression artifacts.
        """
        try:
            print("🔍 Setting up manipulation detection...")
            # We'll use OpenCV for basic manipulation detection
            return {
                'initialized': True,
                'methods': ['noise_analysis', 'compression_analysis', 'metadata_check']
            }
        except Exception as e:
            print(f"⚠️ Could not initialize manipulation detector: {e}")
            return None
    
    def analyze_image(self, image_url):
        """
        Main function to analyze an image for potential manipulation or deepfakes
        
        Args:
            image_url (str): URL of the image to analyze
            
        Returns:
            dict: Analysis results with confidence scores and detection details
        """
        try:
            print(f"🔍 Analyzing image: {image_url[:60]}...")
            
            # Download and prepare the image
            image_data = self._download_image(image_url)
            if not image_data:
                return self._create_error_result("Failed to download image")
            
            # Run all detection methods
            results = {
                'image_url': image_url,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'image_hash': self._calculate_image_hash(image_data),
                'detections': {}
            }
            
            # 1. Deepfake Detection
            deepfake_result = self._detect_deepfake(image_data)
            results['detections']['deepfake'] = deepfake_result
            
            # 2. Manipulation Detection  
            manipulation_result = self._detect_manipulation(image_data)
            results['detections']['manipulation'] = manipulation_result
            
            # 3. Metadata Analysis
            metadata_result = self._analyze_metadata(image_data)
            results['detections']['metadata'] = metadata_result
            
            # Calculate overall assessment
            overall_assessment = self._calculate_overall_assessment(results['detections'])
            results.update(overall_assessment)
            
            return results
            
        except Exception as e:
            print(f"❌ Error analyzing image: {e}")
            return self._create_error_result(str(e))
    
    def _download_image(self, image_url):
        """
        Download image from URL and convert to format we can analyze
        
        For beginners: This gets the image from the internet and converts it
        into a format that our analysis tools can work with.
        """
        try:
            response = requests.get(image_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            # Convert to PIL Image
            image = Image.open(BytesIO(response.content))
            
            # Convert to OpenCV format for analysis
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            return {
                'pil_image': image,
                'opencv_image': opencv_image,
                'raw_data': response.content,
                'size': image.size,
                'format': image.format
            }
            
        except Exception as e:
            print(f"❌ Failed to download image: {e}")
            return None
    
    def _calculate_image_hash(self, image_data):
        """
        Create a unique fingerprint for the image
        
        For beginners: This creates a unique ID for the image so we can track
        if the same image appears multiple times or gets slightly modified.
        """
        try:
            return hashlib.md5(image_data['raw_data']).hexdigest()
        except:
            return "unknown"
    
    def _detect_deepfake(self, image_data):
        """
        Analyze image for potential deepfake characteristics
        
        For beginners: This looks for signs that a face in the image might be
        AI-generated or digitally replaced (like inconsistent skin texture).
        """
        try:
            opencv_image = image_data['opencv_image']
            
            # Basic face detection (foundation for deepfake analysis)
            if self.deepfake_model is not None:
                gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
                faces = self.deepfake_model.detectMultiScale(gray, 1.1, 4)
                
                face_analysis = {
                    'faces_detected': len(faces),
                    'face_locations': faces.tolist() if len(faces) > 0 else [],
                    'suspicious_patterns': []
                }
                
                # Basic deepfake indicators (simplified for demonstration)
                deepfake_score = 0.0
                reasons = []
                
                if len(faces) > 0:
                    # Analyze each detected face
                    for (x, y, w, h) in faces:
                        face_region = opencv_image[y:y+h, x:x+w]
                        
                        # Check for common deepfake artifacts
                        artifacts = self._check_deepfake_artifacts(face_region)
                        deepfake_score += artifacts['score']
                        reasons.extend(artifacts['reasons'])
                
                # Normalize score
                if len(faces) > 0:
                    deepfake_score = min(1.0, deepfake_score / len(faces))
                
                return {
                    'method': 'basic_face_analysis',
                    'confidence': deepfake_score,
                    'is_suspicious': deepfake_score > self.confidence_threshold,
                    'details': face_analysis,
                    'reasons': reasons,
                    'status': 'analyzed'
                }
            
            else:
                return {
                    'method': 'unavailable',
                    'confidence': 0.0,
                    'is_suspicious': False,
                    'status': 'model_not_available'
                }
                
        except Exception as e:
            return {
                'method': 'error',
                'confidence': 0.0,
                'is_suspicious': False,
                'error': str(e),
                'status': 'failed'
            }
    
    def _check_deepfake_artifacts(self, face_region):
        """
        Look for common artifacts in deepfake images
        
        For beginners: Deepfakes often have telltale signs like:
        - Inconsistent lighting on the face
        - Unnatural skin texture
        - Odd blinking patterns (in video)
        - Mismatched resolution between face and background
        """
        score = 0.0
        reasons = []
        
        try:
            # Convert to different color spaces for analysis
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            hsv_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)
            
            # 1. Check for resolution inconsistencies
            face_height, face_width = gray_face.shape
            if face_height < 50 or face_width < 50:
                score += 0.2
                reasons.append("Very low resolution face (common in deepfakes)")
            
            # 2. Analyze texture consistency
            texture_variance = np.var(gray_face)
            if texture_variance < 100:  # Very smooth/artificial looking
                score += 0.3
                reasons.append("Unnaturally smooth skin texture")
            
            # 3. Check for compression artifacts around edges
            edges = cv2.Canny(gray_face, 50, 150)
            edge_density = np.sum(edges) / (face_height * face_width)
            if edge_density < 0.1:  # Too few natural edges
                score += 0.2
                reasons.append("Lack of natural facial details")
            
            # 4. Color consistency check
            # Check if face colors are too uniform (common in AI generation)
            color_std = np.std(hsv_face[:,:,1])  # Saturation channel
            if color_std < 20:
                score += 0.3
                reasons.append("Unnaturally uniform coloring")
            
        except Exception as e:
            print(f"⚠️ Error in deepfake artifact analysis: {e}")
        
        return {
            'score': min(1.0, score),
            'reasons': reasons
        }
    
    def _detect_manipulation(self, image_data):
        """
        Detect general image manipulation (not just deepfakes)
        
        For beginners: This looks for signs that ANY part of the image has been
        edited, like inconsistent lighting, copy-paste artifacts, or digital alterations.
        """
        try:
            opencv_image = image_data['opencv_image']
            
            manipulation_score = 0.0
            reasons = []
            
            # 1. Noise Analysis - manipulated images often have inconsistent noise
            noise_analysis = self._analyze_image_noise(opencv_image)
            manipulation_score += noise_analysis['score']
            reasons.extend(noise_analysis['reasons'])
            
            # 2. Compression Analysis - check for inconsistent compression
            compression_analysis = self._analyze_compression_artifacts(opencv_image)
            manipulation_score += compression_analysis['score'] 
            reasons.extend(compression_analysis['reasons'])
            
            # 3. Edge Analysis - look for unnatural edges/boundaries
            edge_analysis = self._analyze_edge_consistency(opencv_image)
            manipulation_score += edge_analysis['score']
            reasons.extend(edge_analysis['reasons'])
            
            # Normalize final score
            final_score = min(1.0, manipulation_score / 3.0)
            
            return {
                'method': 'multi_factor_analysis',
                'confidence': final_score,
                'is_suspicious': final_score > self.confidence_threshold,
                'reasons': reasons,
                'detailed_analysis': {
                    'noise': noise_analysis,
                    'compression': compression_analysis,
                    'edges': edge_analysis
                },
                'status': 'analyzed'
            }
            
        except Exception as e:
            return {
                'method': 'error',
                'confidence': 0.0,
                'is_suspicious': False,
                'error': str(e),
                'status': 'failed'
            }
    
    def _analyze_image_noise(self, image):
        """Analyze noise patterns that might indicate manipulation"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate noise variance across different regions
            height, width = gray.shape
            regions = [
                gray[0:height//2, 0:width//2],           # Top-left
                gray[0:height//2, width//2:width],       # Top-right  
                gray[height//2:height, 0:width//2],      # Bottom-left
                gray[height//2:height, width//2:width]   # Bottom-right
            ]
            
            variances = [np.var(region) for region in regions]
            variance_std = np.std(variances)
            
            score = 0.0
            reasons = []
            
            # High variance between regions suggests manipulation
            if variance_std > 1000:
                score += 0.4
                reasons.append("Inconsistent noise patterns across image regions")
            
            return {'score': score, 'reasons': reasons, 'variance_std': variance_std}
            
        except Exception as e:
            return {'score': 0.0, 'reasons': [], 'error': str(e)}
    
    def _analyze_compression_artifacts(self, image):
        """Look for inconsistent compression that suggests editing"""
        try:
            # Convert to frequency domain to analyze compression
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            f_transform = np.fft.fft2(gray)
            f_shift = np.fft.fftshift(f_transform)
            magnitude_spectrum = np.log(np.abs(f_shift) + 1)
            
            # Look for unusual frequency patterns
            center_y, center_x = np.array(magnitude_spectrum.shape) // 2
            center_region = magnitude_spectrum[center_y-50:center_y+50, center_x-50:center_x+50]
            edge_region = magnitude_spectrum[0:50, 0:50]
            
            center_energy = np.mean(center_region)
            edge_energy = np.mean(edge_region)
            
            score = 0.0
            reasons = []
            
            # Unusual frequency distribution can indicate manipulation
            energy_ratio = center_energy / (edge_energy + 1)
            if energy_ratio > 10 or energy_ratio < 0.1:
                score += 0.3
                reasons.append("Unusual frequency distribution suggesting editing")
            
            return {'score': score, 'reasons': reasons, 'energy_ratio': energy_ratio}
            
        except Exception as e:
            return {'score': 0.0, 'reasons': [], 'error': str(e)}
    
    def _analyze_edge_consistency(self, image):
        """Analyze edge patterns for signs of manipulation"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect edges using Canny
            edges = cv2.Canny(gray, 50, 150)
            
            # Analyze edge distribution
            height, width = edges.shape
            total_edges = np.sum(edges)
            edge_density = total_edges / (height * width)
            
            score = 0.0
            reasons = []
            
            # Very high or very low edge density can indicate manipulation
            if edge_density > 0.3:
                score += 0.2
                reasons.append("Unusually high edge density")
            elif edge_density < 0.05:
                score += 0.2
                reasons.append("Unusually low edge density")
            
            return {'score': score, 'reasons': reasons, 'edge_density': edge_density}
            
        except Exception as e:
            return {'score': 0.0, 'reasons': [], 'error': str(e)}
    
    def _analyze_metadata(self, image_data):
        """
        Analyze image metadata for authenticity clues
        
        For beginners: Image metadata contains information about when/how the image
        was created. Manipulated images often have suspicious or missing metadata.
        """
        try:
            pil_image = image_data['pil_image']
            
            # Extract EXIF data if available
            exif_data = {}
            if hasattr(pil_image, '_getexif') and pil_image._getexif():
                exif_data = pil_image._getexif()
            
            score = 0.0
            reasons = []
            
            # Check for missing or suspicious metadata
            if not exif_data:
                score += 0.2
                reasons.append("No EXIF metadata found (could indicate editing)")
            
            # Check image format
            format_name = image_data.get('format', 'unknown')
            if format_name in ['PNG', 'BMP']:  # Common formats for edited images
                score += 0.1
                reasons.append(f"Format ({format_name}) commonly used for edited images")
            
            return {
                'method': 'metadata_analysis',
                'confidence': min(1.0, score),
                'is_suspicious': score > 0.3,
                'reasons': reasons,
                'metadata_available': bool(exif_data),
                'image_format': format_name,
                'status': 'analyzed'
            }
            
        except Exception as e:
            return {
                'method': 'error',
                'confidence': 0.0,
                'is_suspicious': False,
                'error': str(e),
                'status': 'failed'
            }
    
    def _calculate_overall_assessment(self, detections):
        """
        Combine all detection results into an overall assessment
        
        For beginners: This takes all our different analysis results and
        combines them into a single "how suspicious is this image" score.
        """
        try:
            total_confidence = 0.0
            active_methods = 0
            all_reasons = []
            
            # Weight different detection methods
            weights = {
                'deepfake': 0.4,      # Deepfakes are high priority
                'manipulation': 0.4,   # General manipulation is also important
                'metadata': 0.2        # Metadata is supporting evidence
            }
            
            for method, weight in weights.items():
                if method in detections and detections[method]['status'] == 'analyzed':
                    confidence = detections[method]['confidence']
                    total_confidence += confidence * weight
                    active_methods += 1
                    
                    if detections[method]['is_suspicious']:
                        all_reasons.extend(detections[method]['reasons'])
            
            # Calculate final assessment
            if active_methods == 0:
                return {
                    'overall_suspicious': False,
                    'overall_confidence': 0.0,
                    'assessment': 'Unable to analyze image',
                    'primary_concerns': []
                }
            
            is_suspicious = total_confidence > self.confidence_threshold
            
            # Determine assessment level
            if total_confidence > 0.8:
                assessment = "Highly likely to be manipulated"
            elif total_confidence > 0.6:
                assessment = "Likely to be manipulated"
            elif total_confidence > 0.4:
                assessment = "Possibly manipulated"
            elif total_confidence > 0.2:
                assessment = "Minor concerns detected"
            else:
                assessment = "Appears authentic"
            
            return {
                'overall_suspicious': is_suspicious,
                'overall_confidence': total_confidence,
                'assessment': assessment,
                'primary_concerns': all_reasons[:3],  # Top 3 concerns
                'methods_used': active_methods
            }
            
        except Exception as e:
            return {
                'overall_suspicious': False,
                'overall_confidence': 0.0,
                'assessment': f'Analysis error: {str(e)}',
                'primary_concerns': []
            }
    
    def _create_error_result(self, error_message):
        """Create a standardized error result"""
        return {
            'overall_suspicious': False,
            'overall_confidence': 0.0,
            'assessment': f'Analysis failed: {error_message}',
            'error': error_message,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Image Analysis Module")
    print("=" * 50)
    
    analyzer = ImageAnalyzer()
    
    # Test with sample images (you'd replace these with real URLs)
    test_images = [
        "https://example.com/suspicious_face.jpg",
        "https://example.com/normal_photo.jpg"
    ]
    
    for image_url in test_images:
        print(f"\n🔍 Testing: {image_url}")
        result = analyzer.analyze_image(image_url)
        
        print(f"Assessment: {result.get('assessment', 'Unknown')}")
        print(f"Confidence: {result.get('overall_confidence', 0):.2f}")
        if result.get('primary_concerns'):
            print(f"Concerns: {', '.join(result['primary_concerns'])}")
        print("-" * 30)