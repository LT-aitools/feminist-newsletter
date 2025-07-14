"""
Core newsletter processing logic for extracting and parsing events.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from config import get_config
from text_parser import (
    normalize_plain_text,
    extract_event_blocks_from_newsletter,
    extract_date,
    extract_title,
    extract_location,
    extract_organizer,
    extract_event_type,
    extract_time_from_text,
    create_event_description
)


@dataclass
class EventData:
    """Data structure for parsed event information."""
    title: str
    date: datetime
    time: str
    duration: int
    location: str
    organizer: str
    description: str
    is_virtual: bool
    event_type: str
    links: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.links is None:
            self.links = []


class NewsletterProcessor:
    """Main processor for newsletter content."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
    
    def process_newsletter_email(self, email_content: str, html_content: str = None) -> List[EventData]:
        """
        Process newsletter email and extract event information.
        Based on the existing Apps Script processTwoEmailsPlainText function.
        """
        self.logger.info("Processing newsletter email")
        
        # Normalize plain text content
        plain_text = normalize_plain_text(email_content)
        self.logger.debug(f"Normalized text length: {len(plain_text)}")
        
        # Extract links from HTML if available
        links = []
        if html_content:
            links = self._extract_links_from_html(html_content)
            self.logger.info(f"Extracted {len(links)} links from HTML")
        
        # Extract event blocks
        event_blocks = extract_event_blocks_from_newsletter(plain_text)
        self.logger.info(f"Found {len(event_blocks)} event blocks")
        
        # Parse each event block
        events = []
        for i, block in enumerate(event_blocks):
            try:
                event = self._parse_event_block(block, links)
                if event:
                    events.append(event)
                    self.logger.info(f"Parsed event {i+1}: {event.title}")
            except Exception as e:
                self.logger.error(f"Failed to parse event block {i+1}: {str(e)}")
                continue
        
        return events
    
    def _extract_links_from_html(self, html_content: str) -> List[Dict[str, str]]:
        """
        Extract relevant links from HTML content.
        Based on the existing Apps Script link extraction logic.
        """
        import re
        
        links = []
        # Look for links with 'בהזמנה' or 'בלינק' in the text
        pattern = r'href=[\'"]([^\'"]+)[\'"][^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html_content)
        
        for url, label in matches:
            label = label.strip()
            if 'בהזמנה' in label or 'בלינק' in label:
                links.append({
                    'url': url,
                    'label': label
                })
        
        return links
    
    def _parse_event_block(self, block: str, links: List[Dict[str, str]]) -> Optional[EventData]:
        """
        Parse a single event block into EventData.
        Based on the existing Apps Script parseEventBlock function.
        """
        try:
            # Extract basic event information
            date = extract_date(block)
            if not date:
                raise ValueError("No valid date found in event block")
            
            title = extract_title(block)
            location = extract_location(block)
            organizer = extract_organizer(block)
            event_type = extract_event_type(block)
            
            # Check if event is virtual
            is_virtual = 'וירטואלי' in location or any(
                word in block.lower() for word in ['וירטואלי', 'זום', 'zoom', 'online']
            )
            
            # Extract time information
            time = extract_time_from_text(block)
            if not time:
                time = self.config['default_start_time']
                # Add note to title if no time found
                if not any(word in block for word in ['19:00', '20:00', '21:00', '18:00']):
                    title += ' (זמן מדויק של האירוע בזימון)'
            
            # Find matching links for this event
            matching_links = []
            for link in links:
                if link['label'] in block:
                    matching_links.append(link)
            
            # Create event data
            event = EventData(
                title=title,
                date=date,
                time=time,
                duration=self.config['default_duration'],
                location=location,
                organizer=organizer,
                description=block,
                is_virtual=is_virtual,
                event_type=event_type,
                links=matching_links
            )
            
            return event
            
        except Exception as e:
            self.logger.error(f"Error parsing event block: {str(e)}")
            self.logger.debug(f"Block content: {block[:200]}...")
            return None
    
    def enhance_event_with_time(self, event: EventData) -> EventData:
        """
        Attempt to extract accurate time from invitation links.
        This will be enhanced with OCR functionality later.
        """
        # For now, return the event as-is
        # TODO: Implement OCR-based time extraction
        return event
    
    def check_for_duplicate_event(self, calendar_service, title: str, date: datetime) -> Optional[Dict[str, Any]]:
        """
        Check for existing events on the same day with similar titles.
        Based on the existing Apps Script checkForDuplicateEvent function.
        """
        try:
            # Create time range for the day
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Get events for the day
            events_result = calendar_service.events().list(
                calendarId=self.config.get('calendar_id'),
                timeMin=start_of_day.isoformat() + 'Z',
                timeMax=end_of_day.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            for existing_event in events:
                existing_title = existing_event.get('summary', '').lower()
                new_title = title.lower()
                
                # Check for exact match or very similar titles
                if (existing_title == new_title or 
                    existing_title.startswith(new_title[:20]) or
                    new_title.startswith(existing_title[:20])):
                    return existing_event
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking for duplicates: {str(e)}")
            return None
    
    def create_calendar_event(self, calendar_service, event: EventData) -> Optional[Dict[str, Any]]:
        """
        Create a calendar event from EventData.
        """
        try:
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
                    'timeZone': self.config['timezone']
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': self.config['timezone']
                },
                'location': event.location if event.location else None
            }
            
            # Add organizer if available
            if event.organizer:
                event_body['description'] += f"\n\nמארגן: {event.organizer}"
            
            # Add links if available
            if event.links:
                links_text = "\n\nקישורים רלוונטיים:\n"
                for link in event.links:
                    links_text += f"🔗 {link['label']}: {link['url']}\n"
                event_body['description'] += links_text
            
            # Create the event
            created_event = calendar_service.events().insert(
                calendarId=self.config.get('calendar_id'),
                body=event_body
            ).execute()
            
            self.logger.info(f"Created calendar event: {created_event.get('summary')}")
            return created_event
            
        except Exception as e:
            self.logger.error(f"Error creating calendar event: {str(e)}")
            return None 