"""
Simple OAuth2 setup for the newsletter automation.
"""
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# OAuth2 scopes for our APIs
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/cloud-vision'
]

def setup_oauth():
    """Set up OAuth2 credentials with proper scopes."""
    
    creds = None
    
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("🔐 Setting up OAuth2 authentication...")
            print("📝 This will open a browser window for authentication")
            
            # Use the default client ID from Google Cloud
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', 
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        print("✅ OAuth2 credentials saved to token.json")
    
    return creds

def test_apis_with_oauth():
    """Test APIs with OAuth2 credentials."""
    print("\n=== TESTING APIS WITH OAUTH2 ===")
    
    try:
        creds = setup_oauth()
        
        if not creds:
            print("❌ Failed to get OAuth2 credentials")
            return False
        
        print(f"✅ OAuth2 credentials obtained with scopes: {creds.scopes}")
        
        # Test Calendar API
        try:
            calendar_service = build('calendar', 'v3', credentials=creds)
            calendar_list = calendar_service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            print(f"✅ Calendar API working - Found {len(calendars)} calendars")
            for calendar in calendars:
                print(f"  - {calendar.get('summary', 'No name')}")
        except Exception as e:
            print(f"❌ Calendar API error: {e}")
        
        # Test Gmail API
        try:
            gmail_service = build('gmail', 'v1', credentials=creds)
            profile = gmail_service.users().getProfile(userId='me').execute()
            print(f"✅ Gmail API working - Email: {profile.get('emailAddress')}")
        except Exception as e:
            print(f"❌ Gmail API error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing APIs: {e}")
        return False

def create_client_secrets_template():
    """Create a template for client_secrets.json."""
    
    template = {
        "installed": {
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "project_id": "womens-rights-calendar",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open('client_secrets_template.json', 'w') as f:
        json.dump(template, f, indent=2)
    
    print("📝 Created client_secrets_template.json")
    print("📝 Please:")
    print("1. Go to Google Cloud Console > APIs & Services > Credentials")
    print("2. Create an OAuth 2.0 Client ID")
    print("3. Download the client_secrets.json file")
    print("4. Replace the template with the real file")

def main():
    """Main setup function."""
    print("🔐 OAUTH2 SETUP FOR NEWSLETTER AUTOMATION")
    print("=" * 50)
    
    # Check if client_secrets.json exists
    if not os.path.exists('client_secrets.json'):
        print("❌ client_secrets.json not found")
        create_client_secrets_template()
        print("\n⚠️ Please set up client_secrets.json first")
        return
    
    # Test APIs with OAuth2
    success = test_apis_with_oauth()
    
    if success:
        print("\n🎉 OAuth2 setup completed successfully!")
        print("📝 You can now use the newsletter automation with real APIs")
    else:
        print("\n⚠️ OAuth2 setup needs additional configuration")

if __name__ == "__main__":
    main() 