"""
Focused test for time range integration in the complete workflow.
"""
import logging
from datetime import datetime, timedelta
from newsletter_processor import NewsletterProcessor, EventData
from calendar_handler import CalendarHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_time_range_integration():
    """Test that time ranges are correctly extracted and applied to events."""
    
    print("Time Range Integration Test")
    print("=" * 50)
    
    # Create a test event with invitation link
    test_event = EventData(
        title="קריאה פמיניסטית בארכיון - השקת ספרה של אריז'",
        date=datetime.now() + timedelta(days=1),
        time="19:00",  # Default time
        duration=120,  # Default duration
        location="בית אשה לאשה, רחוב ארלוזורוב 118 חיפה",
        organizer="ד\"ר רות פרפר",
        description="קריאה פמיניסטית בארכיון - השקת ספרה של אריז'",
        is_virtual=False,
        event_type="lecture",
        links=[{
            'url': 'https://wordpress.us13.list-manage.com/track/click?u=f65a5e7e35679e023bb1c29fa&id=ffa30d4bfc&e=18dc259e38',
            'label': 'בהזמנה'
        }],
        time_verified=False
    )
    
    print(f"Initial event:")
    print(f"  Title: {test_event.title}")
    print(f"  Time: {test_event.time}")
    print(f"  Duration: {test_event.duration} minutes")
    print(f"  Time Verified: {test_event.time_verified}")
    print(f"  End Time: {test_event.end_time}")
    
    # Initialize processor and enhance event with time extraction
    processor = NewsletterProcessor()
    enhanced_event = processor._enhance_event_with_time(test_event)
    
    print(f"\nAfter time extraction:")
    print(f"  Title: {enhanced_event.title}")
    print(f"  Time: {enhanced_event.time}")
    print(f"  Duration: {enhanced_event.duration} minutes")
    print(f"  Time Verified: {enhanced_event.time_verified}")
    print(f"  End Time: {enhanced_event.end_time}")
    
    # Test calendar integration
    try:
        calendar_handler = CalendarHandler()
        if calendar_handler.authenticate():
            calendar_service = calendar_handler.get_service()
            
            # Create event body (dry run - don't actually create)
            event_body = processor.create_calendar_event(calendar_service, enhanced_event)
            
            if event_body:
                print(f"\n✅ SUCCESS: Calendar event created successfully!")
                print(f"  Summary: {event_body.get('summary')}")
                print(f"  Start: {event_body.get('start')}")
                print(f"  End: {event_body.get('end')}")
                print(f"  Description contains time info: {'✅ זמן מאומת' in event_body.get('description', '')}")
                return True
            else:
                print(f"\n❌ FAILED: Could not create calendar event")
                return False
        else:
            print(f"\n❌ FAILED: Calendar authentication failed")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_time_range_integration()
    print(f"\n{'='*50}")
    print(f"Test {'PASSED' if success else 'FAILED'}") 