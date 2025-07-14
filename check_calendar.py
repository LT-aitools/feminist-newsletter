"""
Script to check events in the calendar and their descriptions.
"""
import logging
from datetime import datetime, timedelta
from calendar_handler import CalendarHandler
from config import get_config

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def check_calendar():
    """Check events in the calendar."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    config = get_config()
    
    try:
        logger.info("=== CHECKING CALENDAR EVENTS ===")
        
        # Initialize calendar handler
        calendar_handler = CalendarHandler()
        
        # Authenticate
        logger.info("Authenticating with Calendar API...")
        if not calendar_handler.authenticate():
            raise RuntimeError("Failed to authenticate with Calendar API")
        
        # Get events for the next year
        start_date = datetime.now()
        end_date = start_date + timedelta(days=365)
        
        logger.info("Fetching events from calendar...")
        events = calendar_handler.get_events(start_date, end_date, max_results=1000)
        
        if not events:
            logger.info("No events found in calendar")
            return
        
        logger.info(f"Found {len(events)} events in calendar:")
        
        # Display each event
        for i, event in enumerate(events):
            event_id = event['id']
            event_title = event.get('summary', 'Unknown')
            event_description = event.get('description', 'No description')
            event_start = event.get('start', {}).get('dateTime', 'No start time')
            
            logger.info(f"\n--- Event {i+1} ---")
            logger.info(f"ID: {event_id}")
            logger.info(f"Title: {event_title}")
            logger.info(f"Start: {event_start}")
            logger.info(f"Description: {event_description}")
            
            # Check if description contains tracking links
            if 'wordpress.us13.list-manage.com' in event_description:
                logger.warning("⚠️  Description contains tracking links!")
            elif '[image:' in event_description:
                logger.warning("⚠️  Description contains image tags!")
            else:
                logger.info("✅ Description looks clean")
        
    except Exception as e:
        logger.error(f"Critical error during check: {str(e)}")

if __name__ == "__main__":
    check_calendar() 