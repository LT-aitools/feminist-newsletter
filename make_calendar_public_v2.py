"""
Alternative approach to make the service account calendar public.
"""
import logging
from service_account_auth import ServiceAccountAuth

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def make_calendar_public_v2():
    """Make the service account calendar public using ACL rules."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== MAKING CALENDAR PUBLIC (V2) ===")
        
        # Initialize service account auth
        auth = ServiceAccountAuth()
        calendar_service = auth.get_calendar_service()
        
        # Service account calendar ID
        calendar_id = "5b6f7ad099565ddfa52d0bfe297cedc40ea0321360104f2b61782b5e69480270@group.calendar.google.com"
        
        logger.info(f"Calendar ID: {calendar_id}")
        
        # Get current calendar settings
        calendar = calendar_service.calendars().get(calendarId=calendar_id).execute()
        logger.info(f"Calendar: {calendar.get('summary')}")
        
        # Method 1: Add public access ACL rule
        try:
            public_rule = {
                'scope': {
                    'type': 'default'
                },
                'role': 'reader'
            }
            
            result = calendar_service.acl().insert(
                calendarId=calendar_id,
                body=public_rule
            ).execute()
            
            logger.info("✅ Added public access ACL rule")
            logger.info(f"Rule: {result}")
            
        except Exception as e:
            logger.warning(f"ACL rule already exists or failed: {str(e)}")
        
        # Method 2: Update calendar settings
        try:
            updated_calendar = {
                'summary': calendar.get('summary'),
                'timeZone': calendar.get('timeZone', 'Asia/Jerusalem'),
                'conferenceProperties': {
                    'allowedConferenceSolutionTypes': ['hangoutsMeet']
                }
            }
            
            result = calendar_service.calendars().update(
                calendarId=calendar_id,
                body=updated_calendar
            ).execute()
            
            logger.info("✅ Updated calendar settings")
            
        except Exception as e:
            logger.warning(f"Calendar update failed: {str(e)}")
        
        # Method 3: Try to get the calendar as a public user
        try:
            # Get calendar list entry
            calendar_list_entry = calendar_service.calendarList().get(calendarId=calendar_id).execute()
            logger.info("✅ Calendar list entry retrieved")
            
            # Try to get the calendar directly
            public_calendar = calendar_service.calendars().get(calendarId=calendar_id).execute()
            logger.info(f"✅ Calendar accessible: {public_calendar.get('summary')}")
            
        except Exception as e:
            logger.error(f"Calendar access failed: {str(e)}")
        
        # Show sharing information
        logger.info(f"\n=== SHARING INFORMATION ===")
        logger.info(f"Calendar ID: {calendar_id}")
        logger.info(f"Calendar Name: {calendar.get('summary')}")
        
        logger.info("\n=== TESTING ACCESS ===")
        logger.info("Try these methods to access the calendar:")
        logger.info("1. Go to Google Calendar")
        logger.info("2. Click '+' next to 'Other calendars'")
        logger.info("3. Click 'Subscribe to calendar'")
        logger.info(f"4. Enter: {calendar_id}")
        logger.info("5. Click 'Add calendar'")
        
        logger.info("\n=== ALTERNATIVE: CREATE NEW PUBLIC CALENDAR ===")
        logger.info("If the above doesn't work, we can create a new public calendar")
        
        return calendar_id
        
    except Exception as e:
        logger.error(f"Error making calendar public: {str(e)}")
        return None

def create_new_public_calendar():
    """Create a new public calendar as backup."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== CREATING NEW PUBLIC CALENDAR ===")
        
        auth = ServiceAccountAuth()
        calendar_service = auth.get_calendar_service()
        
        # Create new calendar
        calendar_body = {
            'summary': 'Feminist Newsletter Events - Public',
            'description': 'Public calendar for feminist newsletter events',
            'timeZone': 'Asia/Jerusalem'
        }
        
        created_calendar = calendar_service.calendars().insert(body=calendar_body).execute()
        calendar_id = created_calendar['id']
        
        logger.info(f"✅ Created new calendar: {created_calendar['summary']}")
        logger.info(f"Calendar ID: {calendar_id}")
        
        # Make it public
        public_rule = {
            'scope': {
                'type': 'default'
            },
            'role': 'reader'
        }
        
        result = calendar_service.acl().insert(
            calendarId=calendar_id,
            body=public_rule
        ).execute()
        
        logger.info("✅ Made new calendar public")
        logger.info(f"Calendar ID: {calendar_id}")
        
        return calendar_id
        
    except Exception as e:
        logger.error(f"Error creating new calendar: {str(e)}")
        return None

def main():
    """Main function."""
    calendar_id = make_calendar_public_v2()
    
    if not calendar_id:
        print("\nTrying to create a new public calendar...")
        calendar_id = create_new_public_calendar()
    
    if calendar_id:
        print(f"\nCalendar ID: {calendar_id}")
        print("Try subscribing to this calendar in Google Calendar")

if __name__ == "__main__":
    main() 