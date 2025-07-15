import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""
Debug script to print event dates and titles from the 4 most recent processed emails.
"""
import logging
from datetime import datetime, timedelta
from service_account_auth import ServiceAccountAuth
from email_handler import GmailHandler
from newsletter_processor import NewsletterProcessor
from config import get_config

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def print_event_dates_from_recent_emails():
    setup_logging()
    logger = logging.getLogger(__name__)
    config = get_config()
    
    # Auth
    auth = ServiceAccountAuth()
    gmail_handler = GmailHandler()
    user_email = config.get('gmail_account', 'hello@letstalkaitools.com')
    gmail_service = auth.get_gmail_service(user_email)
    gmail_handler.service = gmail_service
    processor = NewsletterProcessor()
    
    # Use the same date logic as main.py
    days_back = 7
    end_date = datetime.now() + timedelta(days=1)
    start_date = datetime.now() - timedelta(days=days_back)
    start_str = start_date.strftime('%Y/%m/%d')
    end_str = end_date.strftime('%Y/%m/%d')
    senders = [config['newsletter_sender'], 'nlevran@gmail.com']
    query = f"({' OR '.join([f'from:{sender}' for sender in senders])}) after:{start_str} before:{end_str}"
    
    logger.info(f"Query: {query}")
    results = gmail_handler.service.users().messages().list(
        userId=user_email,
        q=query,
        maxResults=4
    ).execute()
    messages = results.get('messages', [])
    logger.info(f"Found {len(messages)} recent emails")
    
    for i, message in enumerate(messages):
        email_info = gmail_handler._get_email_details(message['id'])
        subject = email_info.get('subject', 'No subject')
        logger.info(f"\n--- EMAIL {i+1} ---")
        logger.info(f"Subject: {subject}")
        events = processor.process_newsletter_email(
            email_info.get('plain_text', ''),
            email_info.get('html_content', '')
        )
        if not events:
            logger.info("No events found in this email.")
        for event in events:
            logger.info(f"Event: {event.title}")
            logger.info(f"  Date: {event.date.strftime('%Y-%m-%d')}")
            logger.info(f"  Time: {event.time}")
            logger.info(f"  Duration: {event.duration} min")
            logger.info(f"  Location: {event.location}")
            logger.info(f"  Verified: {event.time_verified}")
            logger.info("")

if __name__ == "__main__":
    print_event_dates_from_recent_emails() 