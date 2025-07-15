"""
Configuration settings for the newsletter automation system.
"""
import os
from typing import Dict, Any

# Core Configuration
CONFIG: Dict[str, Any] = {
    'calendar_name': 'Feminist Newsletter Events',
    'calendar_id': '5b6f7ad099565ddfa52d0bfe297cedc40ea0321360104f2b61782b5e69480270@group.calendar.google.com',
    'test_calendar_id': 'c1745d57a6fcefc58c38ea8d81a44075e01cd619485db9eda00441a03362eb7b@group.calendar.google.com',
    'use_test_calendar': False,  # Set to False for production, True for demo/testing
    'use_service_account': True,  # Use service account for Gmail and Vision APIs
    'timezone': 'Asia/Jerusalem',
    'newsletter_sender': 'sharon.orsh@56456773.mailchimpapp.com',
    'gmail_account': 'hello@letstalkaitools.com',  # Account that owns the calendar
    'processed_label_name': 'WomensRightsProcessed',
    'default_duration': 120,  # 2 hours in minutes
    'default_start_time': '19:00',
    'max_emails_to_process': 10,
    'skip_past_events': True
}

# Environment Variables (for Cloud Functions)
def get_config() -> Dict[str, Any]:
    """Get configuration with environment variable overrides."""
    config = CONFIG.copy()
    
    # Override with environment variables if present
    config['calendar_name'] = os.getenv('CALENDAR_NAME', config['calendar_name'])
    config['timezone'] = os.getenv('TIMEZONE', config['timezone'])
    config['newsletter_sender'] = os.getenv('GMAIL_SENDER_EMAIL', config['newsletter_sender'])
    config['default_duration'] = int(os.getenv('DEFAULT_EVENT_DURATION', config['default_duration']))
    config['default_start_time'] = os.getenv('DEFAULT_START_TIME', config['default_start_time'])
    config['max_emails_to_process'] = int(os.getenv('MAX_EMAILS_TO_PROCESS', config['max_emails_to_process']))
    
    return config

# Hebrew Time Patterns for OCR extraction
TIME_PATTERNS = [
    r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})',  # 19:00-21:00
    r'(\d{1,2})\s*:\s*(\d{2})\s*-\s*(\d{1,2})\s*:\s*(\d{2})',  # 19 : 00 - 21 : 00
    r'מ(\d{1,2}):(\d{2})\s*עד\s*(\d{1,2}):(\d{2})',  # Hebrew format
    r'(\d{1,2}):(\d{2})',  # Single time
]

# Event Types
EVENT_TYPES = {
    'discussion': 'דיון',
    'lecture': 'הרצאה', 
    'meeting': 'מפגש'
}

# Cities for location detection
CITIES = ['תל אביב', 'ירושלים', 'חיפה', 'באר שבע']

# Footer patterns to remove from email content
FOOTER_PATTERNS = [
    'This email was sent to',
    'Want to change how you receive',
    'Facebook (https://',
    '** Website (https://',
    '** Email (mailto:',
    'Facebook (http://',
    'Website (https://',
    'Email (mailto:',
    'Copyright ©',
    'Our mailing address is:',
    'unsubscribe from this list',
    '============================================================='
] 