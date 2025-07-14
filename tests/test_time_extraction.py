"""
Test script for time extraction functionality.
"""
import logging
import sys
from time_extractor import TimeExtractor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_time_extraction():
    """Test time extraction with the provided sample link."""
    
    # Updated MailChimp link (working)
    sample_link = "https://wordpress.us13.list-manage.com/track/click?u=f65a5e7e35679e023bb1c29fa&id=ffa30d4bfc&e=18dc259e38"
    
    print("Testing time extraction functionality...")
    print(f"Sample link: {sample_link}")
    print("-" * 50)
    
    # Initialize time extractor
    extractor = TimeExtractor()
    
    try:
        # Attempt to extract time
        extracted_times = extractor.extract_time_from_invitation_link(sample_link)
        
        if extracted_times:
            if isinstance(extracted_times, dict):
                if 'end' in extracted_times:
                    print(f"✅ SUCCESS: Extracted time range: {extracted_times['start']} - {extracted_times['end']}")
                else:
                    print(f"✅ SUCCESS: Extracted start time: {extracted_times['start']}")
            else:
                # Backward compatibility
                print(f"✅ SUCCESS: Extracted time: {extracted_times}")
        else:
            print("❌ FAILED: Could not extract time from the invitation")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        logging.exception("Detailed error information:")

def test_ocr_patterns():
    """Test OCR time pattern matching with sample text."""
    
    print("\nTesting OCR pattern matching...")
    print("-" * 50)
    
    # Sample Hebrew text with times
    sample_texts = [
        "האירוע יתקיים ביום שלישי בשעה 20:00",
        "שעת התחלה: 19:30 - שעת סיום: 21:30",
        "מ-18:00 עד 20:00",
        "19 : 00 - 21 : 00",
        "התחלה ב-20.00",
        "שעה: 19:00",
    ]
    
    extractor = TimeExtractor()
    
    for i, text in enumerate(sample_texts, 1):
        print(f"\nSample {i}: {text}")
        extracted_times = extractor._find_time_in_text(text)
        if extracted_times:
            if isinstance(extracted_times, dict):
                if 'end' in extracted_times:
                    print(f"  ✅ Extracted: {extracted_times['start']} - {extracted_times['end']}")
                else:
                    print(f"  ✅ Extracted: {extracted_times['start']}")
            else:
                print(f"  ✅ Extracted: {extracted_times}")
        else:
            print(f"  ❌ No time found")

def test_mailchimp_image_link():
    """Test extraction from MailChimp link that returns JPEG image directly."""
    print("\n" + "="*60)
    print("Testing MailChimp Image Link")
    print("="*60)
    
    extractor = TimeExtractor()
    
    # Test the specific link that was failing
    mailchimp_url = "https://wordpress.us13.list-manage.com/track/click?u=f65a5e7e35679e023bb1c29fa&id=f8d281c6d9&e=18dc259e38"
    
    print(f"Testing URL: {mailchimp_url}")
    
    result = extractor.extract_time_from_invitation_link(mailchimp_url)
    
    if result:
        print(f"✅ SUCCESS: Extracted time: {result}")
        if 'start' in result:
            print(f"   Start time: {result['start']}")
        if 'end' in result:
            print(f"   End time: {result['end']}")
    else:
        print("❌ FAILED: No time extracted")
    
    return result is not None

if __name__ == "__main__":
    print("Time Extraction Test Suite")
    print("=" * 50)
    
    # Test OCR patterns first
    test_ocr_patterns()
    
    # Test actual link processing
    test_time_extraction()
    test_mailchimp_image_link()  # Add the new test
    
    print("\n" + "=" * 50)
    print("Test completed!") 