"""
Main Cloud Function entry point for newsletter automation.
"""
import logging
import json
from typing import Dict, Any
from datetime import datetime

from newsletter_processor import NewsletterProcessor, EventData
from email_handler import GmailHandler
from calendar_handler import CalendarHandler
from config import get_config


def setup_logging():
    """Configure logging for the Cloud Function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def newsletter_processor(request):
    """
    Main Cloud Function entry point.
    Triggered weekly by Cloud Scheduler.
    
    Args:
        request: Flask request object (for HTTP triggers)
    
    Returns:
        JSON response with processing summary
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
    
    # Get last processed date from environment variable
    import os
    last_processed_date = os.getenv('LAST_PROCESSED_DATE', 'Never')
    logger.info(f"Last processed date: {last_processed_date}")
    
    start_time = datetime.now()
    
    try:
        logger.info("=== STARTING NEWSLETTER PROCESSING ===")
        
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
        
        # Get unread newsletter emails
        logger.info("Fetching unread newsletter emails...")
        emails = gmail_handler.get_unread_newsletters()
        
        if not emails:
            logger.info("No unread newsletter emails found")
            stats['processing_time'] = (datetime.now() - start_time).total_seconds()
            return create_response(stats, "No emails to process")
        
        logger.info(f"Found {len(emails)} unread newsletter emails")
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
                
                # Mark email as processed (if write permissions available)
                gmail_handler.mark_as_processed(email['id'])
                
            except Exception as e:
                logger.error(f"Error processing email {i+1}: {str(e)}")
                stats['errors'].append(f"Email processing error: {str(e)}")
                continue
        
        # Calculate processing time
        stats['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        # Update last processed date if emails were processed
        if stats['emails_processed'] > 0:
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"🎯 EMAILS PROCESSED - Last processed date: {current_date}")
            stats['last_processed_date'] = current_date
        else:
            logger.info(f"📭 No emails processed - Last processed date: {last_processed_date}")
            stats['last_processed_date'] = last_processed_date
        
        # Log summary
        logger.info("=== PROCESSING SUMMARY ===")
        logger.info(f"Emails processed: {stats['emails_processed']}")
        logger.info(f"Events created: {stats['events_created']}")
        logger.info(f"Events skipped: {stats['events_skipped']}")
        logger.info(f"Events failed: {stats['events_failed']}")
        logger.info(f"Processing time: {stats['processing_time']:.2f} seconds")
        logger.info(f"Last processed date: {last_processed_date}")
        
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


def create_event_body(event: EventData, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create the event body for Google Calendar API.
    """
    from datetime import timedelta
    
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


def create_event_description(event: EventData) -> str:
    """
    Create formatted event description.
    """
    description = event.description
    return f"{description}\n\n---\nנוצר אוטומטית מהניוזלטר הפמיניסטי השבועי"


def create_response(stats: Dict[str, Any], message: str, status_code: int = 200) -> Dict[str, Any]:
    """
    Create a standardized response for the Cloud Function.
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


# For local testing
if __name__ == "__main__":
    # Simulate a Cloud Function request
    class MockRequest:
        pass
    
    request = MockRequest()
    result = newsletter_processor(request)
    print(json.dumps(result, indent=2, ensure_ascii=False)) 