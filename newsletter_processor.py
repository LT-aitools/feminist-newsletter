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
from time_extractor import TimeExtractor


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
    time_verified: bool = False
    end_time: str = None
    
    def __post_init__(self):
        if self.links is None:
            self.links = []


class NewsletterProcessor:
    """Main processor for newsletter content."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.time_extractor = TimeExtractor()
    
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
        available_links = links.copy()  # Create a copy to consume links from
        
        for i, block in enumerate(event_blocks):
            try:
                event = self._parse_event_block(block, available_links, plain_text, event_blocks, html_content)
                if event:
                    # Remove used links from available_links so they can't be reused
                    for used_link in event.links:
                        if used_link in available_links:
                            available_links.remove(used_link)
                    
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
        
        # First, find all <a> tags and check if they contain invitation text
        a_tag_pattern = r'<a[^>]+href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>'
        a_matches = re.findall(a_tag_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for url, content in a_matches:
            # Remove HTML tags from content to get clean text
            clean_content = re.sub(r'<[^>]+>', '', content).strip()
            if 'בהזמנה' in clean_content or 'בלינק' in clean_content:
                # Prefer MailChimp tracking URLs over other types
                if 'wordpress.us13.list-manage.com/track/click' in url:
                    links.append({
                        'url': url,
                        'label': clean_content
                    })
                elif not links:  # Only add non-MailChimp URLs if no MailChimp URLs found
                    links.append({
                        'url': url,
                        'label': clean_content
                    })
        
        return links
    

    
    def _parse_event_block(self, block: str, links: List[Dict[str, str]] = None, plain_text: str = "", event_blocks: List[str] = None, html_content: str = None) -> Optional[EventData]:
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
            
            # DEBUG: Print HTML positions of event blocks and links
            if links and html_content and event_blocks:
                print("\n--- DEBUG: HTML Event Block and Link Positions ---")
                # Find HTML positions for all event blocks
                block_html_positions = []
                for eb in event_blocks:
                    pos = html_content.find(eb[:30])
                    block_html_positions.append(pos)
                    print(f"Event block start (first 30 chars): {eb[:30]!r} at HTML pos {pos}")
                # Find HTML positions for all links
                for link in links:
                    url_pos = html_content.find(link['url'])
                    print(f"Link: {link['label']!r} {link['url']} at HTML pos {url_pos}")
                print("--- END DEBUG ---\n")

            # Find matching links for this event (pure HTML-order-based matching)
            matching_links = []
            if links and html_content and event_blocks:
                # Find HTML positions for all event blocks
                block_html_positions = []
                for eb in event_blocks:
                    pos = html_content.find(eb[:30])
                    block_html_positions.append(pos)
                # Find this event's HTML start and the next event's start
                block_index = event_blocks.index(block)
                this_block_html_start = block_html_positions[block_index]
                if block_index + 1 < len(block_html_positions):
                    next_block_html_start = block_html_positions[block_index + 1]
                else:
                    next_block_html_start = len(html_content)
                # Build a list of (link, html_pos) for all links
                link_positions = []
                for link in links:
                    url_pos = html_content.find(link['url'])
                    if url_pos != -1:
                        link_positions.append((link, url_pos))
                # Sort links by their position in the HTML
                link_positions.sort(key=lambda x: x[1])
                # For each label type, pick the first link in the HTML range for this event
                for label_type in ['בהזמנה', 'בלינק']:
                    for link, url_pos in link_positions:
                        if label_type in link['label'] and this_block_html_start <= url_pos < next_block_html_start:
                            matching_links.append(link)
                            break
            else:
                # Fallback: original label matching if no html_content
                if links:
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
                links=matching_links,
                time_verified=False
            )
            
            # Try to extract time from invitation links
            if matching_links:
                event = self._enhance_event_with_time(event)
            
            return event
            
        except Exception as e:
            self.logger.error(f"Error parsing event block: {str(e)}")
            self.logger.debug(f"Block content: {block[:200]}...")
            return None
    
    def _enhance_event_with_time(self, event: EventData) -> EventData:
        """
        Attempt to extract accurate time from invitation links using OCR.
        """
        try:
            # Look for invitation links first
            invitation_links = [link for link in event.links 
                              if 'בהזמנה' in link.get('label', '')]
            
            # If no invitation links, try regular links as fallback
            if not invitation_links:
                regular_links = [link for link in event.links 
                               if 'בלינק' in link.get('label', '')]
                if regular_links:
                    self.logger.info(f"No invitation links found for event '{event.title}', trying {len(regular_links)} regular links")
                    invitation_links = regular_links
                else:
                    self.logger.info(f"No invitation or regular links found for event '{event.title}'")
                    return event
            
            # Try to extract time from each invitation link until one succeeds
            for i, link in enumerate(invitation_links):
                mailchimp_url = link['url']
                self.logger.info(f"Trying invitation link {i+1}/{len(invitation_links)} for event '{event.title}': {mailchimp_url}")
                
                extracted_times = self.time_extractor.extract_time_from_invitation_link(mailchimp_url)
                
                if extracted_times:
                    # Update event with extracted times
                    if isinstance(extracted_times, dict):
                        event.time = extracted_times['start']
                        if 'end' in extracted_times:
                            event.end_time = extracted_times['end']
                            # Calculate duration from start and end times
                            start_hour, start_minute = map(int, extracted_times['start'].split(':'))
                            end_hour, end_minute = map(int, extracted_times['end'].split(':'))
                            start_minutes = start_hour * 60 + start_minute
                            end_minutes = end_hour * 60 + end_minute
                            event.duration = end_minutes - start_minutes
                            self.logger.info(f"Updated event '{event.title}' with verified time range: {extracted_times['start']} - {extracted_times['end']} ({event.duration} minutes)")
                        else:
                            self.logger.info(f"Updated event '{event.title}' with verified start time: {extracted_times['start']}")
                    else:
                        # Backward compatibility for single time string
                        event.time = extracted_times
                        self.logger.info(f"Updated event '{event.title}' with verified time: {extracted_times}")
                    
                    event.time_verified = True
                    
                    # Remove the note about time being in invitation if it was added
                    if ' (זמן מדויק של האירוע בזימון)' in event.title:
                        event.title = event.title.replace(' (זמן מדויק של האירוע בזימון)', '')
                    
                    # Success - no need to try more links
                    break
                else:
                    self.logger.info(f"Link {i+1} failed for event '{event.title}' - trying next link")
            else:
                # All links failed
                self.logger.info(f"Could not extract time for event '{event.title}' from any invitation link - using default time")
            
            return event
            
        except Exception as e:
            self.logger.error(f"Error enhancing event with time extraction: {str(e)}")
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
                'description': event.description,
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
            
            # Add time verification status
            if not event.time_verified:
                event_body['description'] += f"\n\n⚠️ זמן משוער: {event.time} (זמן מדויק בהזמנה)"
            
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