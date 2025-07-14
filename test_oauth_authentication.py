"""
Test script with OAuth2 authentication for Gmail and Calendar APIs.
"""
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# OAuth2 scopes for Gmail and Calendar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/cloud-vision'
]

def get_oauth_credentials():
    """Get OAuth2 credentials with proper scopes."""
    creds = None
    
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Create a client secrets file or use a default one
            # For now, we'll try to use the existing credentials
            print("⚠️ No OAuth2 credentials found. Using existing authentication...")
            return None
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def test_gmail_api_oauth():
    """Test Gmail API with OAuth2."""
    print("=== TESTING GMAIL API WITH OAUTH2 ===")
    try:
        creds = get_oauth_credentials()
        if not creds:
            print("❌ No OAuth2 credentials available")
            return False
        
        # Build Gmail service
        gmail_service = build('gmail', 'v1', credentials=creds)
        
        # Test API call
        profile = gmail_service.users().getProfile(userId='me').execute()
        print(f"✅ Gmail API working - Email: {profile.get('emailAddress')}")
        return True
        
    except Exception as e:
        print(f"❌ Gmail API error: {e}")
        return False

def test_calendar_api_oauth():
    """Test Calendar API with OAuth2."""
    print("\n=== TESTING CALENDAR API WITH OAUTH2 ===")
    try:
        creds = get_oauth_credentials()
        if not creds:
            print("❌ No OAuth2 credentials available")
            return False
        
        # Build Calendar service
        calendar_service = build('calendar', 'v3', credentials=creds)
        
        # Test API call - list calendars
        calendar_list = calendar_service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        print(f"✅ Calendar API working - Found {len(calendars)} calendars")
        for calendar in calendars:
            print(f"  - {calendar.get('summary', 'No name')} ({calendar.get('id', 'No ID')})")
        return True
        
    except Exception as e:
        print(f"❌ Calendar API error: {e}")
        return False

def test_simple_gmail_access():
    """Test simple Gmail access using existing credentials."""
    print("\n=== TESTING SIMPLE GMAIL ACCESS ===")
    try:
        from google.auth import default
        credentials, project = default()
        
        # Try to build Gmail service
        gmail_service = build('gmail', 'v1', credentials=credentials)
        
        # Try a simple API call
        profile = gmail_service.users().getProfile(userId='me').execute()
        print(f"✅ Simple Gmail access working - Email: {profile.get('emailAddress')}")
        return True
        
    except Exception as e:
        print(f"❌ Simple Gmail access failed: {e}")
        return False

def main():
    """Run OAuth2 authentication tests."""
    print("🔐 TESTING OAUTH2 AUTHENTICATION")
    print("=" * 50)
    
    # Test simple access first
    simple_gmail = test_simple_gmail_access()
    
    # Test OAuth2 access
    gmail_oauth = test_gmail_api_oauth()
    calendar_oauth = test_calendar_api_oauth()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 OAUTH2 TEST SUMMARY")
    print(f"Simple Gmail Access: {'✅ Working' if simple_gmail else '❌ Failed'}")
    print(f"Gmail API (OAuth2): {'✅ Working' if gmail_oauth else '❌ Failed'}")
    print(f"Calendar API (OAuth2): {'✅ Working' if calendar_oauth else '❌ Failed'}")
    
    if simple_gmail:
        print("\n🎉 Basic Gmail access is working! We can proceed with testing.")
    else:
        print("\n⚠️ Need to set up proper OAuth2 credentials.")

if __name__ == "__main__":
    main() 