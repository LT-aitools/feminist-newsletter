"""
Google Calendar API integration for creating and managing events.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import get_config


class CalendarHandler:
    """Handles Google Calendar API operations."""
    
    # Calendar API scopes
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.service = None
        self.calendar_id = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API using OAuth2 credentials.
        """
        try:
            import os
            import json
            import base64
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            
            creds = None
            
            # Check if we're running in Cloud Functions (environment variables)
            if os.getenv('OAUTH_CREDENTIALS'):
                try:
                    # Decode credentials from environment variable
                    oauth_data = json.loads(os.getenv('OAUTH_CREDENTIALS'))
                    if 'token' in oauth_data:
                        token_data = json.loads(base64.b64decode(oauth_data['token']).decode('utf-8'))
                        creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)
                        self.logger.info("Loaded OAuth credentials from environment variables")
                except Exception as e:
                    self.logger.warning(f"Failed to load credentials from environment: {str(e)}")
            
            # Fallback to local files
            if not creds and os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    self.logger.info("Setting up OAuth2 authentication for Calendar...")
                    
                    # Try to load client secrets from environment first
                    client_secrets_file = 'client_secrets.json'
                    if os.getenv('CLIENT_SECRETS'):
                        try:
                            client_data = json.loads(os.getenv('CLIENT_SECRETS'))
                            if 'client_secrets' in client_data:
                                client_secrets_content = base64.b64decode(client_data['client_secrets']).decode('utf-8')
                                # Create temporary file
                                import tempfile
                                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                                    f.write(client_secrets_content)
                                    client_secrets_file = f.name
                        except Exception as e:
                            self.logger.warning(f"Failed to load client secrets from environment: {str(e)}")
                    
                    # Use the client secrets file
                    flow = InstalledAppFlow.from_client_secrets_file(
                        client_secrets_file, 
                        self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run (only if not in Cloud Functions)
                if not os.getenv('OAUTH_CREDENTIALS') and os.path.exists('token.json'):
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
                    self.logger.info("OAuth2 credentials saved to token.json")
            
            # Build the Calendar service
            self.service = build('calendar', 'v3', credentials=creds)
            
            # Use the configured calendar_id
            self.calendar_id = self.config.get('calendar_id')
            
            self.logger.info(f"Successfully authenticated with Calendar API")
            self.logger.info(f"Using calendar: {self.config['calendar_name']} (ID: {self.calendar_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Calendar authentication failed: {str(e)}")
            return False
    
    def get_service(self):
        """
        Get the Calendar service object.
        """
        if not self.service:
            raise RuntimeError("Calendar service not initialized. Call authenticate() first.")
        return self.service
    
    def create_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a calendar event.
        """
        if not self.service or not self.calendar_id:
            raise RuntimeError("Calendar service not initialized. Call authenticate() first.")
        
        try:
            # Create the event
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_data
            ).execute()
            
            self.logger.info(f"Created calendar event: {created_event.get('summary')}")
            return created_event
            
        except HttpError as error:
            self.logger.error(f"Error creating calendar event: {error}")
            return None
    
    def check_for_duplicate_event(self, title: str, date: datetime) -> Optional[Dict[str, Any]]:
        """
        Check for existing events on the same day with similar titles.
        Based on the existing Apps Script checkForDuplicateEvent function.
        """
        if not self.service or not self.calendar_id:
            raise RuntimeError("Calendar service not initialized. Call authenticate() first.")
        
        try:
            # Create time range for the day
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Get events for the day
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
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
                    self.logger.info(f"Found duplicate event: {existing_event.get('summary')}")
                    return existing_event
            
            return None
            
        except HttpError as error:
            self.logger.error(f"Error checking for duplicates: {error}")
            return None
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """
        List all available calendars for debugging purposes.
        Based on the existing Apps Script listAllCalendars function.
        """
        if not self.service:
            raise RuntimeError("Calendar service not initialized. Call authenticate() first.")
        
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            self.logger.info(f"Found {len(calendars)} calendars:")
            for i, calendar in enumerate(calendars):
                self.logger.info(f"{i+1}. {calendar['summary']} (ID: {calendar['id']})")
            
            return calendars
            
        except HttpError as error:
            self.logger.error(f"Error listing calendars: {error}")
            return []
    
    def get_events(self, start_date: datetime = None, end_date: datetime = None, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get events from the calendar within a date range.
        Based on the existing Apps Script viewExistingEvents function.
        """
        if not self.service or not self.calendar_id:
            raise RuntimeError("Calendar service not initialized. Call authenticate() first.")
        
        try:
            # Default to next 60 days if no dates provided
            if not start_date:
                start_date = datetime.now()
            if not end_date:
                end_date = start_date + timedelta(days=60)
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            self.logger.info(f"Found {len(events)} events between {start_date.date()} and {end_date.date()}")
            
            return events
            
        except HttpError as error:
            self.logger.error(f"Error getting events: {error}")
            return []
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event.
        """
        if not self.service or not self.calendar_id:
            raise RuntimeError("Calendar service not initialized. Call authenticate() first.")
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            self.logger.info(f"Deleted event: {event_id}")
            return True
            
        except HttpError as error:
            self.logger.error(f"Error deleting event: {error}")
            return False
    
    def cleanup_test_events(self) -> int:
        """
        Clean up test and debug events from the calendar.
        Based on the existing Apps Script cleanupTestEvents function.
        """
        if not self.service or not self.calendar_id:
            raise RuntimeError("Calendar service not initialized. Call authenticate() first.")
        
        try:
            # Get events for the next year
            start_date = datetime.now()
            end_date = start_date + timedelta(days=365)
            
            events = self.get_events(start_date, end_date, max_results=1000)
            
            deleted_count = 0
            for event in events:
                title = event.get('summary', '')
                description = event.get('description', '')
                
                # Check if it's a test event or newsletter event
                if (title and any(keyword in title for keyword in ['Test', 'Debug', '(זמן מדויק של האירוע בזימון)']) or
                    description and 'נוצר אוטומטית מהניוזלטר הפמיניסטי השבועי' in description):
                    
                    if self.delete_event(event['id']):
                        deleted_count += 1
            
            self.logger.info(f"Cleaned up {deleted_count} test/debug events")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up test events: {str(e)}")
            return 0 