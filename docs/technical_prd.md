Technical PRD - Women's Rights Newsletter Automation
Python + Google Cloud Functions Implementation
Project Overview
Migrate and enhance the existing Google Apps Script newsletter automation to a Python-based Google Cloud Functions solution that can handle MailChimp redirects and extract accurate event times from invitation materials.

Architecture Overview
Gmail API → Cloud Function → [Web Scraping] → [OCR Processing] → Calendar API
    ↓
Cloud Scheduler (Weekly Trigger) → Cloud Function → Cloud Vision API → Google Calendar

Core Components
Cloud Function: Main processing logic
Cloud Scheduler: Weekly automation trigger
Cloud Vision API: OCR for time extraction
Gmail API: Email processing
Google Calendar API: Event creation
Cloud Storage: Temporary image storage

Technical Requirements
Part 1: Core Newsletter Processing (Migration)
Email Processing
Gmail API Integration: Replace Apps Script Gmail access
Hebrew Text Processing: Robust Unicode handling for RTL text
Newsletter Parsing: Extract event blocks using improved regex patterns
Duplicate Prevention: Enhanced duplicate detection logic
Event Data Extraction
Date Parsing: Hebrew date format handling (ה7/7 format)
Title Extraction: Multiple pattern matching for event titles
Location Detection: City and virtual event identification
Organizer Identification: Extract organizing bodies
Calendar Integration
Google Calendar API: Create events with full metadata
Timezone Handling: Proper Israel/Jerusalem timezone support
Event Formatting: Hebrew text formatting and descriptions
Part 2: Time Extraction from Invitations
Link Resolution
MailChimp Redirect Following: Resolve tracking URLs to final destinations
HTTP Request Handling: Proper redirect following with session management
Error Handling: Graceful handling of failed redirects
Content Processing
Content Type Detection: Identify if final destination is HTML, image, or PDF
Image Extraction: Download images from web pages or direct image links
HTML Parsing: Extract embedded images or time information from HTML
OCR Implementation
Google Cloud Vision API: Primary OCR service for Hebrew text
Image Preprocessing: Optimize images for OCR accuracy
Text Extraction: Extract all text from invitation images
Time Parsing Logic
Hebrew Time Formats: Parse various Hebrew time representations
Time Range Detection: Identify start and end times (19:00-21:00)
Single Time Handling: Default to 2-hour duration for start-time-only events
Validation: Ensure extracted times are reasonable

Implementation Specifications
Technology Stack
# Core Dependencies
google-auth==2.23.3
google-api-python-client==2.102.0
google-cloud-vision==3.4.4
google-cloud-storage==2.10.0
requests==2.31.0
beautifulsoup4==4.12.2
Pillow==10.0.1
python-dateutil==2.8.2

Project Structure
newsletter-automation/
├── main.py                 # Cloud Function entry point
├── newsletter_processor.py # Core processing logic
├── email_handler.py        # Gmail API integration
├── calendar_handler.py     # Calendar API integration
├── link_resolver.py        # MailChimp redirect resolution
├── ocr_processor.py        # Image OCR and time extraction
├── text_parser.py          # Hebrew text parsing utilities
├── config.py              # Configuration and constants
├── requirements.txt       # Python dependencies
└── tests/                 # Unit tests

Configuration Management
# Environment Variables
GMAIL_SENDER_EMAIL = "sharon.orsh@56456773.mailchimpapp.com"
CALENDAR_NAME = "מייל פמיניסטי שבועי"
TIMEZONE = "Asia/Jerusalem"
DEFAULT_EVENT_DURATION = 120  # 2 hours in minutes
DEFAULT_START_TIME = "19:00"
MAX_EMAILS_TO_PROCESS = 10


Core Function Specifications
1. Main Cloud Function (main.py)
def newsletter_processor(request):
    """
    Main Cloud Function entry point
    Triggered weekly by Cloud Scheduler
    """
    # Initialize API clients
    # Process unread newsletters
    # Create calendar events
    # Return processing summary

