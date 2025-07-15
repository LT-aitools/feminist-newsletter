"""
Text parsing utilities for Hebrew newsletter content processing.
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from config import FOOTER_PATTERNS, CITIES, EVENT_TYPES


def normalize_plain_text(content: str) -> str:
    """
    Clean and normalize plain text content from email.
    Based on the existing Apps Script normalizePlainText function.
    """
    clean = content
    
    # Remove content after footer patterns
    for pattern in FOOTER_PATTERNS:
        if pattern in clean:
            clean = clean.split(pattern)[0]
    
    # Remove only specific unwanted tracking/social links
    # Remove Facebook tracking links
    clean = re.sub(r'\[image: Facebook\]\s*<https://wordpress\.us13\.list-manage\.com[^>]*>', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'Facebook\s*\(https://wordpress\.us13\.list-manage\.com[^)]*\)', '', clean, flags=re.IGNORECASE)
    
    # Remove Website tracking links
    clean = re.sub(r'\[image: Website\]\s*<https://wordpress\.us13\.list-manage\.com[^>]*>', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\*\*\s*Website\s*\(https://wordpress\.us13\.list-manage\.com[^)]*\)', '', clean, flags=re.IGNORECASE)
    
    # Remove Email tracking links
    clean = re.sub(r'\[image: Email\]\s*<[^>]*>', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\*\*\s*Email\s*\(mailto:[^)]*\)', '', clean, flags=re.IGNORECASE)
    
    # Remove any remaining [image: Facebook], [image: Website], [image: Email] tags
    clean = re.sub(r'\[image: (Facebook|Website|Email)\]', '', clean, flags=re.IGNORECASE)
    
    # DO NOT remove generic URLs or other [image: ...] tags
    # DO NOT remove <https://...> unless it's part of the above patterns
    
    # Clean up orphaned content and punctuation
    clean = re.sub(r'^\s*[\.\,\;\:]\s*\(https:\/\/[^)]*\)\s*', '', clean)
    clean = re.sub(r'^\s*[\.\,\;\:\)]\s*', '', clean)
    
    # Remove remaining markers and separators
    clean = re.sub(r'\s*\*+\s*$', '', clean)
    clean = re.sub(r'\s*=+\s*$', '', clean)
    
    # Normalize whitespace
    clean = re.sub(r'\r?\n|\r', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean)
    
    return clean.strip()


def extract_event_blocks_from_newsletter(content: str) -> List[str]:
    """
    Extract event blocks from newsletter content.
    Based on the existing Apps Script extractEventBlocksFromNewsletter function.
    """
    # Split by 'ביום' (Hebrew for 'on day') to find event blocks
    blocks = re.split(r'(?=ביום)', content)
    
    # Filter blocks that are long enough and contain date patterns
    valid_blocks = []
    for block in blocks:
        block = block.strip()
        if (len(block) > 15 and 
            re.search(r'\d{1,2}/\d{1,2}', block)):
            valid_blocks.append(block)
    
    return valid_blocks


def extract_date(block: str) -> Optional[datetime]:
    """
    Extract date from event block using Hebrew date format.
    Based on the existing Apps Script extractDate function.
    """
    match = re.search(r'ה(\d{1,2})/(\d{1,2})', block)
    if not match:
        return None
    
    day = int(match.group(1))
    month = int(match.group(2))
    current_year = datetime.now().year
    today = datetime.now()
    
    # Create event date for current year first
    event_date = datetime(current_year, month, day)
    
    # Calculate days difference
    days_diff = (today - event_date).days
    
    # Smart year assignment logic:
    # 1. If the date is in the future or within the last 60 days, use current year
    # 2. If the date is more than 60 days in the past, assume next year
    # 3. Special case: if we're in the first few months of the year and the date is from last year,
    #    but it's within a reasonable range (e.g., December events), keep it as current year
    
    if days_diff > 60:
        # Only assign to next year if it's significantly in the past
        # But be more conservative for newsletter events
        if days_diff > 90:  # More than 3 months in the past
            event_date = datetime(current_year + 1, month, day)
        else:
            # For dates 60-90 days in the past, keep as current year
            # This handles cases like June events when we're in July
            pass
    
    return event_date


def extract_title(block: str) -> str:
    """
    Extract event title from block using multiple patterns.
    Based on the existing Apps Script extractTitle function.
    """
    # Try multiple patterns to extract the title
    
    # Pattern 1: בנושא "title"
    match = re.search(r'בנושא "([^"]+)"', block)
    if match:
        return match.group(1).strip()
    
    # Pattern 2: בנושא 'title'
    match = re.search(r'בנושא \'([^\']+)\'', block)
    if match:
        return match.group(1).strip()
    
    # Pattern 3: בנושא title.
    match = re.search(r'בנושא ([^.]+)\.', block)
    if match:
        return match.group(1).strip()
    
    # Pattern 4: Any quoted text
    match = re.search(r'"([^"]+)"', block)
    if match:
        return match.group(1).strip()
    
    # Pattern 5: Event description after מפגש/הרצאה/דיון
    match = re.search(r'(מפגש|הרצאה|דיון)\s+([^.]+)', block)
    if match:
        return match.group(2).strip()
    
    return 'אירוע זכויות נשים'


def extract_location(block: str) -> str:
    """
    Extract location from event block.
    Based on the existing Apps Script extractLocation function.
    """
    # Check for virtual events
    if re.search(r'וירטואלי|זום|zoom|online', block, re.IGNORECASE):
        return 'וירטואלי'
    
    # Check for Knesset
    if re.search(r'בכנסת|הכנסת', block):
        return 'ירושלים'
    
    # Check for known cities
    for city in CITIES:
        if city in block:
            return city
    
    return ''


def extract_organizer(block: str) -> str:
    """
    Extract organizer from event block.
    Based on the existing Apps Script extractOrganizer function.
    """
    if 'הוועדה לקידום מעמד האישה' in block:
        return 'הוועדה לקידום מעמד האישה'
    return ''


def extract_event_type(block: str) -> str:
    """
    Extract event type from block.
    Based on the existing Apps Script extractEventType function.
    """
    for event_type, hebrew_word in EVENT_TYPES.items():
        if hebrew_word in block:
            return event_type
    return ''


def extract_time_from_text(block: str) -> Optional[str]:
    """
    Extract time information from text block.
    Returns time string if found, None otherwise.
    """
    # Look for time patterns in the text
    time_patterns = [
        r'(\d{1,2}):(\d{2})',  # 19:00
        r'(\d{1,2})\s*:\s*(\d{2})',  # 19 : 00
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, block)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
    
    return None


def create_event_description(event: Dict[str, Any]) -> str:
    """
    Create formatted event description.
    Based on the existing Apps Script createEventDescription function.
    """
    description = event.get('description', '')
    return f"{description}\n\n---\nנוצר אוטומטית מהניוזלטר הפמיניסטי השבועי" 