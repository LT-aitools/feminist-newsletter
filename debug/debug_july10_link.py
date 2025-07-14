#!/usr/bin/env python3
"""
Debug script to test the specific July 10th invitation link.
"""

import logging
from time_extractor import TimeExtractor
import requests
from PIL import Image
import io
import cv2
import numpy as np
import pytesseract

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_july10_link():
    """Debug the specific July 10th invitation link."""
    
    # The specific link from July 10th event
    test_url = "https://wordpress.us13.list-manage.com/track/click?u=f65a5e7e35679e023bb1c29fa&id=f8d281c6d9&e=18dc259e38"
    
    print("=== DEBUGGING JULY 10TH INVITATION LINK ===")
    print(f"URL: {test_url}")
    print()
    
    # Initialize time extractor
    extractor = TimeExtractor()
    
    try:
        print("1. Following redirect and downloading image...")
        
        # Follow the redirect and get the final URL
        response = requests.get(test_url, allow_redirects=True, timeout=30)
        final_url = response.url
        print(f"   Final URL after redirect: {final_url}")
        print(f"   Response status: {response.status_code}")
        print(f"   Content type: {response.headers.get('content-type', 'unknown')}")
        
        if 'image' in response.headers.get('content-type', ''):
            print("   ✅ Content is an image")
            
            # Save the image for inspection
            image_data = response.content
            print(f"   Image size: {len(image_data)} bytes")
            
            # Try to open with PIL to get image details
            try:
                image = Image.open(io.BytesIO(image_data))
                print(f"   Image format: {image.format}")
                print(f"   Image size: {image.size}")
                print(f"   Image mode: {image.mode}")
            except Exception as e:
                print(f"   ❌ Could not open image with PIL: {e}")
            
            print()
            print("2. Running OCR on the image...")
            
            # Convert image data to OpenCV format
            pil_image = Image.open(io.BytesIO(image_data))
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            print()
            print("2. Running OCR on the image...")
            
            # Run OCR using the time extractor's method
            extracted_time = extractor._extract_time_from_image(opencv_image)
            print(f"   Extracted time: {extracted_time}")
            
            if extracted_time:
                print("   ✅ Time extraction successful!")
            else:
                print("   ❌ Time extraction failed - no valid time found")
                
                # Let's also try with different preprocessing
                print()
                print("4. Trying with different image preprocessing...")
                
                # Try with different preprocessing options
                preprocessed_image = extractor._preprocess_image(opencv_image)
                preprocessed_text = pytesseract.image_to_string(preprocessed_image, lang='heb+eng')
                print(f"   Preprocessed OCR Output:")
                print(f"   {'='*50}")
                print(preprocessed_text)
                print(f"   {'='*50}")
                
                # Try time extraction on preprocessed text
                preprocessed_time = extractor._find_time_in_text(preprocessed_text)
                print(f"   Extracted time (preprocessed): {preprocessed_time}")
                
        else:
            print("   ❌ Content is not an image")
            print(f"   Response content preview: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_july10_link() 