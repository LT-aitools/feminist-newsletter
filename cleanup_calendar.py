"""
Script to clean up all events from the Feminist Newsletter Events calendar.
Useful for testing the improved text cleaning.
"""
import logging
from datetime import datetime, timedelta
from calendar_handler import CalendarHandler
from service_account_auth import ServiceAccountAuth
from config import get_config

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def cleanup_calendar():
    """Delete all events from the calendar (5 years back and forward)."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    config = get_config()
    
    try:
        logger.info("=== CALENDAR CLEANUP ===")
        
        # Initialize service account authentication
        logger.info("Setting up service account authentication...")
        auth = ServiceAccountAuth()
        calendar_service = auth.get_calendar_service()
        
        # Initialize calendar handler with service account
        calendar_handler = CalendarHandler(service=calendar_service)
        
        logger.info(f"Using calendar ID: {calendar_handler.calendar_id}")
        
        # Get events for the last 5 years to next 5 years
        start_date = datetime.now() - timedelta(days=5*365)
        end_date = datetime.now() + timedelta(days=5*365)
        
        logger.info(f"Fetching events from {start_date.date()} to {end_date.date()}...")
        events = calendar_handler.get_events(start_date, end_date, max_results=2000)
        
        if not events:
            logger.info("No events found to delete")
            return
        
        logger.info(f"Found {len(events)} events to delete")
        
        # Delete each event
        deleted_count = 0
        for i, event in enumerate(events):
            try:
                event_id = event['id']
                event_title = event.get('summary', 'Unknown')
                
                logger.info(f"Deleting event {i+1}/{len(events)}: {event_title}")
                
                if calendar_handler.delete_event(event_id):
                    deleted_count += 1
                    logger.info(f"Successfully deleted: {event_title}")
                else:
                    logger.error(f"Failed to delete: {event_title}")
                    
            except Exception as e:
                logger.error(f"Error deleting event {i+1}: {str(e)}")
                continue
        
        logger.info(f"=== CLEANUP COMPLETE ===")
        logger.info(f"Total events found: {len(events)}")
        logger.info(f"Successfully deleted: {deleted_count}")
        logger.info(f"Failed to delete: {len(events) - deleted_count}")
        
    except Exception as e:
        logger.error(f"Critical error during cleanup: {str(e)}")

if __name__ == "__main__":
    cleanup_calendar() 