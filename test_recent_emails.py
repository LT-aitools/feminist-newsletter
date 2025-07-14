"""
Test script to process recent newsletter emails and test the improved text cleaning.
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from newsletter_processor import NewsletterProcessor
from email_handler import GmailHandler
from calendar_handler import CalendarHandler
from config import get_config


def setup_logging():
    """Configure logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_recent_emails():
    """
    Test processing recent newsletter emails to verify text cleaning improvements.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    config = get_config()
    
    # Initialize processing statistics
    stats = {
        'emails_processed': 0,
        'events_created': 0,
        'events_skipped': 0,
        'events_failed': 0,
        'processing_time': 0,
        'errors': []
    }
    
    start_time = datetime.now()
    
    try:
        logger.info("=== TESTING RECENT EMAILS PROCESSING ===")
        
        # Initialize handlers
        gmail_handler = GmailHandler()
        calendar_handler = CalendarHandler()
        newsletter_processor = NewsletterProcessor()
        
        # Authenticate with APIs
        logger.info("Authenticating with Gmail API...")
        if not gmail_handler.authenticate():
            raise RuntimeError("Failed to authenticate with Gmail API")
        
        logger.info("Authenticating with Calendar API...")
        if not calendar_handler.authenticate():
            raise RuntimeError("Failed to authenticate with Calendar API")
        
        # Try to get all unread emails from nlevran@gmail.com
        logger.info("Searching for all unread emails from nlevran@gmail.com...")
        query = "from:nlevran@gmail.com is:unread"
        results = gmail_handler.service.users().messages().list(
            userId='me',
            q=query,
            maxResults=50
        ).execute()
        messages = results.get('messages', [])
        logger.info(f"Found {len(messages)} unread emails from nlevran@gmail.com")
        
        # Get full message details and log subjects
        emails = []
        for message in messages:
            try:
                email_info = gmail_handler._get_email_details(message['id'])
                logger.info(f"Email subject: {email_info.get('subject', '')}")
                if email_info and 'מייל פמיניסטי שבועי' in email_info.get('subject', ''):
                    emails.append(email_info)
            except Exception as e:
                logger.error(f"Error getting details for message {message['id']}: {str(e)}")
                continue
        logger.info(f"Found {len(emails)} relevant unread forwarded emails to process.")
        
        if not emails:
            logger.info("No relevant unread forwarded emails found")
            stats['processing_time'] = (datetime.now() - start_time).total_seconds()
            return create_response(stats, "No emails to process")
        
        stats['emails_processed'] = len(emails)
        
        # Process each email
        for i, email in enumerate(emails):
            try:
                logger.info(f"Processing email {i+1}/{len(emails)}: {email.get('subject', 'No subject')}")
                
                # Process newsletter content
                events = newsletter_processor.process_newsletter_email(
                    email.get('plain_text', ''),
                    email.get('html_content', '')
                )
                
                logger.info(f"Extracted {len(events)} events from email")
                
                # Process each event
                for j, event in enumerate(events):
                    try:
                        logger.info(f"Processing event {j+1}/{len(events)}: {event.title}")
                        
                        # Check for duplicates
                        duplicate = calendar_handler.check_for_duplicate_event(event.title, event.date)
                        if duplicate:
                            logger.info(f"Skipping duplicate event: {event.title}")
                            stats['events_skipped'] += 1
                            continue
                        
                        # Create calendar event
                        event_data = create_event_body(event, config)
                        created_event = calendar_handler.create_event(event_data)
                        
                        if created_event:
                            logger.info(f"Successfully created event: {created_event.get('summary')}")
                            stats['events_created'] += 1
                        else:
                            logger.error(f"Failed to create event: {event.title}")
                            stats['events_failed'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing event {j+1}: {str(e)}")
                        stats['events_failed'] += 1
                        stats['errors'].append(f"Event processing error: {str(e)}")
                        continue
                
            except Exception as e:
                logger.error(f"Error processing email {i+1}: {str(e)}")
                stats['errors'].append(f"Email processing error: {str(e)}")
                continue
        
        # Calculate processing time
        stats['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        # Log summary
        logger.info("=== PROCESSING SUMMARY ===")
        logger.info(f"Emails processed: {stats['emails_processed']}")
        logger.info(f"Events created: {stats['events_created']}")
        logger.info(f"Events skipped: {stats['events_skipped']}")
        logger.info(f"Events failed: {stats['events_failed']}")
        logger.info(f"Processing time: {stats['processing_time']:.2f} seconds")
        
        if stats['errors']:
            logger.warning(f"Errors encountered: {len(stats['errors'])}")
            for error in stats['errors']:
                logger.warning(f"  - {error}")
        
        return create_response(stats, "Processing completed successfully")
        
    except Exception as e:
        logger.error(f"Critical error in newsletter processing: {str(e)}")
        stats['processing_time'] = (datetime.now() - start_time).total_seconds()
        stats['errors'].append(f"Critical error: {str(e)}")
        return create_response(stats, f"Processing failed: {str(e)}", status_code=500)


def create_event_body(event, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create the event body for Google Calendar API.
    """
    
    # Combine date and time
    start_datetime = event.date.replace(
        hour=int(event.time.split(':')[0]),
        minute=int(event.time.split(':')[1]),
        second=0,
        microsecond=0
    )
    
    # Calculate end time
    end_datetime = start_datetime + timedelta(minutes=event.duration)
    
    # Create event body
    event_body = {
        'summary': event.title,
        'description': create_event_description(event),
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': config['timezone']
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': config['timezone']
        }
    }
    
    # Add location if available
    if event.location:
        event_body['location'] = event.location
    
    # Add organizer if available
    if event.organizer:
        event_body['description'] += f"\n\nמארגן: {event.organizer}"
    
    # Add links if available
    if event.links:
        links_text = "\n\nקישורים רלוונטיים:\n"
        for link in event.links:
            links_text += f"🔗 {link['label']}: {link['url']}\n"
        event_body['description'] += links_text
    
    return event_body


def create_event_description(event) -> str:
    """
    Create formatted event description.
    """
    description = event.description
    return f"{description}\n\n---\nנוצר אוטומטית מהניוזלטר הפמיניסטי השבועי"


def create_response(stats: Dict[str, Any], message: str, status_code: int = 200) -> Dict[str, Any]:
    """
    Create a standardized response.
    """
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'statistics': stats
        }, ensure_ascii=False),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }


# For testing
if __name__ == "__main__":
    result = test_recent_emails()
    print(json.dumps(result, indent=2, ensure_ascii=False)) 