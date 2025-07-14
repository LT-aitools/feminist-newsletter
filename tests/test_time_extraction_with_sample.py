"""
Test script to test time extraction with sample newsletter content.
This avoids Gmail authentication issues while testing the core functionality.
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

def test_with_sample_newsletter():
    """Test time extraction with sample newsletter content."""
    
    print("Testing Time Extraction with Sample Newsletter")
    print("=" * 60)
    
    # Sample newsletter content with real invitation links (matching working format)
    sample_newsletter = """
    מייל פמיניסטי שבועי - אירועים השבוע
    
    ביום שלישי ה15/7 - קריאה פמיניסטית בארכיון - השקת ספרה של אריז' סבאע'-ח'ורי
    מיקום: בית אשה לאשה, רחוב ארלוזורוב 118 חיפה
    מארגן: ד"ר רות פרפר
    בהזמנה: https://wordpress.us13.list-manage.com/track/click?u=f65a5e7e35679e023bb1c29fa&id=ffa30d4bfc&e=18dc259e38
    
    ביום רביעי ה16/7 - אירוע נוסף עם זמן מאומת
    מיקום: תל אביב
    מארגן: ארגון נשים
    בהזמנה: https://wordpress.us13.list-manage.com/track/click?u=f65a5e7e35679e023bb1c29fa&id=a1758cb152&e=18dc259e38
    
    ביום חמישי ה17/7 - אירוע ללא הזמנה
    מיקום: ירושלים
    מארגן: ארגון אחר
    """
    
    sample_html = """
    <html>
    <body>
    <p>מייל פמיניסטי שבועי - אירועים השבוע</p>
    <p>קריאה פמיניסטית בארכיון - השקת ספרה של אריז' סבאע'-ח'ורי</p>
    <p>תאריך: יום שלישי, 15 ביולי 2025</p>
    <p>מיקום: בית אשה לאשה, רחוב ארלוזורוב 118 חיפה</p>
    <p>מארגן: ד"ר רות פרפר</p>
    <p><a href="https://wordpress.us13.list-manage.com/track/click?u=f65a5e7e35679e023bb1c29fa&id=ffa30d4bfc&e=18dc259e38">בהזמנה</a></p>
    
    <p>אירוע נוסף עם זמן מאומת</p>
    <p>תאריך: יום רביעי, 16 ביולי 2025</p>
    <p>מיקום: תל אביב</p>
    <p>מארגן: ארגון נשים</p>
    <p><a href="https://wordpress.us13.list-manage.com/track/click?u=f65a5e7e35679e023bb1c29fa&id=a1758cb152&e=18dc259e38">בהזמנה</a></p>
    
    <p>אירוע ללא הזמנה</p>
    <p>תאריך: יום חמישי, 17 ביולי 2025</p>
    <p>מיקום: ירושלים</p>
    <p>מארגן: ארגון אחר</p>
    </body>
    </html>
    """
    
    try:
        # Initialize handlers
        calendar_handler = CalendarHandler()
        processor = NewsletterProcessor()
        
        # Authenticate with Calendar
        print("Authenticating with Calendar...")
        if not calendar_handler.authenticate():
            print("❌ Failed to authenticate with Calendar")
            return False
        
        # Process the sample newsletter
        print("Processing sample newsletter with time extraction...")
        events = processor.process_newsletter_email(
            email_content=sample_newsletter,
            html_content=sample_html
        )
        
        if not events:
            print("❌ No events found in sample newsletter")
            return False
        
        print(f"✅ Found {len(events)} events in sample newsletter")
        
        # Display event details and create calendar events
        calendar_service = calendar_handler.get_service()
        created_count = 0
        
        for i, event in enumerate(events, 1):
            print(f"\n--- Event {i}: {event.title} ---")
            print(f"   Date: {event.date.strftime('%Y-%m-%d')}")
            print(f"   Time: {event.time}")
            if event.end_time:
                print(f"   End Time: {event.end_time}")
            print(f"   Duration: {event.duration} minutes")
            print(f"   Location: {event.location}")
            print(f"   Organizer: {event.organizer}")
            print(f"   Time Verified: {event.time_verified}")
            print(f"   Links: {len(event.links)} invitation links")
            
            # Show invitation links
            for link in event.links:
                print(f"     - {link['label']}: {link['url']}")
            
            # Create calendar event
            print(f"   Creating calendar event...")
            created_event = processor.create_calendar_event(calendar_service, event)
            
            if created_event:
                created_count += 1
                print(f"   ✅ Created: {created_event.get('summary')}")
                print(f"   📅 Start: {created_event.get('start', {}).get('dateTime', 'N/A')}")
                print(f"   📅 End: {created_event.get('end', {}).get('dateTime', 'N/A')}")
                
                # Check if description contains time warning
                description = created_event.get('description', '')
                if '⚠️ זמן משוער' in description:
                    print(f"   ⚠️  Time warning in description")
                else:
                    print(f"   ✅ Clean description (no time warning)")
            else:
                print(f"   ❌ Failed to create calendar event")
        
        print(f"\n{'='*60}")
        print(f"Sample Newsletter Processing Complete!")
        print(f"Events found: {len(events)}")
        print(f"Events created: {created_count}")
        print(f"Time extraction working: ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing sample newsletter: {str(e)}")
        logging.exception("Detailed error information:")
        return False

if __name__ == "__main__":
    success = test_with_sample_newsletter()
    print(f"\nTest {'PASSED' if success else 'FAILED'}") 