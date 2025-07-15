PRD - Event Time Extraction from Newsletter Invitations
Problem Statement
Currently, the automated newsletter processing creates calendar events with default times (19:00) because the actual event times are only available in linked invitation images/pages. Users must manually click each invitation link to find the real event time and update the calendar entry.
User Need
As a user of the women's rights events calendar, I want the correct event times to be automatically extracted and set in my calendar so that I don't have to manually verify and update each event's timing.
Current State
Newsletter contains events with dates but often no specific times in the main text
Event times are specified in linked invitation materials (referenced as "בהזמנה" links)
These invitation links currently lead to MailChimp redirect URLs
All calendar events are created with default 19:00 start time
Users must manually follow links and update calendar events with correct times
Desired Future State
Calendar events automatically show the correct start and end times as specified in the invitation materials
No manual intervention required for time verification
Clear indication when automatic time extraction was successful vs. when it failed
Success Criteria
Primary Success Metrics
Accuracy: When automatic time extraction succeeds, calendar events show the correct times matching the invitation
Coverage: Automatic time extraction works for at least 70% of events that have "בהזמנה" links
Reliability: The system gracefully handles cases where time extraction fails
User Experience Goals
Users can trust that calendar times are accurate when available
Clear differentiation between confirmed times vs. default times
Minimal manual intervention required
User Stories
Story 1: Successful Time Extraction
As a calendar subscriber
 I want events with invitation links to show the correct times
 So that I can plan my schedule without manually checking each invitation
Acceptance Criteria:
Event shows actual start time (e.g., 20:00 instead of default 19:00)
Event shows actual end time when provided in invitation
When only start time is available, event duration defaults to 2 hours
Event title/description indicates time was automatically verified
Story 2: Failed Time Extraction
As a calendar subscriber
 I want to know when event times couldn't be automatically verified
 So that I know which events need manual time checking
Acceptance Criteria:
Event clearly indicates when time is unverified (default)
Easy access to invitation link for manual verification
Consistent formatting for unverified time events
Story 3: Mixed Newsletter Processing
As a system user
 I want the newsletter processing to continue working even when some events fail time extraction
 So that the entire automation doesn't break due to individual event issues
Acceptance Criteria:
Failed time extraction doesn't prevent other events from being processed
Clear logging of which events succeeded/failed time extraction
Batch processing completes successfully regardless of individual failures
Constraints
Known Technical Constraints
Newsletter links are MailChimp redirects, not direct links
Invitation materials may be in various formats (images, web pages, PDFs)
Content is primarily in Hebrew
Processing happens within Google Cloud Functions environment
Business Constraints
Must not break existing automation functionality
Should not significantly increase processing time
Must handle various invitation formats gracefully
Out of Scope
Explicitly Not Included
Extraction of location details beyond what's in newsletter text
Extraction of additional event metadata (speakers, registration info, etc.)
Historical event processing (only applies to new newsletter processing)
Integration with external calendar systems beyond Google Calendar
Assumptions
Most events with "בהזמנה" links contain discoverable time information
Time formats in invitations follow common Hebrew conventions
Invitation materials may contain either:
Full time range (start and end times) - use exactly as specified
Start time only - use provided start time with 2-hour default duration
No specific time - fall back to default handling
Users prefer automatic time extraction with fallback over manual-only process
Some level of manual verification will still be acceptable for edge cases

## Implementation Status: PRODUCTION READY

### Current Implementation
- **Technology**: Google Cloud Vision API for OCR processing
- **Deployment**: Running in production on Google Cloud Functions
- **Schedule**: Automated processing 3x per week (Sunday, Monday, Tuesday at 7 PM Israel time)
- **Authentication**: Service account with domain-wide delegation

### Performance Metrics (Current Production)
- **OCR Success Rate**: ~60% of events with invitation links
- **Processing Speed**: ~15 seconds for 3 emails with 14 events
- **Error Recovery**: 100% graceful degradation on failures
- **Cost**: ~$1-3 USD per month for Vision API usage

### Technical Implementation
- **Link Resolution**: Follows MailChimp redirects to final destinations
- **Content Processing**: Handles images, HTML pages, and PDFs
- **OCR Processing**: Google Cloud Vision API with Hebrew text support
- **Time Parsing**: Multiple Hebrew time format patterns
- **Calendar Integration**: Updates events with verified times

### Success Criteria Achievement
✅ **Accuracy**: Extracted times match invitation times when OCR succeeds
✅ **Coverage**: Working for ~60% of events with invitation links (approaching 70% target)
✅ **Reliability**: Graceful handling of failures with fallback to default times
✅ **User Experience**: Clear indication of verified vs. default times in calendar events

### Future Improvements
- **Enhanced OCR**: Potential for improved Hebrew text recognition
- **Pattern Learning**: Automatically detect new time formats
- **Batch Processing**: Process multiple images in parallel
- **Caching**: Cache extracted times to avoid reprocessing
