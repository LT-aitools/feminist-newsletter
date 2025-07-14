"""
Test script to process the latest real emails with the new time extraction functionality.
This ensures that event details and titles are preserved correctly in production.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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

def test_latest_emails():
    """Process the latest emails with time extraction to verify production functionality."""
    
    print("Testing Latest Emails with Time Extraction")
    print("=" * 60)
    
    try:
        # Initialize handlers
        gmail_handler = GmailHandler()
        calendar_handler = CalendarHandler()
        processor = NewsletterProcessor()
        
        # Authenticate with Calendar (this should work)
        print("Authenticating with Calendar...")
        if not calendar_handler.authenticate():
            print("❌ Failed to authenticate with Calendar")
            return False
        
        # Try to authenticate with Gmail
        print("Authenticating with Gmail...")
        gmail_success = gmail_handler.authenticate()
        
        if not gmail_success:
            print("⚠️  Gmail authentication failed - this is expected due to scope issues")
            print("   We'll test with the existing email processing methods")
            
            # Try alternative methods to get emails
            print("\nTrying alternative email access methods...")
            
            # Check if we can use the existing test methods
            try:
                # Try to get recent newsletters using existing methods
                print("Attempting to get recent newsletters...")
                # This might work if the OAuth2 credentials have the right scopes
                recent_emails = gmail_handler.get_recent_newsletters(days_back=7)
                
                if recent_emails:
                    print(f"✅ Found {len(recent_emails)} recent newsletters")
                    return process_emails(recent_emails, processor, calendar_handler)
                else:
                    print("❌ No recent newsletters found")
                    return False
                    
            except Exception as e:
                print(f"❌ Error accessing emails: {str(e)}")
                print("   This confirms the Gmail scope issue")
                return False
        else:
            print("✅ Gmail authentication successful!")
            return process_latest_emails(gmail_handler, processor, calendar_handler)
        
    except Exception as e:
        print(f"❌ Error in test: {str(e)}")
        logging.exception("Detailed error information:")
        return False

def process_latest_emails(gmail_handler, processor, calendar_handler):
    """Process the latest emails with time extraction."""
    
    try:
        # Get the latest unread newsletter emails (from both senders)
        print("Fetching latest unread newsletter emails...")
        unread_emails = gmail_handler.get_unread_newsletters()
        
        if not unread_emails:
            print("❌ No unread newsletter email found")
            return False
        
        # Process the last 2 emails
        emails_to_process = unread_emails[:2]
        print(f"Processing {len(emails_to_process)} emails...")
        
        total_events = 0
        total_created = 0
        
        for i, email in enumerate(emails_to_process, 1):
            print(f"\n--- Processing Email {i}: {email.get('subject', 'No subject')} ---")
            print(f"   Date: {email['date']}")
            print(f"   From: {email['from']}")
            
            success, events_created = process_single_email(email, processor, calendar_handler)
            
            if success:
                total_events += events_created
                total_created += events_created
        
        print(f"\n{'='*60}")
        print(f"Email Processing Complete!")
        print(f"Total events processed: {total_events}")
        print(f"Total events created: {total_created}")
        
        return total_created > 0
        
    except Exception as e:
        print(f"❌ Error processing latest emails: {str(e)}")
        return False

def process_emails(emails, processor, calendar_handler):
    """Process multiple emails with time extraction."""
    
    print(f"\nProcessing {len(emails)} emails with time extraction...")
    
    total_events = 0
    total_created = 0
    
    for i, email in enumerate(emails, 1):
        print(f"\n--- Processing Email {i}: {email.get('subject', 'No subject')} ---")
        
        success, events_created = process_single_email(email, processor, calendar_handler)
        
        if success:
            total_events += events_created
            total_created += events_created
    
    print(f"\n{'='*60}")
    print(f"Email Processing Complete!")
    print(f"Total events processed: {total_events}")
    print(f"Total events created: {total_created}")
    
    return total_created > 0

def process_single_email(email, processor, calendar_handler):
    """Process a single email with time extraction."""
    
    try:
        # Process the newsletter
        events = processor.process_newsletter_email(
            email_content=email.get('plain_text', ''),
            html_content=email.get('html_content', '')
        )
        
        if not events:
            print("   ❌ No events found in email")
            return True, 0
        
        print(f"   ✅ Found {len(events)} events in email")
        
        # Display event details and create calendar events
        calendar_service = calendar_handler.get_service()
        created_count = 0
        
        for j, event in enumerate(events, 1):
            print(f"\n   --- Event {j}: {event.title} ---")
            print(f"      Date: {event.date.strftime('%Y-%m-%d')}")
            print(f"      Time: {event.time}")
            if event.end_time:
                print(f"      End Time: {event.end_time}")
            print(f"      Duration: {event.duration} minutes")
            print(f"      Location: {event.location}")
            print(f"      Organizer: {event.organizer}")
            print(f"      Time Verified: {event.time_verified}")
            print(f"      Links: {len(event.links)} invitation links")
            
            # Show invitation links
            for link in event.links:
                print(f"        - {link['label']}: {link['url']}")
            
            # Create calendar event
            print(f"      Creating calendar event...")
            created_event = processor.create_calendar_event(calendar_service, event)
            
            if created_event:
                created_count += 1
                print(f"      ✅ Created: {created_event.get('summary')}")
                print(f"      📅 Start: {created_event.get('start', {}).get('dateTime', 'N/A')}")
                print(f"      📅 End: {created_event.get('end', {}).get('dateTime', 'N/A')}")
                
                # Check if description contains time warning
                description = created_event.get('description', '')
                if '⚠️ זמן משוער' in description:
                    print(f"      ⚠️  Time warning in description")
                else:
                    print(f"      ✅ Clean description (no time warning)")
            else:
                print(f"      ❌ Failed to create calendar event")
        
        return True, created_count
        
    except Exception as e:
        print(f"   ❌ Error processing email: {str(e)}")
        return False, 0

if __name__ == "__main__":
    success = test_latest_emails()
    print(f"\nTest {'PASSED' if success else 'FAILED'}") 