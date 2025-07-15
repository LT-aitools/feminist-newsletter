"""
Debug script to test email filtering logic.
"""
import logging
from datetime import datetime, timedelta
from service_account_auth import ServiceAccountAuth
from email_handler import GmailHandler
from config import get_config

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def debug_email_filtering():
    """Debug the email filtering logic."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    config = get_config()
    
    try:
        logger.info("=== DEBUGGING EMAIL FILTERING ===")
        
        # Initialize service account authentication
        logger.info("Setting up service account authentication...")
        auth = ServiceAccountAuth()
        
        # Initialize Gmail handler
        gmail_handler = GmailHandler()
        user_email = config.get('gmail_account', 'hello@letstalkaitools.com')
        gmail_service = auth.get_gmail_service(user_email)
        gmail_handler.service = gmail_service
        
        # Test different search queries
        search_queries = [
            # Original query
            {
                'name': 'Original query (7 days, both senders)',
                'query': f"(from:{config['newsletter_sender']} OR from:nlevran@gmail.com) after:2025/07/08 before:2025/07/15",
                'maxResults': 50
            },
            # Broader date range
            {
                'name': 'Broader date range (14 days)',
                'query': f"(from:{config['newsletter_sender']} OR from:nlevran@gmail.com) after:2025/07/01 before:2025/07/15",
                'maxResults': 100
            },
            # Just today
            {
                'name': 'Just today',
                'query': f"(from:{config['newsletter_sender']} OR from:nlevran@gmail.com) after:2025/07/15 before:2025/07/16",
                'maxResults': 50
            },
            # All emails from nlevran today
            {
                'name': 'All emails from nlevran today',
                'query': f"from:nlevran@gmail.com after:2025/07/15 before:2025/07/16",
                'maxResults': 50
            },
            # All emails with the subject
            {
                'name': 'All emails with subject containing "מייל פמיניסטי שבועי"',
                'query': f"subject:\"מייל פמיניסטי שבועי\" after:2025/07/15 before:2025/07/16",
                'maxResults': 50
            }
        ]
        
        for search_config in search_queries:
            logger.info(f"\n=== {search_config['name']} ===")
            logger.info(f"Query: {search_config['query']}")
            
            try:
                results = gmail_handler.service.users().messages().list(
                    userId=user_email,
                    q=search_config['query'],
                    maxResults=search_config['maxResults']
                ).execute()
                messages = results.get('messages', [])
                logger.info(f"Found {len(messages)} messages")
                
                if messages:
                    # Get details for first few messages
                    for i, message in enumerate(messages[:5]):  # Show first 5
                        try:
                            email_info = gmail_handler._get_email_details(message['id'])
                            if email_info:
                                sender = email_info['from']
                                subject = email_info.get('subject', 'No subject')
                                date = email_info.get('date', 'No date')
                                logger.info(f"  {i+1}. From: {sender}")
                                logger.info(f"     Subject: {subject}")
                                logger.info(f"     Date: {date}")
                        except Exception as e:
                            logger.error(f"Error getting details for message {message['id']}: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error with query '{search_config['name']}': {str(e)}")
        
        # Now test the actual filtering logic
        logger.info(f"\n=== TESTING ACTUAL FILTERING LOGIC ===")
        
        # Use the original query
        days_back = 7
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_str = start_date.strftime('%Y/%m/%d')
        end_str = end_date.strftime('%Y/%m/%d')
        senders = [config['newsletter_sender'], 'nlevran@gmail.com']
        query = f"({' OR '.join([f'from:{sender}' for sender in senders])}) after:{start_str} before:{end_str}"
        
        logger.info(f"Date range: {start_str} to {end_str}")
        logger.info(f"Searching for recent emails with query: {query}")
        
        results = gmail_handler.service.users().messages().list(
            userId=user_email,
            q=query,
            maxResults=50
        ).execute()
        messages = results.get('messages', [])
        logger.info(f"Found {len(messages)} recent newsletter emails (from any sender)")
        
        # Get full message details and debug filtering
        emails = []
        filtered_out = []
        
        for i, message in enumerate(messages):
            try:
                logger.info(f"Processing message {i+1}/{len(messages)}: {message['id']}")
                email_info = gmail_handler._get_email_details(message['id'])
                
                if email_info:
                    sender = email_info['from'].lower()
                    subject = email_info.get('subject', '')
                    date = email_info.get('date', '')
                    
                    logger.info(f"  From: {sender}")
                    logger.info(f"  Subject: {subject}")
                    logger.info(f"  Date: {date}")
                    
                    # Check filtering logic
                    if sender.startswith('nlevran@gmail.com'):
                        if 'מייל פמיניסטי שבועי' in subject:
                            emails.append(email_info)
                            logger.info(f"  ✅ INCLUDED (nlevran with correct subject)")
                        else:
                            filtered_out.append({
                                'reason': 'nlevran@gmail.com but wrong subject',
                                'sender': sender,
                                'subject': subject,
                                'date': date
                            })
                            logger.info(f"  ❌ FILTERED OUT (nlevran@gmail.com but subject doesn't contain 'מייל פמיניסטי שבועי')")
                    else:
                        emails.append(email_info)
                        logger.info(f"  ✅ INCLUDED (other sender)")
                else:
                    logger.warning(f"  ⚠️ Could not get email details for message {message['id']}")
                    
            except Exception as e:
                logger.error(f"Error getting details for message {message['id']}: {str(e)}")
                continue
        
        logger.info(f"\n=== FILTERING RESULTS ===")
        logger.info(f"Emails included: {len(emails)}")
        logger.info(f"Emails filtered out: {len(filtered_out)}")
        
        if filtered_out:
            logger.info(f"\n=== FILTERED OUT EMAILS ===")
            for i, email in enumerate(filtered_out):
                logger.info(f"{i+1}. Reason: {email['reason']}")
                logger.info(f"   From: {email['sender']}")
                logger.info(f"   Subject: {email['subject']}")
                logger.info(f"   Date: {email['date']}")
                logger.info("")
        
        if emails:
            logger.info(f"\n=== INCLUDED EMAILS ===")
            for i, email in enumerate(emails):
                logger.info(f"{i+1}. From: {email['from']}")
                logger.info(f"   Subject: {email.get('subject', 'No subject')}")
                logger.info(f"   Date: {email.get('date', 'No date')}")
                logger.info("")
        
    except Exception as e:
        logger.error(f"Critical error during debugging: {str(e)}")

if __name__ == "__main__":
    debug_email_filtering() 