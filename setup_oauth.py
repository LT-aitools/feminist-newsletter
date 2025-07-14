"""
Simple OAuth2 setup for Gmail and Calendar APIs.
"""
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# OAuth2 scopes for Gmail and Calendar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/cloud-vision'
]

def create_oauth_credentials():
    """Create OAuth2 credentials with proper scopes."""
    
    creds = None
    
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Create a simple OAuth2 flow
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json',  # We'll create this
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def create_client_secrets():
    """Create a basic client_secrets.json file."""
    
    # This is a basic client secrets file for testing
    # In production, you'd get this from Google Cloud Console
    client_secrets = {
        "installed": {
            "client_id": "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",
            "project_id": "womens-rights-calendar",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "GOCSPX-your-secret-here",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open('client_secrets.json', 'w') as f:
        json.dump(client_secrets, f, indent=2)
    
    print("⚠️ Created basic client_secrets.json")
    print("⚠️ You'll need to update the client_secret with the real value from Google Cloud Console")

def test_oauth_credentials():
    """Test the OAuth2 credentials."""
    try:
        creds = create_oauth_credentials()
        
        if creds:
            print("✅ OAuth2 credentials created successfully!")
            print(f"✅ Scopes: {creds.scopes}")
            return True
        else:
            print("❌ Failed to create OAuth2 credentials")
            return False
            
    except Exception as e:
        print(f"❌ Error creating OAuth2 credentials: {e}")
        return False

def main():
    """Main setup function."""
    print("🔐 OAUTH2 SETUP FOR GMAIL AND CALENDAR APIS")
    print("=" * 50)
    
    # Check if client_secrets.json exists
    if not os.path.exists('client_secrets.json'):
        print("📝 Creating client_secrets.json...")
        create_client_secrets()
        print("\n⚠️ IMPORTANT: You need to:")
        print("1. Go to Google Cloud Console")
        print("2. Navigate to APIs & Services > Credentials")
        print("3. Create an OAuth 2.0 Client ID")
        print("4. Download the client_secrets.json file")
        print("5. Replace the current client_secrets.json with the downloaded one")
        print("\nFor now, let's try with the basic setup...")
    
    # Test OAuth2 credentials
    success = test_oauth_credentials()
    
    if success:
        print("\n🎉 OAuth2 setup completed!")
        print("📝 You can now use the token.json file for API access")
    else:
        print("\n⚠️ OAuth2 setup needs manual configuration")
        print("📝 Please follow the steps above to create proper client_secrets.json")

if __name__ == "__main__":
    main() 