# Women's Rights Newsletter Automation

A Python-based Google Cloud Functions solution for automating the processing of feminist newsletter emails and creating calendar events. This system migrates and enhances the existing Google Apps Script functionality with new OCR-based time extraction features.

## 📋 Project Description

This project automates the processing of feminist newsletter emails from the Israeli Women's Rights movement. It extracts event information from Hebrew newsletter content and automatically creates calendar events, eliminating the need for manual event entry.

### 🎯 **What it does:**
- **Automatically processes** feminist newsletter emails from Gmail
- **Extracts event details** from Hebrew text (dates, times, locations, organizers)
- **Creates calendar events** in Google Calendar with proper timezone handling
- **Prevents duplicates** using smart duplicate detection
- **Runs on schedule** via Cloud Scheduler (Sunday, Monday, Tuesday at 7 PM Israel time)

### 🔧 **Key Features:**
- **Hebrew Text Processing**: Robust RTL text handling and Hebrew date/time parsing
- **Smart Duplicate Detection**: Prevents creating duplicate calendar events
- **Multi-Source Support**: Processes both direct newsletters and forwarded emails
- **Cloud-Native**: Deployed as a Google Cloud Function with automatic scaling
- **Comprehensive Logging**: Detailed processing statistics and error tracking

### 🚀 **Current Status:**
- ✅ **Fully Deployed**: Cloud Function is live and operational
- ✅ **Automated Scheduling**: Runs 3x per week via Cloud Scheduler
- ✅ **OAuth Integration**: Secure authentication with Gmail and Calendar APIs
- ✅ **Production Ready**: Processing real newsletter emails and creating events

## 🚀 Features

### Core Functionality (Migrated from Apps Script)
- **Email Processing**: Gmail API integration for reading newsletter emails
- **Hebrew Text Processing**: Robust Unicode handling for RTL text
- **Event Extraction**: Parse event blocks using improved regex patterns
- **Duplicate Prevention**: Enhanced duplicate detection logic
- **Calendar Integration**: Google Calendar API for event creation
- **Timezone Handling**: Proper Israel/Jerusalem timezone support

### New OCR-Based Features (Planned)
- **MailChimp Redirect Resolution**: Follow tracking URLs to final destinations
- **Image OCR Processing**: Extract time information from invitation images
- **Time Extraction**: Parse Hebrew time formats from images
- **Enhanced Event Data**: More accurate event times and details

## 📁 Project Structure

```
feminist-newsletter/
├── main.py                  # Cloud Function entry point
├── newsletter_processor.py  # Core processing logic
├── email_handler.py         # Gmail API integration
├── calendar_handler.py      # Calendar API integration
├── text_parser.py           # Hebrew text parsing utilities
├── config.py                # Configuration and constants
├── requirements.txt         # Python dependencies
├── tests/                   # All test scripts (test_*.py)
│   ├── test_core_functionality.py
│   ├── test_time_extraction.py
│   ├── ...
├── debug/                   # All debug scripts (debug_*.py)
│   ├── debug_link_extraction.py
│   ├── debug_july10_link.py
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

2. **Service Account Permissions**:
   - Gmail: `https://www.googleapis.com/auth/gmail.readonly`
   - Calendar: `https://www.googleapis.com/auth/calendar`
   - Vision: `roles/cloudvision.admin`

3. **Environment Variables**:
   ```bash
   CALENDAR_NAME="מייל פמיניסטי שבועי"
   TIMEZONE="Asia/Jerusalem"
   GMAIL_SENDER_EMAIL="sharon.orsh@56456773.mailchimpapp.com"
   DEFAULT_EVENT_DURATION=120
   DEFAULT_START_TIME="19:00"
   MAX_EMAILS_TO_PROCESS=10
   ```

## 🧪 Testing

All test scripts are now located in the `tests/` directory. To run a specific test, use:
```bash
python tests/test_core_functionality.py
```
Or run all tests:
```bash
python -m unittest discover tests
```

