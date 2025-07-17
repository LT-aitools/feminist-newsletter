"""
Script to update the calendar name to remove "(service account)" suffix.
"""
import logging
from service_account_auth import ServiceAccountAuth

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def update_calendar_name():
    """Update the calendar name to remove service account suffix."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== UPDATING CALENDAR NAME ===")
        
        # Initialize service account auth
        auth = ServiceAccountAuth()
        calendar_service = auth.get_calendar_service()
        
        # Calendar ID
        calendar_id = "5b6f7ad099565ddfa52d0bfe297cedc40ea0321360104f2b61782b5e69480270@group.calendar.google.com"
        
        logger.info(f"Calendar ID: {calendar_id}")
        
        # Get current calendar
        calendar = calendar_service.calendars().get(calendarId=calendar_id).execute()
        current_name = calendar.get('summary', '')
        
        logger.info(f"Current calendar name: {current_name}")
        
        # Check if it has "(Service Account)" suffix (case insensitive)
        if "(service account)" in current_name.lower():
            # Remove the suffix (handle different cases)
            new_name = current_name.replace(" (Service Account)", "").replace("(Service Account)", "")
            new_name = new_name.replace(" (service account)", "").replace("(service account)", "")
            new_name = new_name.strip()
            
            logger.info(f"Removing service account suffix...")
            logger.info(f"New name will be: {new_name}")
            
            # Update the calendar
            updated_calendar = {
                'summary': new_name,
                'timeZone': calendar.get('timeZone', 'Asia/Jerusalem'),
                'description': calendar.get('description', 'Feminist newsletter events calendar')
            }
            
            result = calendar_service.calendars().update(
                calendarId=calendar_id,
                body=updated_calendar
            ).execute()
            
            logger.info("✅ Successfully updated calendar name!")
            logger.info(f"New name: {result.get('summary')}")
            
            return result.get('summary')
            
        else:
            logger.info("✅ Calendar name doesn't contain '(service account)' suffix")
            logger.info(f"Current name: {current_name}")
            return current_name
        
    except Exception as e:
        logger.error(f"Error updating calendar name: {str(e)}")
        return None

def main():
    """Main function."""
    new_name = update_calendar_name()
    
    if new_name:
        print(f"\n✅ Calendar name updated successfully!")
        print(f"New name: {new_name}")
    else:
        print(f"\n❌ Failed to update calendar name")

if __name__ == "__main__":
    main() 