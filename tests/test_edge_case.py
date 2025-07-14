"""
Test script for edge case: committee schedule with multiple events and no specific times.
"""
import logging
import requests
from time_extractor import TimeExtractor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_committee_schedule_link():
    """Test the committee schedule link that contains multiple events without specific times."""
    
    # Committee schedule link (edge case)
    committee_link = "https://wordpress.us13.list-manage.com/track/click?u=f65a5e7e35679e023bb1c29fa&id=308e640a65&e=18dc259e38"
    
    print("Testing Committee Schedule Edge Case")
    print("=" * 50)
    print(f"Link: {committee_link}")
    print("-" * 50)
    
    # Initialize time extractor
    extractor = TimeExtractor()
    
    try:
        # Attempt to extract time
        extracted_times = extractor.extract_time_from_invitation_link(committee_link)
        
        if extracted_times:
            if isinstance(extracted_times, dict):
                if 'end' in extracted_times:
                    print(f"❌ UNEXPECTED: Extracted time range: {extracted_times['start']} - {extracted_times['end']}")
                else:
                    print(f"❌ UNEXPECTED: Extracted start time: {extracted_times['start']}")
            else:
                print(f"❌ UNEXPECTED: Extracted time: {extracted_times}")
        else:
            print(f"✅ EXPECTED: Could not extract time from committee schedule")
            print(f"   This is correct behavior for multi-day committee schedules")
            
    except Exception as e:
        print(f"✅ EXPECTED: Error occurred: {str(e)}")
        print(f"   This is expected for non-image content")

def test_link_content():
    """Test what content the link actually contains."""
    
    committee_link = "https://wordpress.us13.list-manage.com/track/click?u=f65a5e7e35679e023bb1c29fa&id=308e640a65&e=18dc259e38"
    
    print("\nTesting Link Content")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        session = requests.Session()
        response = session.get(committee_link, headers=headers, allow_redirects=True, timeout=15)
        final_url = response.url
        content_type = response.headers.get('content-type', '')
        
        print(f"Final URL: {final_url}")
        print(f"Content Type: {content_type}")
        print(f"Status Code: {response.status_code}")
        
        if 'text/html' in content_type:
            print(f"✅ EXPECTED: HTML content (committee schedule page)")
            print(f"   This should fail time extraction as expected")
        elif 'image' in content_type:
            print(f"❌ UNEXPECTED: Image content")
        else:
            print(f"Content type: {content_type}")
            
    except Exception as e:
        print(f"Error accessing link: {str(e)}")

if __name__ == "__main__":
    print("Committee Schedule Edge Case Test")
    print("=" * 60)
    
    # Test what the link contains
    test_link_content()
    
    # Test time extraction
    test_committee_schedule_link()
    
    print("\n" + "=" * 60)
    print("Expected Result: Time extraction should fail gracefully")
    print("System should fall back to default 19:00 times with warning") 