This will test:
- Text cleaning and normalization
- Event block extraction
- Event parsing functions
- Full processing pipeline
- Edge cases and error handling

## 🐞 Debugging

All debug scripts are now located in the `debug/` directory. For example, to debug the July 10th invitation link:
```bash
python debug/debug_july10_link.py
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
- `check_for_duplicate_event()`: Duplicate detection
- `create_calendar_event()`: Calendar event creation

### 3. Email Handler (`email_handler.py`)
Gmail API integration:
- `GmailHandler`: Gmail operations class
- `authenticate()`: API authentication
- `get_unread_newsletters()`: Fetch unread emails
- `_extract_body_content()`: Extract email content
- `get_recent_newsletters()`: Get recent emails for testing

### 4. Calendar Handler (`calendar_handler.py`)
Google Calendar API integration:
- `CalendarHandler`: Calendar operations class
- `authenticate()`: API authentication
- `_get_or_create_calendar()`: Find or create target calendar
- `create_event()`: Create calendar events
- `check_for_duplicate_event()`: Duplicate detection
- `cleanup_test_events()`: Clean up test events

### 5. Main Function (`main.py`)
Cloud Function entry point:
- `newsletter_processor()`: Main processing function
- Orchestrates the entire workflow
- Handles authentication, email processing, and event creation
- Returns processing statistics

## 🔧 Configuration

### Core Settings (`config.py`)
```python
CONFIG = {
    'calendar_name': 'מייל פמיניסטי שבועי',
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

### Google Cloud Functions
1. **Deploy the function**:
   ```bash
   gcloud functions deploy newsletter-processor \
     --runtime python311 \
     --trigger-http \
     --allow-unauthenticated \
     --memory 512MB \
     --timeout 540s
   ```

2. **Set up Cloud Scheduler**:
   ```bash
   gcloud scheduler jobs create http weekly-newsletter-trigger \
     --schedule="0 10 * * 1" \
     --time-zone="Asia/Jerusalem" \
     --uri="YOUR_FUNCTION_URL" \
     --http-method=POST
   ```

### Local Development
For local testing and development:
```bash
python main.py
```

## 📊 Processing Flow

1. **Email Retrieval**: Fetch unread emails from the newsletter sender
2. **Content Processing**: Clean and normalize email content
3. **Event Extraction**: Parse event blocks from newsletter content
4. **Link Extraction**: Extract relevant links from HTML content
5. **Event Parsing**: Parse individual events with dates, titles, locations
6. **Duplicate Check**: Check for existing events to avoid duplicates
7. **Calendar Creation**: Create calendar events with full metadata
8. **Statistics**: Return processing summary and statistics

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
    is_virtual=False
)
```

## 🐛 Error Handling

The system includes comprehensive error handling:
- **Authentication failures**: Graceful handling of API auth issues
- **Email processing errors**: Continue processing other emails
- **Event parsing errors**: Skip invalid events, continue processing
- **Calendar API errors**: Retry logic and fallback handling
- **Invalid data**: Validation and sanitization of input data

## 📈 Monitoring & Logging

- **Structured logging**: Detailed logs for each processing step
- **Processing statistics**: Count of emails processed, events created, etc.
- **Error tracking**: Comprehensive error logging with context
- **Performance metrics**: Processing time and resource usage

## 🔮 Future Enhancements

### OCR-Based Time Extraction (Next Phase)
- **Link Resolution**: Follow MailChimp redirects to final destinations
- **Image Processing**: Download and process invitation images
- **OCR Integration**: Use Google Cloud Vision API for text extraction
- **Time Parsing**: Extract accurate event times from images
- **Enhanced Events**: More precise event timing and details

### Additional Features
- **Webhook Support**: Real-time processing of new emails
- **Email Templates**: Customizable event descriptions
- **Analytics Dashboard**: Processing statistics and insights
- **Multi-language Support**: Support for additional languages
- **Advanced Filtering**: More sophisticated event filtering

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the test script for functionality verification
2. Review the logging output for error details
3. Verify Google Cloud API permissions
4. Ensure proper environment variable configuration 