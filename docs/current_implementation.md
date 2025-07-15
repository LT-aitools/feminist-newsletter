# Current Implementation Documentation

## Overview

This document describes the current Python-based implementation of the Women's Rights Newsletter Automation system, which has been migrated from Google Apps Script to Google Cloud Functions with enhanced OCR capabilities.

## Architecture

### System Components
```
Gmail API → Cloud Function → [MailChimp Redirect Resolution] → [Vision API OCR] → Calendar API
    ↓
Cloud Scheduler (Weekly Trigger) → Cloud Function → Google Calendar
```

### Core Modules

#### 1. Main Function (`main.py`)
**Purpose**: Cloud Function entry point and orchestration
**Key Functions**:
- `newsletter_processor(request)`: Main processing function
- `create_event_body(event, config)`: Format event data for Calendar API
- `create_event_description(event)`: Generate event descriptions
- `create_response(stats, message)`: Format response for Cloud Function

**Processing Flow**:
1. Initialize service account authentication
2. Set up Gmail, Calendar, and Vision API clients
3. Search for recent newsletter emails (last 7 days)
4. Process each email through the newsletter processor
5. Create calendar events for extracted events
6. Return processing statistics

#### 2. Newsletter Processor (`newsletter_processor.py`)
**Purpose**: Core event extraction and processing logic
**Key Classes**:
- `NewsletterProcessor`: Main processing class
- `EventData`: Data structure for parsed events

**Key Functions**:
- `process_newsletter_email(plain_text, html_content)`: Extract events from email
- `_parse_event_block(block)`: Parse individual event blocks
- `_enhance_event_with_time(event)`: Extract time from invitation links
- `check_for_duplicate_event(title, date)`: Duplicate detection
- `create_calendar_event(event)`: Create calendar events

#### 3. Text Parser (`text_parser.py`)
**Purpose**: Hebrew text processing and event extraction
**Key Functions**:
- `normalize_plain_text(content)`: Clean email content
- `extract_event_blocks_from_newsletter(content)`: Split into event blocks
- `extract_date(block)`: Parse Hebrew date format (ה7/7)
- `extract_title(block)`: Extract event titles using multiple patterns
- `extract_location(block)`: Identify event locations
- `extract_organizer(block)`: Extract organizing bodies

#### 4. Email Handler (`email_handler.py`)
**Purpose**: Gmail API integration
**Key Classes**:
- `GmailHandler`: Gmail operations class

**Key Functions**:
- `authenticate()`: Service account authentication
- `get_unread_newsletters()`: Fetch unread emails
- `get_recent_newsletters()`: Get recent emails (regardless of read status)
- `_extract_body_content(message)`: Extract email content
- `mark_as_processed(message_id)`: Mark email as processed

#### 5. Calendar Handler (`calendar_handler.py`)
**Purpose**: Google Calendar API integration
**Key Classes**:
- `CalendarHandler`: Calendar operations class

**Key Functions**:
- `authenticate()`: Service account authentication
- `create_event(event_data)`: Create calendar events
- `check_for_duplicate_event(title, date)`: Duplicate detection
- `cleanup_test_events()`: Clean up test events

#### 6. Time Extractor (`time_extractor.py`)
**Purpose**: OCR time extraction from invitation images
**Key Classes**:
- `TimeExtractor`: OCR processing class

**Key Functions**:
- `extract_time_from_invitation_link(mailchimp_url)`: Process invitation links
- `_follow_mailchimp_redirect(url)`: Follow redirects to final content
- `_extract_time_from_image(image_bytes)`: Extract times from images using Vision API
- `_find_time_in_text(text)`: Parse Hebrew time formats
- `_download_image(image_url)`: Download images for processing

#### 7. Service Account Auth (`service_account_auth.py`)
**Purpose**: Authentication management for all Google APIs
**Key Classes**:
- `ServiceAccountAuth`: Service account authentication class

**Key Functions**:
- `__init__()`: Initialize with service account credentials
- `get_gmail_service(user_email)`: Gmail API authentication
- `get_calendar_service()`: Calendar API authentication
- `get_vision_client()`: Vision API authentication

#### 8. Configuration (`config.py`)
**Purpose**: Centralized configuration management
**Key Components**:
- `CONFIG`: Main configuration dictionary
- `TIME_PATTERNS`: Hebrew time extraction patterns
- `EVENT_TYPES`: Event type mappings
- `CITIES`: Location detection cities
- `FOOTER_PATTERNS`: Email footer removal patterns

## Data Flow

### 1. Email Processing
```
Gmail API → Email Handler → Text Parser → Newsletter Processor
```

1. **Email Retrieval**: Search for recent newsletter emails from configured senders
2. **Content Extraction**: Extract plain text and HTML content from emails
3. **Text Normalization**: Remove footers and clean up content
4. **Event Block Extraction**: Split content into individual event blocks
5. **Event Parsing**: Extract date, title, location, and organizer information

### 2. Time Extraction
```
Invitation Link → MailChimp Redirect → Content Download → Vision API OCR → Time Parsing
```

