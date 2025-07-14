"""
Gmail API integration for processing newsletter emails.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import get_config


class GmailHandler:
    """Handles Gmail API operations for newsletter processing."""
    
    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.service = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2 credentials.
        """
        try:
            import os
            import json
            import base64
            from google_auth_oauthlib.flow import InstalledAppFlow
            
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
                    self.logger.info("Setting up OAuth2 authentication for Gmail...")
                    
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
            
            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            
            # Test the connection
            self.service.users().getProfile(userId='me').execute()
            
            self.logger.info("Successfully authenticated with Gmail API")
            return True
            
        except Exception as e:
            self.logger.error(f"Gmail authentication failed: {str(e)}")
            return False
    
    def get_unread_newsletters(self, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Get unread newsletter emails from the specified sender(s).
        Accepts both the configured newsletter sender and nlevran@gmail.com, but only processes emails from nlevran@gmail.com if the subject or body contains 'מייל פמיניסטי שבועי'.
        """
        if not self.service:
            raise RuntimeError("Gmail service not initialized. Call authenticate() first.")
        
        try:
            max_results = max_results or self.config['max_emails_to_process']
            
            # Accept both senders
            senders = [self.config['newsletter_sender'], 'nlevran@gmail.com']
            query = f"({' OR '.join([f'from:{sender}' for sender in senders])}) is:unread"
            
            self.logger.info(f"Searching for emails with query: {query}")
            
            # Get message IDs
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            self.logger.info(f"Found {len(messages)} unread newsletter emails (from any sender)")
            
            # Get full message details
            email_data = []
            for message in messages:
                try:
                    email_info = self._get_email_details(message['id'])
                    if email_info:
                        # Only accept nlevran@gmail.com if subject contains 'מייל פמיניסטי שבועי'
                        if email_info['from'].lower().startswith('nlevran@gmail.com'):
                            if 'מייל פמיניסטי שבועי' in email_info.get('subject', ''):
                                email_data.append(email_info)
                        else:
                            email_data.append(email_info)
                except Exception as e:
                    self.logger.error(f"Error getting details for message {message['id']}: {str(e)}")
                    continue
            
            return email_data
            
        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            return []
    
    def _get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific email message.
        """
        try:
            # Get the full message
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date_header = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Parse date
            try:
                # Simple date parsing - you might want to use dateutil.parser for more robust parsing
                date_obj = datetime.now()  # Default to now if parsing fails
            except:
                date_obj = datetime.now()
            
            # Extract body content
            body_data = self._extract_body_content(message['payload'])
            
            email_info = {
                'id': message_id,
                'subject': subject,
                'from': from_header,
                'date': date_obj,
                'plain_text': body_data.get('plain_text', ''),
                'html_content': body_data.get('html_content', ''),
                'thread_id': message.get('threadId', '')
            }
            
            return email_info
            
        except Exception as e:
            self.logger.error(f"Error extracting email details: {str(e)}")
            return None
    
    def _extract_body_content(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract plain text and HTML content from email payload.
        """
        plain_text = ""
        html_content = ""
        
        def extract_from_part(part):
            nonlocal plain_text, html_content
            
            if part.get('mimeType') == 'text/plain':
                if 'data' in part['body']:
                    import base64
                    plain_text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif part.get('mimeType') == 'text/html':
                if 'data' in part['body']:
                    import base64
                    html_content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            
            # Recursively process nested parts
            if 'parts' in part:
                for subpart in part['parts']:
                    extract_from_part(subpart)
        
        extract_from_part(payload)
        
        return {
            'plain_text': plain_text,
            'html_content': html_content
        }
    
    def mark_as_processed(self, message_id: str) -> bool:
        """
        Mark an email as processed by adding a label.
        Note: This requires write permissions which are not included in the current scope.
        """
        self.logger.info(f"Would mark message {message_id} as processed (requires write permissions)")
        return True
    
    def get_recent_newsletters(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Get recent newsletter emails (not just unread) for testing purposes.
        """
        if not self.service:
            raise RuntimeError("Gmail service not initialized. Call authenticate() first.")
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates for Gmail query
            start_str = start_date.strftime('%Y/%m/%d')
            end_str = end_date.strftime('%Y/%m/%d')
            
            # Search for emails from the newsletter sender in date range
            query = f"from:{self.config['newsletter_sender']} after:{start_str} before:{end_str}"
            
            self.logger.info(f"Searching for recent emails with query: {query}")
            
            # Get message IDs
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50  # Get more for testing
            ).execute()
            
            messages = results.get('messages', [])
            self.logger.info(f"Found {len(messages)} recent newsletter emails")
            
            # Get full message details
            email_data = []
            for message in messages:
                try:
                    email_info = self._get_email_details(message['id'])
                    if email_info:
                        email_data.append(email_info)
                except Exception as e:
                    self.logger.error(f"Error getting details for message {message['id']}: {str(e)}")
                    continue
            
            return email_data
            
        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            return [] 