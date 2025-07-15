import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""
Debug script to test date extraction for June dates.
"""
import logging
from datetime import datetime, timedelta
from text_parser import extract_date, extract_event_blocks_from_newsletter
from service_account_auth import ServiceAccountAuth
from email_handler import GmailHandler
from newsletter_processor import NewsletterProcessor
from config import get_config

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def debug_june_dates():
    setup_logging()
    logger = logging.getLogger(__name__)
    config = get_config()
    
    try:
        logger.info("=== DEBUGGING JUNE DATES ===")
        
        # Initialize handlers with service account authentication
        logger.info("Setting up service account authentication...")
        auth = ServiceAccountAuth()
        
        # Verify service account is working
        if not auth.credentials:
            raise RuntimeError("Failed to initialize service account credentials")
        
        logger.info(f"Using service account: {auth.credentials.service_account_email}")
        
        # Initialize handlers with service account
        gmail_handler = GmailHandler()
        
        # Set up service account authentication
        logger.info("Authenticating with Gmail API...")
        user_email = config.get('gmail_account', 'hello@letstalkaitools.com')
        gmail_service = auth.get_gmail_service(user_email)
        gmail_handler.service = gmail_service
        
        # Get recent emails
        days_back = 7
        end_date = datetime.now() + timedelta(days=1)
        start_date = datetime.now() - timedelta(days=days_back)
        start_str = start_date.strftime('%Y/%m/%d')
        end_str = end_date.strftime('%Y/%m/%d')
        senders = [config['newsletter_sender'], 'nlevran@gmail.com']
        query = f"({' OR '.join([f'from:{sender}' for sender in senders])}) after:{start_str} before:{end_str}"
        
        logger.info(f"Searching for recent emails with query: {query}")
        results = gmail_handler.service.users().messages().list(
            userId=user_email,
            q=query,
            maxResults=50
        ).execute()
        messages = results.get('messages', [])
        
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
        
        logger.info(f"Found {len(emails)} emails to process")
        
        # Process each email
        for i, email in enumerate(emails):
            logger.info(f"\n=== EMAIL {i+1} ===")
            logger.info(f"Subject: {email.get('subject', 'No subject')}")
            
            # Extract event blocks
            plain_text = email.get('plain_text', '')
            event_blocks = extract_event_blocks_from_newsletter(plain_text)
            logger.info(f"Found {len(event_blocks)} event blocks")
            
            # Test date extraction for each block
            for j, block in enumerate(event_blocks):
                logger.info(f"\n--- BLOCK {j+1} ---")
                logger.info(f"Block preview: {block[:100]}...")
                
                # Extract date
                date = extract_date(block)
                if date:
                    logger.info(f"✅ Extracted date: {date.strftime('%Y-%m-%d')}")
                    
                    # Check if it's a June date
                    if date.month == 6:
                        logger.info(f"🎯 JUNE DATE FOUND: {date.strftime('%Y-%m-%d')}")
                        
                        # Check if it's being assigned to next year
                        current_year = datetime.now().year
                        if date.year == current_year + 1:
                            logger.warning(f"⚠️ June date assigned to next year: {date.strftime('%Y-%m-%d')}")
                        else:
                            logger.info(f"✅ June date assigned to current year: {date.strftime('%Y-%m-%d')}")
                    else:
                        logger.info(f"📅 Non-June date: {date.strftime('%Y-%m-%d')}")
                else:
                    logger.warning(f"❌ No date extracted from block")
                    
                    # Show what patterns we're looking for
                    import re
                    match = re.search(r'ה(\d{1,2})/(\d{1,2})', block)
                    if match:
                        logger.info(f"🔍 Found date pattern: ה{match.group(1)}/{match.group(2)}")
                    else:
                        logger.info(f"🔍 No date pattern found in block")
                        
    except Exception as e:
        logger.error(f"Error in debug_june_dates: {str(e)}")
        raise

if __name__ == "__main__":
    debug_june_dates() 