1. **Link Detection**: Find "בהזמנה" links in event descriptions
2. **Redirect Following**: Follow MailChimp redirects to final content
3. **Content Download**: Download images or extract HTML content
4. **OCR Processing**: Use Google Cloud Vision API for text extraction
5. **Time Parsing**: Apply Hebrew time patterns to extracted text

### 3. Calendar Integration
```
Event Data → Duplicate Check → Calendar API → Event Creation
```

1. **Duplicate Detection**: Check for existing events on the same date
2. **Event Formatting**: Format event data for Calendar API
3. **Event Creation**: Create calendar events with verified times
4. **Response Handling**: Handle success/failure responses

## Configuration

### Environment Variables
```bash
GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
CALENDAR_NAME="Feminist Newsletter Events"
CALENDAR_ID="5b6f7ad099565ddfa52d0bfe297cedc40ea0321360104f2b61782b5e69480270@group.calendar.google.com"
TIMEZONE="Asia/Jerusalem"
GMAIL_SENDER_EMAIL="sharon.orsh@56456773.mailchimpapp.com"
DEFAULT_EVENT_DURATION=120
DEFAULT_START_TIME="19:00"
MAX_EMAILS_TO_PROCESS=10
```

### Core Configuration
```python
CONFIG = {
    'calendar_name': 'Feminist Newsletter Events',
    'calendar_id': '5b6f7ad099565ddfa52d0bfe297cedc40ea0321360104f2b61782b5e69480270@group.calendar.google.com',
    'use_service_account': True,
    'timezone': 'Asia/Jerusalem',
    'newsletter_sender': 'sharon.orsh@56456773.mailchimpapp.com',
    'gmail_account': 'hello@letstalkaitools.com',
    'default_duration': 120,  # 2 hours
    'default_start_time': '19:00',
    'max_emails_to_process': 10,
    'skip_past_events': True
}
```

## Error Handling

### Graceful Degradation
- **MailChimp Redirect Failure**: Continue with default time
- **Image Download Failure**: Skip OCR, use default time
- **OCR Failure**: Log error, use default time
- **Calendar API Failure**: Retry with exponential backoff
- **Invalid Event Data**: Skip event, continue processing

### Logging Strategy
- **Structured Logging**: Each processing step logged with context
- **Error Tracking**: Detailed error information with stack traces
- **Performance Metrics**: Processing time and success rates
- **Statistics**: Email processing, OCR extraction, event creation counts

## Performance Characteristics

### Processing Speed
- **Email Processing**: ~5 seconds per email
- **Time Extraction**: ~3-8 seconds per event with invitation link
- **Calendar Creation**: ~1-2 seconds per event
- **Total Processing**: ~15 seconds for 3 emails with 14 events

### Resource Usage
- **Memory**: 512MB allocated (Cloud Function)
- **Timeout**: 540 seconds (9 minutes)
- **API Quotas**: Respects Gmail, Calendar, and Vision API limits

### Success Rates
- **OCR Success**: ~60% of events with invitation links
- **Duplicate Detection**: 100% effective
- **Error Recovery**: 100% graceful degradation

## Deployment

### Google Cloud Functions
- **Runtime**: Python 3.11
- **Memory**: 512MB
- **Timeout**: 540 seconds
- **Generation**: 1st gen (--no-gen2 flag)
- **Trigger**: HTTP (called by Cloud Scheduler)

### Cloud Scheduler
- **Schedule**: "0 19 * * 0,1,2" (Sunday, Monday, Tuesday at 7 PM)
- **Timezone**: Asia/Jerusalem
- **Target**: Cloud Function HTTP endpoint

### Service Account Setup
- **Account**: Configured with domain-wide delegation
- **Permissions**: Gmail, Calendar, and Vision API access
- **Authentication**: Automatic credential management

## Testing

### Test Files
- `test_core_functionality.py`: Core functionality tests
- `test_recent_emails.py`: Recent email processing tests
- `test_time_extraction.py`: OCR time extraction tests
- `test_complete_workflow.py`: End-to-end workflow tests

### Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: API integration testing
- **End-to-End Tests**: Complete workflow testing
- **Production Testing**: Real email processing validation

## Migration from Google Apps Script

### Key Changes
1. **Language**: JavaScript → Python
2. **Platform**: Google Apps Script → Google Cloud Functions
3. **OCR**: Tesseract → Google Cloud Vision API
4. **Authentication**: OAuth → Service Account
5. **Deployment**: Manual → Automated via Cloud Scheduler

### Benefits
- **Better Hebrew Text Processing**: Improved RTL text handling
- **Enhanced OCR**: Google Cloud Vision API for better accuracy
- **Scalability**: Cloud-native architecture
- **Reliability**: Service account authentication prevents token expiration
- **Monitoring**: Better logging and error tracking

### Compatibility
- **Email Processing**: Maintains same logic and patterns
- **Event Extraction**: Enhanced with better text parsing
- **Calendar Integration**: Same event format and structure
- **Duplicate Detection**: Improved algorithm 