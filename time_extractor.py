"""
Time extraction module for extracting event times from invitation images.
Handles MailChimp redirects, image downloading, and OCR processing.
"""
import logging
import re
import requests
from typing import Optional, Tuple, List, Dict
from urllib.parse import urlparse, parse_qs
# import cv2  # DEPRECATED: No longer used, replaced by Google Cloud Vision API
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
        Follow MailChimp redirect and extract time from the resulting content (image or HTML).
        
        Args:
            mailchimp_url: MailChimp tracking URL
            
        Returns:
            Dictionary with 'start' and optionally 'end' time strings (HH:MM format) 
            or None if extraction failed
        """
        try:
            self.logger.info(f"Processing invitation link: {mailchimp_url}")
            
            # Follow the redirect to get the actual content
            content_info = self._follow_mailchimp_redirect(mailchimp_url)
            if not content_info:
                self.logger.warning("Failed to follow MailChimp redirect")
                return None
            
            content_type = content_info.get('type')
            content_data = content_info.get('data')
            
            if content_type == 'image':
                self.logger.info(f"Found image URL: {content_data}")
                # Download and process the image
                image_bytes = self._download_image(content_data)
                if image_bytes is None:
                    self.logger.warning("Failed to download image")
                    return None
                
                # Extract time using OCR
                extracted_times = self._extract_time_from_image(image_bytes)
            elif content_type == 'html':
                self.logger.info("Found HTML content, extracting time from text")
                # Extract time directly from HTML text
                extracted_times = self._extract_time_from_html_text(content_data)
            elif content_type == 'pdf':
                self.logger.info(f"Found PDF URL: {content_data}")
                # Download and extract text from PDF
                extracted_times = self._extract_time_from_pdf(content_data)
            else:
                self.logger.warning(f"Unknown content type: {content_type}")
                return None
            
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
                self.logger.warning("No time found in content")
            
            return extracted_times
            
        except Exception as e:
            self.logger.error(f"Error extracting time from invitation: {str(e)}")
            return None
    
    def _follow_mailchimp_redirect(self, mailchimp_url: str) -> Optional[Dict[str, str]]:
        """
        Follow MailChimp redirect to get the actual content (image or HTML).
        
        Args:
            mailchimp_url: MailChimp tracking URL
            
        Returns:
            Dictionary with 'type' ('image' or 'html') and 'data' (URL or HTML content)
            or None if redirect failed
        """
        try:
            # Follow redirects to get the final URL
            response = self.session.get(mailchimp_url, allow_redirects=True, timeout=10)
            response.raise_for_status()
            
            final_url = response.url
            self.logger.debug(f"Redirected to: {final_url}")
            
            # Check if the final URL is an image
            if self._is_image_url(final_url):
                return {'type': 'image', 'data': final_url}
            
            # Check if the final URL is a PDF
            if self._is_pdf_url(final_url):
                return {'type': 'pdf', 'data': final_url}
            
            # If not an image or PDF, check if it's HTML content
            if 'text/html' in response.headers.get('content-type', ''):
                # First try to extract image URL from the page content
                image_url = self._extract_image_from_html(response.text)
                if image_url:
                    return {'type': 'image', 'data': image_url}
                else:
                    # If no image found, return the HTML content for text extraction
                    return {'type': 'html', 'data': response.text}
            
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
    
    def _is_pdf_url(self, url: str) -> bool:
        """Check if URL points to a PDF file."""
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        return path.endswith('.pdf')
    
    def _extract_image_from_html(self, html_content: str) -> Optional[str]:
        """Extract image URL from HTML content, prioritizing current event images."""
        try:
            # Collect all potential images
            all_images = []
            
            # Look for og:image meta tags
            og_image_pattern = r'<meta[^>]+property=[\'"]og:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]'
            og_matches = re.findall(og_image_pattern, html_content, re.IGNORECASE)
            for match in og_matches:
                if self._is_image_url(match):
                    all_images.append({
                        'url': match,
                        'type': 'og:image',
                        'priority': 1  # Lower priority for og:image (often cached/old)
                    })
            
            # Look for img tags
            img_pattern = r'<img[^>]+src=[\'"]([^\'"]+)[\'"]'
            img_matches = re.findall(img_pattern, html_content, re.IGNORECASE)
            for match in img_matches:
                if self._is_image_url(match):
                    # Check if it's likely a current event image
                    priority = 2  # Default priority for img tags
                    
                    # Higher priority for images that look like current event images
                    if any(keyword in match.lower() for keyword in ['2025', 'seminar', 'conference', 'יום-עיון']):
                        priority = 3
                    
                    # Lower priority for obviously old images
                    if any(keyword in match.lower() for keyword in ['2024', '2023', 'old', 'cache']):
                        priority = 0
                    
                    all_images.append({
                        'url': match,
                        'type': 'img',
                        'priority': priority
                    })
            
            if not all_images:
                return None
            
            # Sort by priority (highest first), then by type preference
            all_images.sort(key=lambda x: (x['priority'], x['type'] == 'img'), reverse=True)
            
            # Log all found images for debugging
            self.logger.info(f"Found {len(all_images)} potential images:")
            for i, img in enumerate(all_images):
                self.logger.info(f"  {i+1}. {img['type']} (priority {img['priority']}): {img['url']}")
            
            # Return the highest priority image
            selected_image = all_images[0]
            self.logger.info(f"Selected image: {selected_image['url']} (type: {selected_image['type']}, priority: {selected_image['priority']})")
            return selected_image['url']
            
        except Exception as e:
            self.logger.error(f"Error extracting image from HTML: {str(e)}")
            return None
    
    def _extract_time_from_html_text(self, html_content: str) -> Optional[Dict[str, str]]:
        """
        Extract time information directly from HTML text content.
        
        Args:
            html_content: HTML content as string
            
        Returns:
            Dictionary with 'start' and optionally 'end' time strings (HH:MM format) 
            or None if not found
        """
        try:
            # Remove HTML tags to get clean text
            clean_text = re.sub(r'<[^>]+>', ' ', html_content)
            # Normalize whitespace
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            self.logger.debug(f"Extracted text from HTML: {clean_text[:200]}...")
            print("\n--- DEBUG: HTML Text Content ---")
            print(clean_text)
            print("--- END DEBUG ---\n")
            
            # Look for time patterns in the cleaned text
            extracted_times = self._find_time_in_text(clean_text)
            if not extracted_times:
                print("\n--- DEBUG: No time found in HTML text ---")
                print(clean_text)
                print("--- END DEBUG ---\n")
            
            return extracted_times
            
        except Exception as e:
            self.logger.error(f"Error extracting time from HTML text: {str(e)}")
            return None
    
    def _extract_time_from_pdf(self, pdf_url: str) -> Optional[Dict[str, str]]:
        """
        Extract time information from PDF content.
        
        Args:
            pdf_url: URL of the PDF file
            
        Returns:
            Dictionary with 'start' and optionally 'end' time strings (HH:MM format) 
            or None if not found
        """
        try:
            # Download the PDF
            pdf_bytes = self._download_image(pdf_url)  # Reuse the download method
            if pdf_bytes is None:
                self.logger.warning("Failed to download PDF")
                return None
            
            # Try to extract text using PyPDF2 if available
            try:
                import PyPDF2
                from io import BytesIO
                
                pdf_file = BytesIO(pdf_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract text from all pages
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + " "
                
                self.logger.debug(f"Extracted text from PDF: {text[:200]}...")
                print("\n--- DEBUG: PDF Text Content ---")
                print(text)
                print("--- END DEBUG ---\n")
                
                # Look for time patterns in the extracted text
                extracted_times = self._find_time_in_text(text)
                if not extracted_times:
                    print("\n--- DEBUG: No time found in PDF text ---")
                    print(text)
                    print("--- END DEBUG ---\n")
                
                return extracted_times
                
            except ImportError:
                self.logger.warning("PyPDF2 not available, cannot extract text from PDF")
                return None
            except Exception as e:
                self.logger.error(f"Error extracting text from PDF: {str(e)}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
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
    
    # All cv2-based image processing functions below are deprecated and should not be used.
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
        Find time patterns in OCR-extracted text, prioritizing main event start times.
        
        Args:
            text: Text extracted from image
            
        Returns:
            Dictionary with 'start' and optionally 'end' time strings (HH:MM format) 
            or None if not found
        """
        try:
            # First, collect all time matches with their positions
            all_times = []
            for pattern in TIME_PATTERNS:
                for match in re.finditer(pattern, text):
                    if len(match.groups()) == 4:  # Time range: 19:00-21:00
                        start_hour, start_minute, end_hour, end_minute = match.groups()
                        start_time = f"{int(start_hour):02d}:{int(start_minute):02d}"
                        end_time = f"{int(end_hour):02d}:{int(end_minute):02d}"
                        all_times.append({
                            'start': start_time,
                            'end': end_time,
                            'position': match.start(),
                            'context': text[max(0, match.start()-30):match.end()+30]
                        })
                    elif len(match.groups()) == 2:  # Single time: 19:00
                        hour, minute = match.groups()
                        time = f"{int(hour):02d}:{int(minute):02d}"
                        all_times.append({
                            'start': time,
                            'position': match.start(),
                            'context': text[max(0, match.start()-30):match.end()+30]
                        })
            
            if not all_times:
                return None
            
            # Sort by position in text (appearance order)
            all_times.sort(key=lambda x: x['position'])
            
            # Filter out times that are clearly from old events or date references
            filtered_times = []
            for time_info in all_times:
                context = time_info['context'].lower()
                time_str = time_info['start']
                
                # Skip times that appear to be from old events or date references
                if any(skip_word in context for skip_word in ['2025', 'תשפייה', '|']):
                    self.logger.debug(f"Skipping time {time_str} - appears to be from old event: {context}")
                    continue
                
                # Skip very early morning times that are likely registration times
                if time_str in ['08:30', '09:00', '09:15', '09:45']:
                    # Only skip if it's clearly a registration/gathering time
                    if any(reg_word in context for reg_word in ['התכנסות', 'פתיחה', 'ברכות']):
                        self.logger.debug(f"Skipping time {time_str} - appears to be registration time: {context}")
                        continue
                
                filtered_times.append(time_info)
            
            # If we have filtered times, use the first one (main event start)
            if filtered_times:
                best_time = filtered_times[0]
                self.logger.info(f"Selected time {best_time['start']} from context: {best_time['context']}")
                return {'start': best_time['start']}
            
            # Fallback: if no filtered times, use the first time found
            if all_times:
                fallback_time = all_times[0]
                self.logger.warning(f"Using fallback time {fallback_time['start']} from context: {fallback_time['context']}")
                return {'start': fallback_time['start']}
            
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