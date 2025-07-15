"""
Test script to process recent newsletter emails regardless of read status, for both main and backup senders.
"""
import logging
from datetime import datetime, timedelta

from newsletter_processor import NewsletterProcessor, EventData
from email_handler import GmailHandler
from calendar_handler import CalendarHandler
from config import get_config


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_recent_emails():
    """Test processing recent newsletter emails (not just unread)."""
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
        logger.info("=== TESTING RECENT NEWSLETTER PROCESSING ===")
        
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
        
        # Get recent newsletter emails (last 7 days, regardless of read status) from both senders
        days_back = 7
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_str = start_date.strftime('%Y/%m/%d')
        end_str = end_date.strftime('%Y/%m/%d')
        senders = [config['newsletter_sender'], 'nlevran@gmail.com']
        query = f"({' OR '.join([f'from:{sender}' for sender in senders])}) after:{start_str} before:{end_str}"
        logger.info(f"Searching for recent emails with query: {query}")
        results = gmail_handler.service.users().messages().list(
            userId='me',
            q=query,
            maxResults=50
        ).execute()
        messages = results.get('messages', [])
        logger.info(f"Found {len(messages)} recent newsletter emails (from any sender)")
        
        # Get full message details
        emails = []
        for message in messages:
            try:
                email_info = gmail_handler._get_email_details(message['id'])
                if email_info:
                    sender = email_info['from'].lower()
                    subject = email_info.get('subject', '')
                    if sender.startswith('nlevran@gmail.com'):
                        if 'מייל פמיניסטי שבועי' in subject:
                            emails.append(email_info)
                    else:
                        emails.append(email_info)
            except Exception as e:
                logger.error(f"Error getting details for message {message['id']}: {str(e)}")
                continue
        
        if not emails:
            logger.info("No recent newsletter emails found")
            stats['processing_time'] = (datetime.now() - start_time).total_seconds()
            return stats
        
        logger.info(f"Processing {len(emails)} filtered recent newsletter emails")
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
        
        return stats
        
    except Exception as e:
        logger.error(f"Critical error in newsletter processing: {str(e)}")
        stats['processing_time'] = (datetime.now() - start_time).total_seconds()
        stats['errors'].append(f"Critical error: {str(e)}")
        return stats


def create_event_body(event: EventData, config: dict) -> dict:
    """Create the event body for Google Calendar API."""
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
    
    return event_body


def create_event_description(event: EventData) -> str:
    """Create event description with source information."""
    description = f"Source: Feminist Newsletter\n"
    if event.description:
        description += f"\n{event.description}\n"
    if event.link:
        description += f"\nInvitation link: {event.link}"
    return description


if __name__ == "__main__":
    result = test_recent_emails()
    print(f"\nFinal result: {result}") 