"""
Test script to process the latest newsletter email with updated time extraction.
"""
import logging
from datetime import datetime, timedelta
from newsletter_processor import NewsletterProcessor
from email_handler import GmailHandler
from calendar_handler import CalendarHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_latest_newsletter():
    """Process the latest newsletter email with time extraction."""
    
    print("Testing Latest Newsletter with Time Extraction")
    print("=" * 60)
    
    try:
        # Initialize handlers
        gmail_handler = GmailHandler()
        calendar_handler = CalendarHandler()
        processor = NewsletterProcessor()
        
        # Authenticate with Gmail
        print("Authenticating with Gmail...")
        if not gmail_handler.authenticate():
            print("❌ Failed to authenticate with Gmail")
            return False
        
        # Authenticate with Calendar
        print("Authenticating with Calendar...")
        if not calendar_handler.authenticate():
            print("❌ Failed to authenticate with Calendar")
            return False
        
        # Get the latest newsletter email
        print("Fetching latest newsletter email...")
        latest_email = gmail_handler.get_latest_newsletter_email()
        
        if not latest_email:
            print("❌ No newsletter email found")
            return False
        
        print(f"✅ Found newsletter: {latest_email['subject']}")
        print(f"   Date: {latest_email['date']}")
        print(f"   From: {latest_email['from']}")
        
        # Process the newsletter
        print("\nProcessing newsletter with time extraction...")
        events = processor.process_newsletter_email(
            email_content=latest_email['body'],
            html_content=latest_email.get('html_body')
        )
        
        if not events:
            print("❌ No events found in newsletter")
            return False
        
        print(f"✅ Found {len(events)} events in newsletter")
        
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
            else:
                print(f"   ❌ Failed to create calendar event")
        
        print(f"\n{'='*60}")
        print(f"Newsletter Processing Complete!")
        print(f"Events found: {len(events)}")
        print(f"Events created: {created_count}")
        print(f"Time extraction working: ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing newsletter: {str(e)}")
        logging.exception("Detailed error information:")
        return False

if __name__ == "__main__":
    success = test_latest_newsletter()
    print(f"\nTest {'PASSED' if success else 'FAILED'}") 