2. Link Resolution (link_resolver.py)
def resolve_mailchimp_redirect(url: str) -> Tuple[str, bytes]:
    """
    Resolve MailChimp tracking URL to final destination
    Returns: (final_url, content)
    """
    
def extract_images_from_content(content: bytes, base_url: str) -> List[str]:
    """
    Extract image URLs from HTML content
    Returns: List of image URLs
    """

3. OCR Processing (ocr_processor.py)
def extract_text_from_image(image_url: str) -> str:
    """
    Download image and extract text using Cloud Vision API
    Returns: Extracted text content
    """
    
def parse_hebrew_time(text: str) -> Optional[TimeInfo]:
    """
    Parse Hebrew time information from OCR text
    Returns: TimeInfo object with start_time, end_time, duration
    """

4. Event Processing (newsletter_processor.py)
def process_newsletter_email(email_content: str) -> List[EventData]:
    """
    Extract event information from newsletter content
    Returns: List of parsed events
    """
    
def enhance_event_with_time(event: EventData) -> EventData:
    """
    Attempt to extract accurate time from invitation links
    Returns: Enhanced event with actual times if found
    """


Time Extraction Logic
Hebrew Time Pattern Matching
TIME_PATTERNS = [
    r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})',  # 19:00-21:00
    r'(\d{1,2})\s*:\s*(\d{2})\s*-\s*(\d{1,2})\s*:\s*(\d{2})',  # 19 : 00 - 21 : 00
    r'מ(\d{1,2}):(\d{2})\s*עד\s*(\d{1,2}):(\d{2})',  # Hebrew format
    r'(\d{1,2}):(\d{2})',  # Single time
]

Time Handling Strategy
Full Range Found: Use exact start and end times
Start Time Only: Use start time + 2 hours duration
No Time Found: Fall back to default (19:00, 2 hours)
Invalid Time: Log error and use default

Deployment Architecture
Google Cloud Resources
# Cloud Function Configuration
Name: newsletter-processor
Runtime: Python 3.11
Memory: 512MB
Timeout: 540 seconds (9 minutes)
Trigger: HTTP (called by Cloud Scheduler)

# Cloud Scheduler Configuration
Name: weekly-newsletter-trigger
Schedule: "0 10 * * 1"  # Every Monday at 10:00 AM
Timezone: Asia/Jerusalem
Target: Cloud Function HTTP endpoint

IAM Permissions Required
Cloud Vision API: roles/cloudvision.admin
Gmail API: https://www.googleapis.com/auth/gmail.readonly
Calendar API: https://www.googleapis.com/auth/calendar
Cloud Storage: roles/storage.objectAdmin

Error Handling & Monitoring
Logging Strategy
# Structured logging for each processing step
- Email processing: Count of emails processed
- Link resolution: Success/failure rates
- OCR processing: Text extraction results
- Calendar events: Created/updated/skipped counts
- Errors: Detailed error information with context

Failure Scenarios
MailChimp Redirect Failure: Continue with default time
Image Download Failure: Skip OCR, use default time
OCR Failure: Log error, use default time
Calendar API Failure: Retry with exponential backoff
Invalid Event Data: Skip event, continue processing
Monitoring Dashboard
Cloud Function Metrics: Execution time, memory usage, error rates
API Usage: Gmail, Calendar, Vision API call counts
Success Rates: Email processing, OCR extraction, event creation
Cost Tracking: Monthly usage and costs

Testing Strategy
Unit Tests
Text Parsing: Hebrew date/time extraction
Link Resolution: MailChimp redirect handling
OCR Processing: Image text extraction
Event Creation: Calendar API integration
Integration Tests
End-to-End: Full newsletter processing pipeline
Error Scenarios: Handling of various failure cases
Performance: Processing time and memory usage
Production Testing
Dry Run Mode: Process emails without creating calendar events
Single Email Testing: Process one email at a time
Rollback Plan: Ability to revert to Apps Script if needed


