# Women's Rights Newsletter Automation

A Python-based Google Cloud Functions solution for automating the processing of feminist newsletter emails and creating calendar events. This system migrates and enhances the existing Google Apps Script functionality with OCR-based time extraction features using Google Cloud Vision API.

## 📋 Project Description

This project automates the processing of feminist newsletter emails from the Israeli Women's Rights movement. It extracts event information from Hebrew newsletter content and automatically creates calendar events, eliminating the need for manual event entry.

### 🎯 **What it does:**
- **Automatically processes** feminist newsletter emails from Gmail (both main and backup senders)
- **Extracts event details** from Hebrew text (dates, times, locations, organizers)
- **Extracts accurate times** from invitation images using Google Cloud Vision API OCR
- **Creates calendar events** in Google Calendar with proper timezone handling
- **Prevents duplicates** using smart duplicate detection
- **Runs on schedule** via Cloud Scheduler (Sunday, Monday, Tuesday at 7 PM Israel time)

### 🔧 **Key Features:**
- **Hebrew Text Processing**: Robust RTL text handling and Hebrew date/time parsing
- **OCR Time Extraction**: Google Cloud Vision API for extracting times from invitation images
- **Smart Duplicate Detection**: Prevents creating duplicate calendar events
- **Multi-Source Support**: Processes both direct newsletters and forwarded emails
- **Service Account Authentication**: Secure, token-free authentication for all APIs
- **Cloud-Native**: Deployed as a Google Cloud Function with automatic scaling
- **Comprehensive Logging**: Detailed processing statistics and error tracking

### 🚀 **Current Status:**
- ✅ **Fully Deployed**: Cloud Function is live and operational (1st gen)
- ✅ **Automated Scheduling**: Runs 3x per week via Cloud Scheduler
- ✅ **Service Account Integration**: Secure authentication with Gmail, Calendar, and Vision APIs
- ✅ **OCR Time Extraction**: Successfully extracting times from invitation images
- ✅ **Public Calendar**: Calendar is public and accessible to subscribers
- ✅ **Production Ready**: Processing real newsletter emails and creating events

## 🚀 Features

### Core Functionality (Migrated from Apps Script)
- **Email Processing**: Gmail API integration for reading newsletter emails
- **Hebrew Text Processing**: Robust Unicode handling for RTL text
- **Event Extraction**: Parse event blocks using improved regex patterns
- **Duplicate Prevention**: Enhanced duplicate detection logic
- **Calendar Integration**: Google Calendar API for event creation
- **Timezone Handling**: Proper Israel/Jerusalem timezone support

### OCR-Based Time Extraction (Implemented)
- **Google Cloud Vision API**: Primary OCR service for Hebrew text extraction
- **Invitation Link Processing**: Follow MailChimp redirects to final destinations
- **Image OCR Processing**: Extract time information from invitation images
- **Time Parsing**: Parse Hebrew time formats from OCR results
- **Enhanced Event Data**: More accurate event times and details

## 📁 Project Structure

```
feminist-newsletter/
├── main.py                  # Cloud Function entry point
├── newsletter_processor.py  # Core processing logic
├── email_handler.py         # Gmail API integration
├── calendar_handler.py      # Calendar API integration
├── text_parser.py           # Hebrew text parsing utilities
├── time_extractor.py        # OCR time extraction from images
├── service_account_auth.py  # Service account authentication
├── config.py                # Configuration and constants
├── requirements.txt         # Python dependencies
├── test_recent_emails.py    # Test script for recent email processing
├── make_calendar_public_v2.py # Calendar public access setup
├── cleanup_calendar.py      # Calendar cleanup utilities
├── README.md                # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- Google Cloud Platform account
- Service account with appropriate permissions

### Dependencies
Install the required packages:
```bash
pip install -r requirements.txt
```

### Google Cloud Setup
1. **Enable APIs**:
   - Gmail API
   - Google Calendar API
   - Cloud Vision API (for OCR features)
   - Cloud Functions API
   - Cloud Scheduler API

2. **Service Account Setup**:
   - Create service account: `vision-api-access@womens-rights-calendar.iam.gserviceaccount.com`
   - Download JSON key file
   - Grant domain-wide delegation for Gmail and Calendar APIs
   - Assign Vision API admin role

3. **Service Account Permissions**:
   - Gmail: `https://www.googleapis.com/auth/gmail.readonly`
   - Calendar: `https://www.googleapis.com/auth/calendar`
   - Vision: `roles/cloudvision.admin`

