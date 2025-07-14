"""
Time extraction module for extracting event times from invitation images.
Handles MailChimp redirects, image downloading, and OCR processing.
"""
import logging
import re
import requests
from typing import Optional, Tuple, List, Dict
from urllib.parse import urlparse, parse_qs
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from google.cloud import vision

from config import TIME_PATTERNS


class TimeExtractor:
    """Extracts event times from invitation images using OCR."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        # Set a reasonable timeout and user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_time_from_invitation_link(self, mailchimp_url: str) -> Optional[Dict[str, str]]:
        """
        Follow MailChimp redirect and extract time from the resulting image.
        
        Args:
            mailchimp_url: MailChimp tracking URL
            
        Returns:
            Dictionary with 'start' and optionally 'end' time strings (HH:MM format) 
            or None if extraction failed
        """
        try:
            self.logger.info(f"Processing invitation link: {mailchimp_url}")
            
            # Follow the redirect to get the actual image URL
            image_url = self._follow_mailchimp_redirect(mailchimp_url)
            if not image_url:
                self.logger.warning("Failed to follow MailChimp redirect")
                return None
            
            self.logger.info(f"Found image URL: {image_url}")
            
            # Download and process the image
            image_bytes = self._download_image(image_url)
            if image_bytes is None:
                self.logger.warning("Failed to download image")
                return None
            
            # Extract time using OCR
            extracted_times = self._extract_time_from_image(image_bytes)
            if extracted_times:
                if isinstance(extracted_times, dict):
                    if 'end' in extracted_times:
                        self.logger.info(f"Successfully extracted time range: {extracted_times['start']} - {extracted_times['end']}")
                    else:
                        self.logger.info(f"Successfully extracted start time: {extracted_times['start']}")
                else:
                    # Backward compatibility for single time string
                    self.logger.info(f"Successfully extracted time: {extracted_times}")
                    extracted_times = {'start': extracted_times}
            else:
                self.logger.warning("No time found in image")
            
            return extracted_times
            
        except Exception as e:
            self.logger.error(f"Error extracting time from invitation: {str(e)}")
            return None
    
    def _follow_mailchimp_redirect(self, mailchimp_url: str) -> Optional[str]:
        """
        Follow MailChimp redirect to get the actual image URL.
        
        Args:
            mailchimp_url: MailChimp tracking URL
            
        Returns:
            Actual image URL or None if redirect failed
        """
        try:
            # Follow redirects to get the final URL
            response = self.session.get(mailchimp_url, allow_redirects=True, timeout=10)
            response.raise_for_status()
            
            final_url = response.url
            self.logger.debug(f"Redirected to: {final_url}")
            
            # Check if the final URL is an image
            if self._is_image_url(final_url):
                return final_url
            
            # If not an image, try to extract image URL from the page content
            if 'text/html' in response.headers.get('content-type', ''):
                return self._extract_image_from_html(response.text)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error following redirect: {str(e)}")
            return None
    
    def _is_image_url(self, url: str) -> bool:
        """Check if URL points to an image file."""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        return any(path.endswith(ext) for ext in image_extensions)
    
    def _extract_image_from_html(self, html_content: str) -> Optional[str]:
        """Extract image URL from HTML content if redirect led to a webpage."""
        try:
            # Look for img tags
            img_pattern = r'<img[^>]+src=[\'"]([^\'"]+)[\'"]'
            matches = re.findall(img_pattern, html_content, re.IGNORECASE)
            
            for match in matches:
                if self._is_image_url(match):
                    return match
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting image from HTML: {str(e)}")
            return None
    
    def _download_image(self, image_url: str) -> Optional[bytes]:
        """
        Download image from URL and return raw bytes.
        Args:
            image_url: URL of the image to download
        Returns:
            Raw image bytes or None if download failed
        """
        try:
            response = self.session.get(image_url, timeout=15)
            response.raise_for_status()
            return response.content
        except Exception as e:
            self.logger.error(f"Error downloading image: {str(e)}")
            return None

    def _extract_time_from_image(self, image_bytes: bytes) -> Optional[Dict[str, str]]:
        """
        Extract time information from image using Google Cloud Vision OCR.
        Args:
            image_bytes: Raw image bytes
        Returns:
            Dictionary with 'start' and optionally 'end' time strings (HH:MM format) 
            or None if not found
        """
        try:
            # Use Google Cloud Vision API for OCR on original image bytes
            client = vision.ImageAnnotatorClient()
            vision_image = vision.Image(content=image_bytes)
            response = client.text_detection(image=vision_image)
            texts = response.text_annotations
            if texts:
                text = texts[0].description
                self.logger.debug(f"Vision OCR extracted text: {text[:200]}...")
                print("\n--- DEBUG: Vision OCR Output ---")
                print(text)
                print("--- END DEBUG ---\n")
            else:
                text = ''
                self.logger.warning("Vision OCR found no text.")

            # Look for time patterns in the extracted text
            extracted_times = self._find_time_in_text(text)
            if not extracted_times:
                print("\n--- DEBUG: No time found in OCR output for this image ---")
                print(text)
                print("--- END DEBUG ---\n")
            return extracted_times
        except Exception as e:
            self.logger.error(f"Error extracting time from image (Vision API): {str(e)}")
            return None
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: Original OpenCV image
            
        Returns:
            Preprocessed image
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply threshold to get binary image
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Apply morphological operations to clean up
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error preprocessing image: {str(e)}")
            return image
    
    def _find_time_in_text(self, text: str) -> Optional[Dict[str, str]]:
        """
        Find time patterns in OCR-extracted text.
        
        Args:
            text: Text extracted from image
            
        Returns:
            Dictionary with 'start' and optionally 'end' time strings (HH:MM format) 
            or None if not found
        """
        try:
            # Look for time patterns
            for pattern in TIME_PATTERNS:
                matches = re.findall(pattern, text)
                if matches:
                    # Handle different pattern formats
                    if len(matches[0]) == 4:  # Time range: 19:00-21:00
                        start_hour, start_minute, end_hour, end_minute = matches[0]
                        start_time = f"{int(start_hour):02d}:{int(start_minute):02d}"
                        end_time = f"{int(end_hour):02d}:{int(end_minute):02d}"
                        return {'start': start_time, 'end': end_time}
                    elif len(matches[0]) == 2:  # Single time: 19:00
                        hour, minute = matches[0]
                        time = f"{int(hour):02d}:{int(minute):02d}"
                        return {'start': time}
            
            # Look for common Hebrew time patterns with more strict validation
            hebrew_patterns = [
                r'(\d{1,2})\s*:\s*(\d{2})',  # 19 : 00
                r'(\d{1,2}):(\d{2})',        # 19:00
                r'(\d{1,2})\.(\d{2})',       # 19.00
            ]
            
            for pattern in hebrew_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    hour, minute = matches[0]
                    # Validate time range with more strict rules for event times
                    hour_int = int(hour)
                    minute_int = int(minute)
                    if (8 <= hour_int <= 23 and 0 <= minute_int <= 59 and 
                        minute_int % 5 == 0):  # Most event times are on 5-minute intervals
                        time = f"{hour_int:02d}:{minute_int:02d}"
                        return {'start': time}
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding time in text: {str(e)}")
            return None
    
    def extract_times_from_events(self, events: List[dict]) -> List[dict]:
        """
        Extract times from multiple events with invitation links.
        
        Args:
            events: List of event dictionaries with 'links' field
            
        Returns:
            Updated events list with extracted times
        """
        updated_events = []
        
        for event in events:
            try:
                # Look for invitation links
                invitation_links = [link for link in event.get('links', []) 
                                  if 'בהזמנה' in link.get('label', '')]
                
                if invitation_links:
                    # Try to extract time from the first invitation link
                    mailchimp_url = invitation_links[0]['url']
                    extracted_time = self.extract_time_from_invitation_link(mailchimp_url)
                    
                    if extracted_time:
                        # Update event with extracted time
                        event['time'] = extracted_time
                        event['time_verified'] = True
                        self.logger.info(f"Updated event '{event.get('title', 'Unknown')}' with time: {extracted_time}")
                    else:
                        event['time_verified'] = False
                        self.logger.info(f"Could not extract time for event '{event.get('title', 'Unknown')}'")
                else:
                    event['time_verified'] = False
                
                updated_events.append(event)
                
            except Exception as e:
                self.logger.error(f"Error processing event for time extraction: {str(e)}")
                event['time_verified'] = False
                updated_events.append(event)
        
        return updated_events 