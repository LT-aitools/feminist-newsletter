"""
Script to update past calendar events with time extraction for testing.
This will attempt to extract times from invitation links for existing events.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re

from config import get_config
from time_extractor import TimeExtractor
from email_handler import EmailHandler


class PastEventUpdater:
    """Updates past calendar events with time extraction."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.time_extractor = TimeExtractor()
        self.email_handler = EmailHandler()
    
    def update_past_events(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Update past events with time extraction.
        
        Args:
            days_back: Number of days to look back for events
            
        Returns:
            Summary of update results
        """
        try:
            self.logger.info(f"Starting past event update for last {days_back} days")
            
            # Get calendar service
            calendar_service = self.email_handler.get_calendar_service()
            if not calendar_service:
                self.logger.error("Failed to get calendar service")
                return {"success": False, "error": "Calendar service unavailable"}
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Get events in the date range
            events = self._get_events_in_range(calendar_service, start_date, end_date)
            self.logger.info(f"Found {len(events)} events to process")
            
            # Process each event
            results = {
                "total_events": len(events),
                "updated_events": 0,
                "failed_events": 0,
                "no_invitation_links": 0,
                "details": []
            }
            
            for event in events:
                event_result = self._process_single_event(calendar_service, event)
                results["details"].append(event_result)
                
                if event_result["status"] == "updated":
                    results["updated_events"] += 1
                elif event_result["status"] == "failed":
                    results["failed_events"] += 1
                elif event_result["status"] == "no_links":
                    results["no_invitation_links"] += 1
            
            self.logger.info(f"Update completed: {results['updated_events']} updated, "
                           f"{results['failed_events']} failed, "
                           f"{results['no_invitation_links']} no links")
            
            return {"success": True, "results": results}
            
        except Exception as e:
            self.logger.error(f"Error updating past events: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_events_in_range(self, calendar_service, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get calendar events in the specified date range."""
        try:
            events_result = calendar_service.events().list(
                calendarId=self.config.get('calendar_id'),
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
            
        except Exception as e:
            self.logger.error(f"Error getting events: {str(e)}")
            return []
    
    def _process_single_event(self, calendar_service, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single event for time extraction."""
        event_id = event.get('id')
        event_title = event.get('summary', 'Unknown Event')
        event_description = event.get('description', '')
        
        result = {
            "event_id": event_id,
            "title": event_title,
            "status": "unknown",
            "old_time": None,
            "new_time": None,
            "error": None
        }
        
        try:
            # Extract invitation links from event description
            invitation_links = self._extract_invitation_links(event_description)
            
            if not invitation_links:
                result["status"] = "no_links"
                return result
            
            # Get current event time
            start_time = event.get('start', {}).get('dateTime')
            if start_time:
                current_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                result["old_time"] = current_time.strftime('%H:%M')
            
            # Try to extract time from invitation links
            extracted_time = None
            for link in invitation_links:
                extracted_time = self.time_extractor.extract_time_from_invitation_link(link)
                if extracted_time:
                    break
            
            if extracted_time:
                # Update the event with new time
                success = self._update_event_time(calendar_service, event, extracted_time)
                if success:
                    result["status"] = "updated"
                    result["new_time"] = extracted_time
                    self.logger.info(f"Updated event '{event_title}' with time: {extracted_time}")
                else:
                    result["status"] = "failed"
                    result["error"] = "Failed to update calendar event"
            else:
                result["status"] = "failed"
                result["error"] = "Could not extract time from invitation links"
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.logger.error(f"Error processing event '{event_title}': {str(e)}")
        
        return result
    
    def _extract_invitation_links(self, description: str) -> List[str]:
        """Extract invitation links from event description."""
        links = []
        
        # Look for MailChimp URLs in the description
        mailchimp_pattern = r'https://[^\s]+list-manage\.com[^\s]*'
        matches = re.findall(mailchimp_pattern, description)
        
        for match in matches:
            # Check if this looks like an invitation link
            if 'track/click' in match or 'בהזמנה' in description:
                links.append(match)
        
        return links
    
    def _update_event_time(self, calendar_service, event: Dict[str, Any], new_time: str) -> bool:
        """Update event with new time."""
        try:
            event_id = event.get('id')
            
            # Parse new time
            hour, minute = map(int, new_time.split(':'))
            
            # Get current start date
            start_datetime = event.get('start', {}).get('dateTime')
            if not start_datetime:
                return False
            
            current_start = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
            
            # Create new start time with same date but new time
            new_start = current_start.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Calculate end time (keep same duration)
            end_datetime = event.get('end', {}).get('dateTime')
            if end_datetime:
                current_end = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
                duration = current_end - current_start
                new_end = new_start + duration
            else:
                # Default 2-hour duration
                new_end = new_start + timedelta(hours=2)
            
            # Update event
            updated_event = {
                'start': {
                    'dateTime': new_start.isoformat(),
                    'timeZone': self.config['timezone']
                },
                'end': {
                    'dateTime': new_end.isoformat(),
                    'timeZone': self.config['timezone']
                }
            }
            
            # Update the event
            calendar_service.events().update(
                calendarId=self.config.get('calendar_id'),
                eventId=event_id,
                body=updated_event
            ).execute()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating event time: {str(e)}")
            return False


def main():
    """Main function to run the past event updater."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Past Event Time Extraction Updater")
    print("=" * 50)
    
    # Initialize updater
    updater = PastEventUpdater()
    
    # Update events from last 30 days
    result = updater.update_past_events(days_back=30)
    
    if result["success"]:
        results = result["results"]
        print(f"\n✅ Update completed successfully!")
        print(f"📊 Summary:")
        print(f"   Total events processed: {results['total_events']}")
        print(f"   Events updated: {results['updated_events']}")
        print(f"   Events failed: {results['failed_events']}")
        print(f"   Events with no invitation links: {results['no_invitation_links']}")
        
        # Show details for updated events
        if results['updated_events'] > 0:
            print(f"\n📝 Updated Events:")
            for detail in results['details']:
                if detail['status'] == 'updated':
                    print(f"   • {detail['title']}: {detail['old_time']} → {detail['new_time']}")
        
        # Show details for failed events
        if results['failed_events'] > 0:
            print(f"\n❌ Failed Events:")
            for detail in results['details']:
                if detail['status'] == 'failed':
                    print(f"   • {detail['title']}: {detail['error']}")
    
    else:
        print(f"\n❌ Update failed: {result['error']}")


if __name__ == "__main__":
    main() 