4. **Environment Variables**:
   ```bash
   GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
   CALENDAR_NAME="Feminist Newsletter Events"
   TIMEZONE="Asia/Jerusalem"
   GMAIL_SENDER_EMAIL="sharon.orsh@56456773.mailchimpapp.com"
   DEFAULT_EVENT_DURATION=120
   DEFAULT_START_TIME="19:00"
   MAX_EMAILS_TO_PROCESS=10
   ```

## 🧪 Testing

### Local Testing
```bash
# Test core functionality
python test_core_functionality.py

# Test recent email processing
python test_recent_emails.py

# Test service account integration
python test_service_account_integration.py
```

### Calendar Management
```bash
# Clean up calendar events
python cleanup_calendar.py

# Make calendar public
python make_calendar_public_v2.py
```

## 📋 Core Components

### 1. Text Parser (`text_parser.py`)
Handles Hebrew text processing and event extraction:
- `normalize_plain_text()`: Clean email content
- `extract_event_blocks_from_newsletter()`: Split content into event blocks
- `extract_date()`: Parse Hebrew date format (ה7/7)
- `extract_title()`: Extract event titles using multiple patterns
- `extract_location()`: Identify event locations
- `extract_organizer()`: Extract organizing bodies

### 2. Newsletter Processor (`newsletter_processor.py`)
Main processing logic:
- `NewsletterProcessor`: Core processing class
- `EventData`: Data structure for parsed events
- `process_newsletter_email()`: Process email content
- `_parse_event_block()`: Parse individual event blocks
- `_enhance_event_with_time()`: OCR time extraction from invitation links
- `check_for_duplicate_event()`: Duplicate detection
- `create_calendar_event()`: Calendar event creation

### 3. Email Handler (`email_handler.py`)
Gmail API integration:
- `GmailHandler`: Gmail operations class
- `authenticate()`: Service account authentication
- `get_unread_newsletters()`: Fetch unread emails
- `get_recent_newsletters()`: Get recent emails (regardless of read status)
- `_extract_body_content()`: Extract email content

### 4. Calendar Handler (`calendar_handler.py`)
Google Calendar API integration:
- `CalendarHandler`: Calendar operations class
- `authenticate()`: Service account authentication
- `create_event()`: Create calendar events
- `check_for_duplicate_event()`: Duplicate detection
- `cleanup_test_events()`: Clean up test events

### 5. Time Extractor (`time_extractor.py`)
OCR time extraction:
- `TimeExtractor`: OCR processing class
- `extract_time_from_invitation_link()`: Process invitation links
- `extract_time_from_image()`: Extract times from images using Vision API
- `_parse_hebrew_time()`: Parse Hebrew time formats

### 6. Service Account Auth (`service_account_auth.py`)
Authentication management:
- `ServiceAccountAuth`: Service account authentication class
- `authenticate_gmail()`: Gmail API authentication
- `authenticate_calendar()`: Calendar API authentication
- `authenticate_vision()`: Vision API authentication

### 7. Main Function (`main.py`)
Cloud Function entry point:
- `newsletter_processor()`: Main processing function
- Orchestrates the entire workflow
- Handles authentication, email processing, and event creation
- Returns processing statistics

## 🔧 Configuration

