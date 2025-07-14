"""
Test script to verify Google Cloud authentication and API access.
"""
import logging
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def setup_logging():
    """Setup logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def test_gmail_api():
    """Test Gmail API access."""
    print("=== TESTING GMAIL API ===")
    try:
        # Get credentials
        credentials, project = default()
        print(f"✅ Authenticated with project: {project}")
        
        # Build Gmail service
        gmail_service = build('gmail', 'v1', credentials=credentials)
        
        # Test API call
        profile = gmail_service.users().getProfile(userId='me').execute()
        print(f"✅ Gmail API working - Email: {profile.get('emailAddress')}")
        return True
        
    except Exception as e:
        print(f"❌ Gmail API error: {e}")
        return False

def test_calendar_api():
    """Test Calendar API access."""
    print("\n=== TESTING CALENDAR API ===")
    try:
        # Get credentials
        credentials, project = default()
        
        # Build Calendar service
        calendar_service = build('calendar', 'v3', credentials=credentials)
        
        # Test API call - list calendars
        calendar_list = calendar_service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        print(f"✅ Calendar API working - Found {len(calendars)} calendars")
        for calendar in calendars:
            print(f"  - {calendar.get('summary', 'No name')} ({calendar.get('id', 'No ID')})")
        return True
        
    except Exception as e:
        print(f"❌ Calendar API error: {e}")
        return False

def test_vision_api():
    """Test Vision API access."""
    print("\n=== TESTING VISION API ===")
    try:
        # Get credentials
        credentials, project = default()
        
        # Build Vision service
        vision_service = build('vision', 'v1', credentials=credentials)
        
        print("✅ Vision API service built successfully")
        return True
        
    except Exception as e:
        print(f"❌ Vision API error: {e}")
        return False

def main():
    """Run all authentication tests."""
    setup_logging()
    
    print("🔐 TESTING GOOGLE CLOUD AUTHENTICATION")
    print("=" * 50)
    
    # Test each API
    gmail_ok = test_gmail_api()
    calendar_ok = test_calendar_api()
    vision_ok = test_vision_api()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 AUTHENTICATION TEST SUMMARY")
    print(f"Gmail API: {'✅ Working' if gmail_ok else '❌ Failed'}")
    print(f"Calendar API: {'✅ Working' if calendar_ok else '❌ Failed'}")
    print(f"Vision API: {'✅ Working' if vision_ok else '❌ Failed'}")
    
    if gmail_ok and calendar_ok and vision_ok:
        print("\n🎉 All APIs are working! Ready for newsletter processing.")
    else:
        print("\n⚠️ Some APIs failed. Check the errors above.")

if __name__ == "__main__":
    main() 