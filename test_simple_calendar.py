"""
Simple test for Calendar API access.
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

def test_calendar_access():
    """Test Calendar API access."""
    print("=== TESTING CALENDAR API ACCESS ===")
    
    try:
        # Get credentials
        credentials, project = default()
        print(f"✅ Authenticated with project: {project}")
        
        # Build Calendar service
        calendar_service = build('calendar', 'v3', credentials=credentials)
        print("✅ Calendar service built successfully")
        
        # Try to list calendars
        try:
            calendar_list = calendar_service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            print(f"✅ Calendar API working - Found {len(calendars)} calendars")
            for calendar in calendars:
                print(f"  - {calendar.get('summary', 'No name')} ({calendar.get('id', 'No ID')})")
            
            return True
            
        except HttpError as e:
            if e.resp.status == 403:
                print(f"❌ Calendar API access denied: {e}")
                print("💡 This might be due to insufficient scopes")
                return False
            else:
                print(f"❌ Calendar API error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error setting up Calendar service: {e}")
        return False

def test_calendar_creation():
    """Test creating a calendar."""
    print("\n=== TESTING CALENDAR CREATION ===")
    
    try:
        # Get credentials
        credentials, project = default()
        
        # Build Calendar service
        calendar_service = build('calendar', 'v3', credentials=credentials)
        
        # Try to create a test calendar
        calendar_body = {
            'summary': 'Test Newsletter Calendar',
            'timeZone': 'Asia/Jerusalem',
            'description': 'Test calendar for newsletter automation'
        }
        
        try:
            created_calendar = calendar_service.calendars().insert(body=calendar_body).execute()
            print(f"✅ Successfully created test calendar: {created_calendar.get('summary')}")
            
            # Clean up - delete the test calendar
            calendar_service.calendars().delete(calendarId=created_calendar['id']).execute()
            print("✅ Test calendar deleted")
            
            return True
            
        except HttpError as e:
            if e.resp.status == 403:
                print(f"❌ Calendar creation denied: {e}")
                return False
            else:
                print(f"❌ Calendar creation error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing calendar creation: {e}")
        return False

def main():
    """Run Calendar API tests."""
    setup_logging()
    
    print("📅 TESTING CALENDAR API ACCESS")
    print("=" * 40)
    
    # Test basic access
    access_ok = test_calendar_access()
    
    # Test calendar creation
    creation_ok = test_calendar_creation()
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 CALENDAR API TEST SUMMARY")
    print(f"Calendar Access: {'✅ Working' if access_ok else '❌ Failed'}")
    print(f"Calendar Creation: {'✅ Working' if creation_ok else '❌ Failed'}")
    
    if access_ok and creation_ok:
        print("\n🎉 Calendar API is working perfectly!")
        print("📝 Ready to create newsletter events")
    elif access_ok:
        print("\n⚠️ Calendar access works, but creation failed")
        print("📝 This might be sufficient for basic functionality")
    else:
        print("\n⚠️ Calendar API needs additional setup")
        print("📝 Check authentication and permissions")

if __name__ == "__main__":
    main() 