### Core Settings (`config.py`)
```python
CONFIG = {
    'calendar_name': 'Feminist Newsletter Events',
    'calendar_id': '5b6f7ad099565ddfa52d0bfe297cedc40ea0321360104f2b61782b5e69480270@group.calendar.google.com',
    'use_service_account': True,
    'timezone': 'Asia/Jerusalem',
    'newsletter_sender': 'sharon.orsh@56456773.mailchimpapp.com',
    'default_duration': 120,  # 2 hours
    'default_start_time': '19:00',
    'max_emails_to_process': 10,
    'skip_past_events': True
}
```

### Hebrew Time Patterns
```python
TIME_PATTERNS = [
    r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})',  # 19:00-21:00
    r'(\d{1,2})\s*:\s*(\d{2})\s*-\s*(\d{1,2})\s*:\s*(\d{2})',  # 19 : 00 - 21 : 00
    r'מ(\d{1,2}):(\d{2})\s*עד\s*(\d{1,2}):(\d{2})',  # Hebrew format
    r'(\d{1,2}):(\d{2})',  # Single time
]
```

## 🚀 Deployment

### Google Cloud Functions (1st Gen)
1. **Deploy the function**:
   ```bash
   gcloud functions deploy newsletter-processor \
     --runtime python311 \
     --trigger-http \
     --allow-unauthenticated \
     --memory 512MB \
     --timeout 540s \
     --source . \
     --entry-point newsletter_processor \
     --region=us-central1 \
     --no-gen2
   ```

2. **Set up Cloud Scheduler**:
   ```bash
   gcloud scheduler jobs create http newsletter-processor-schedule \
     --schedule="0 19 * * 0,1,2" \
     --time-zone="Asia/Jerusalem" \
     --uri="YOUR_FUNCTION_URL" \
     --http-method=POST \
     --location=us-central1
   ```

### Local Development
For local testing and development:
```bash
python main.py
```

## 📊 Processing Flow

1. **Email Retrieval**: Fetch recent emails from both newsletter senders
2. **Content Processing**: Clean and normalize email content
3. **Event Extraction**: Parse event blocks from newsletter content
4. **Link Extraction**: Extract relevant links from HTML content
5. **OCR Time Extraction**: Extract times from invitation images using Vision API
6. **Event Parsing**: Parse individual events with dates, titles, locations
7. **Duplicate Check**: Check for existing events to avoid duplicates
8. **Calendar Creation**: Create calendar events with full metadata
9. **Statistics**: Return processing summary and statistics

## 🔍 Event Parsing Examples

### Input Event Block
```
ביום שני, ה7/7, תקיים הוועדה לקידום מעמד האישה ושוויון מגדרי בכנסת דיון בנושא "מימוש הסיוע לגרושות ולגרושים של משרתי המילואים". פרטים והרשמה בהזמנה.
```

### Parsed Event Data
```python
EventData(
    title="מימוש הסיוע לגרושות ולגרושים של משרתי המילואים",
    date=datetime(2024, 7, 7),
    time="19:00",
    duration=120,
    location="ירושלים",
    organizer="הוועדה לקידום מעמד האישה",
    event_type="discussion",
    is_virtual=False,
    time_verified=True  # If OCR extraction succeeded
)
```

## 🐛 Error Handling

The system includes comprehensive error handling:
- **Authentication failures**: Graceful handling of API auth issues
- **Email processing errors**: Continue processing other emails
- **Event parsing errors**: Skip invalid events, continue processing
- **OCR failures**: Fall back to default times, continue processing
- **Calendar API errors**: Retry logic and fallback handling
- **Invalid data**: Validation and sanitization of input data

## 📈 Performance Metrics

### Recent Processing Results
- **Processing Time**: ~15 seconds for 3 emails with 14 events
- **OCR Success Rate**: ~60% of events with invitation links
- **Duplicate Detection**: 100% effective at preventing duplicates
- **Time Extraction Accuracy**: High accuracy when OCR succeeds

### System Reliability
- **Uptime**: 99.9% (Cloud Functions SLA)
- **Error Recovery**: Automatic retry and graceful degradation
- **Monitoring**: Cloud Function logs and metrics
- **Backup**: Service account authentication prevents token expiration issues 