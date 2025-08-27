"""
Service Account Authentication for Newsletter Automation.
Uses Google Cloud Service Account for all API access (Gmail, Calendar, Vision).
"""
import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import vision
from config import get_config

# Service account key file path
SERVICE_ACCOUNT_KEY_FILE = "/Users/Amos/Documents/GitHub/womens-rights-calendar.json"

# API scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/cloud-vision'
]

class ServiceAccountAuth:
    """Handles authentication using Google Cloud Service Account."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.credentials = None
        self.config = get_config()
        self._load_credentials()
    
    def _load_credentials(self):
        """Load service account credentials."""
        try:
            # Check if we're in a Cloud Function environment
            is_cloud_function = os.getenv('FUNCTION_TARGET') is not None or os.getenv('K_SERVICE') is not None
            
            if is_cloud_function:
                # In Cloud Function environment, try to use the configured service account
                try:
                    # Try to download service account key from Cloud Storage
                    try:
                        from google.cloud import storage
                        import tempfile
                        
                        # Download key file from Cloud Storage
                        storage_client = storage.Client()
                        bucket = storage_client.bucket("womens-rights-calendar-keys")
                        blob = bucket.blob("service-account-key.json")
                        
                        # Create temporary file
                        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                            blob.download_to_filename(temp_file.name)
                            temp_key_file = temp_file.name
                        
                        # Use the downloaded key file
                        self.credentials = service_account.Credentials.from_service_account_file(
                            temp_key_file,
                            scopes=SCOPES
                        )
                        self.logger.info(f"🔄 Using service account from Cloud Storage: {self.credentials.service_account_email}")
                        
                        # Clean up temporary file
                        os.unlink(temp_key_file)
                        return
                        
                    except Exception as storage_error:
                        self.logger.warning(f"Could not download key from Cloud Storage: {str(storage_error)}")
                    
                    # Check if GOOGLE_APPLICATION_CREDENTIALS is set
                    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                        # Use the service account key file if available
                        key_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                        if os.path.exists(key_file):
                            self.credentials = service_account.Credentials.from_service_account_file(
                                key_file,
                                scopes=SCOPES
                            )
                            self.logger.info(f"🔄 Using service account from GOOGLE_APPLICATION_CREDENTIALS: {self.credentials.service_account_email}")
                            return
                    
                    # Fallback to default credentials
                    from google.auth import default
                    self.credentials, project = default(scopes=SCOPES)
                    self.logger.info(f"Using default credentials for project: {project}")
                    
                    # Log service account information
                    if hasattr(self.credentials, 'service_account_email'):
                        self.logger.info(f"Service account: {self.credentials.service_account_email}")
                        if "vision-api-access" in self.credentials.service_account_email:
                            self.logger.info("✅ Using correct service account for domain-wide delegation")
                        elif self.credentials.service_account_email == "default":
                            self.logger.warning("⚠️ Using default service account - domain-wide delegation may fail")
                            self.logger.info("This is expected for 1st gen Cloud Functions - function should still work")
                    else:
                        self.logger.warning("Default credentials are not a service account")
                    
                    return
                except Exception as e:
                    self.logger.error(f"Error with default credentials in Cloud Function: {str(e)}")
                    raise
            else:
                # Local development - try default credentials first, then fallback to key file
                try:
                    from google.auth import default
                    self.credentials, project = default(scopes=SCOPES)
                    self.logger.info(f"Using default credentials for project: {project}")
                    
                    # Log service account information
                    if hasattr(self.credentials, 'service_account_email'):
                        self.logger.info(f"Service account: {self.credentials.service_account_email}")
                        if "vision-api-access" in self.credentials.service_account_email:
                            self.logger.info("✅ Using correct service account for domain-wide delegation")
                    else:
                        self.logger.warning("Default credentials are not a service account")
                    
                    return
                except Exception as e:
                    self.logger.debug(f"Default credentials not available: {str(e)}")
                
                # Fallback to service account key file (for local development)
                if os.path.exists(SERVICE_ACCOUNT_KEY_FILE):
                    self.credentials = service_account.Credentials.from_service_account_file(
                        SERVICE_ACCOUNT_KEY_FILE,
                        scopes=SCOPES
                    )
                    self.logger.info(f"Service account credentials loaded from file: {self.credentials.service_account_email}")
                else:
                    raise FileNotFoundError(f"Service account key file not found: {SERVICE_ACCOUNT_KEY_FILE}")
            
        except Exception as e:
            self.logger.error(f"Error loading service account credentials: {str(e)}")
            raise
    
    def get_gmail_service(self, user_email=None):
        """Get authenticated Gmail API service with domain-wide delegation."""
        try:
            if user_email and hasattr(self.credentials, 'with_subject'):
                # Use domain-wide delegation to act on behalf of the user
                try:
                    delegated_credentials = self.credentials.with_subject(user_email)
                    service = build('gmail', 'v1', credentials=delegated_credentials)
                    self.logger.info(f"Gmail API service created for user: {user_email}")
                    return service
                except Exception as e:
                    self.logger.warning(f"Domain-wide delegation failed for {user_email}: {str(e)}")
                    self.logger.info("Falling back to service account's own mailbox")
                    # Fallback to service account's own mailbox
                    service = build('gmail', 'v1', credentials=self.credentials)
                    self.logger.info("Gmail API service created for service account mailbox")
                    return service
            else:
                # Use default service account (limited access)
                service = build('gmail', 'v1', credentials=self.credentials)
                self.logger.info("Gmail API service created (limited access)")
            return service
        except Exception as e:
            self.logger.error(f"Error creating Gmail service: {str(e)}")
            raise
    
    def get_calendar_service(self):
        """Get authenticated Calendar API service."""
        try:
            service = build('calendar', 'v3', credentials=self.credentials)
            self.logger.info("Calendar API service created successfully")
            return service
        except Exception as e:
            self.logger.error(f"Error creating Calendar service: {str(e)}")
            raise
    
    def get_vision_client(self):
        """Get authenticated Vision API client."""
        try:
            client = vision.ImageAnnotatorClient(credentials=self.credentials)
            self.logger.info("Vision API client created successfully")
            return client
        except Exception as e:
            self.logger.error(f"Error creating Vision client: {str(e)}")
            raise
    
    def test_apis(self):
        """Test all API connections."""
        try:
            self.logger.info("=== TESTING SERVICE ACCOUNT APIs ===")
            
            # Test Gmail API with domain-wide delegation
            try:
                user_email = self.config.get('gmail_account', 'hello@letstalkaitools.com')
                gmail_service = self.get_gmail_service(user_email)
                # Test Gmail access
                profile = gmail_service.users().getProfile(userId='me').execute()
                self.logger.info(f"✅ Gmail API working - Email: {profile.get('emailAddress')}")
            except Exception as e:
                self.logger.warning(f"⚠️ Gmail API: {str(e)}")
            
            # Test Calendar API
            try:
                calendar_service = self.get_calendar_service()
                # Test calendar access
                calendar_list = calendar_service.calendarList().list().execute()
                calendars = calendar_list.get('items', [])
                self.logger.info(f"✅ Calendar API working - Found {len(calendars)} calendars")
                for calendar in calendars:
                    self.logger.info(f"  - {calendar.get('summary', 'No name')}")
            except Exception as e:
                self.logger.warning(f"⚠️ Calendar API: {str(e)}")
            
            # Test Vision API
            try:
                vision_client = self.get_vision_client()
                self.logger.info("✅ Vision API client created")
            except Exception as e:
                self.logger.warning(f"⚠️ Vision API: {str(e)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error testing APIs: {str(e)}")
            return False

def main():
    """Test service account authentication."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        auth = ServiceAccountAuth()
        auth.test_apis()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 