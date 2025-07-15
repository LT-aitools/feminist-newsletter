# Time Extraction Feature Guide

## Overview

The Time Extraction feature automatically extracts accurate event times from invitation images linked in newsletter emails using Google Cloud Vision API. This eliminates the need for manual time verification and ensures calendar events show the correct start times.

## How It Works

### 1. Link Detection
- The system scans newsletter emails for links labeled "בהזמנה" (invitation)
- These links are typically MailChimp tracking URLs that redirect to invitation images

### 2. Redirect Following
- The system follows MailChimp redirects to get the actual image URL
- Handles both direct image links and HTML pages containing images
- Supports multiple content types: images, HTML pages, and PDFs

### 3. Image Processing
- Downloads invitation images from the resolved URLs
- Uses Google Cloud Vision API for OCR processing
- No local image preprocessing required (handled by Vision API)

### 4. Time Pattern Recognition
- Searches for common Hebrew time formats:
  - `19:00` (24-hour format)
  - `19 : 00` (with spaces)
  - `19.00` (with dots)
  - Time ranges like `19:00-21:00`
  - Hebrew formats like `מ19:00 עד 21:00`
- Validates extracted times (0-23 hours, 0-59 minutes)

### 5. Calendar Integration
- Updates event times with extracted values
- Marks events as "time verified" in calendar descriptions
- Falls back to default times (19:00) if extraction fails

## Configuration

### Time Patterns
Time patterns are defined in `config.py`:

```python
TIME_PATTERNS = [
    r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})',  # 19:00-21:00
    r'(\d{1,2})\s*:\s*(\d{2})\s*-\s*(\d{1,2})\s*:\s*(\d{2})',  # 19 : 00 - 21 : 00
    r'מ(\d{1,2}):(\d{2})\s*עד\s*(\d{1,2}):(\d{2})',  # Hebrew format
    r'(\d{1,2}):(\d{2})',  # Single time
]
```

### Default Settings
- Default start time: `19:00`
- Default duration: `120` minutes (2 hours)
- Timezone: `Asia/Jerusalem`

### Google Cloud Vision API Setup
1. **Enable Vision API** in Google Cloud Console
2. **Service Account Permissions**: Ensure service account has `roles/cloudvision.admin`
3. **Authentication**: Uses service account credentials automatically

## Usage

### Automatic Processing
Time extraction happens automatically during newsletter processing:

```python
from newsletter_processor import NewsletterProcessor

processor = NewsletterProcessor()
events = processor.process_newsletter_email(email_content, html_content)

# Events now have time_verified field
for event in events:
    if event.time_verified:
        print(f"✅ Verified time: {event.time}")
    else:
        print(f"⚠️ Default time: {event.time}")
```

### Manual Time Extraction
Extract time from a specific invitation link:

```python
from time_extractor import TimeExtractor

extractor = TimeExtractor()
mailchimp_url = "https://wordpress.us13.list-manage.com/track/click?..."
extracted_time = extractor.extract_time_from_invitation_link(mailchimp_url)

if extracted_time:
    print(f"Extracted time: {extracted_time}")
else:
    print("Time extraction failed")
```

### Updating Past Events
Update existing calendar events with time extraction:

```python
from update_past_events import PastEventUpdater

updater = PastEventUpdater()
result = updater.update_past_events(days_back=30)

if result["success"]:
    print(f"Updated {result['results']['updated_events']} events")
```

## Testing

### Run Time Extraction Tests
```bash
python test_time_extraction.py
```

### Run Complete Workflow Tests
```bash
python test_complete_workflow.py
```

### Test OCR Patterns
```python
from time_extractor import TimeExtractor

extractor = TimeExtractor()
sample_texts = [
    "האירוע יתקיים ביום שלישי בשעה 20:00",
    "שעת התחלה: 19:30 - שעת סיום: 21:30",
    "מ-18:00 עד 20:00"
]

for text in sample_texts:
    time = extractor._find_time_in_text(text)
    print(f"{text} -> {time}")
```

## Calendar Event Format

Events with verified times show:
```
✅ זמן מאומת: 20:00
```

Events with default times show:
```
⚠️ זמן משוער: 19:00 (זמן מדויק בהזמנה)
```

## Error Handling

### Graceful Degradation
- If time extraction fails, events use default times
- Processing continues even if individual events fail
- Clear logging indicates success/failure for each event

### Common Issues
1. **MailChimp redirects fail**: Check network connectivity
2. **Vision API quota exceeded**: Check API usage limits
3. **Image quality issues**: Vision API handles most image formats well
4. **Time format variations**: Add new patterns to `TIME_PATTERNS`

## Performance Considerations

### Processing Time
- Image download: ~2-5 seconds per image
- Vision API OCR: ~1-3 seconds per image
- Total time per event: ~3-8 seconds

### Rate Limiting
- Respects Vision API quotas and limits
- Implements timeouts (10s for redirects, 15s for images)
- Uses session reuse for efficiency

### Cost Considerations
- Vision API pricing: ~$1.50 per 1000 images
- Typical usage: ~10-20 images per week
- Monthly cost: ~$1-3 USD

## Dependencies

Required packages for time extraction:
```
google-cloud-vision==3.4.4
requests==2.31.0
Pillow==10.0.1
numpy==1.26.4
```

### Google Cloud Vision API Setup
1. **Enable the API**:
   ```bash
   gcloud services enable vision.googleapis.com
   ```

2. **Service Account Setup**:
   ```bash
   # Create service account (if not exists)
   gcloud iam service-accounts create vision-api-access \
     --display-name="Vision API Access"
   
   # Grant Vision API admin role
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:vision-api-access@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/cloudvision.admin"
   ```

3. **Download Service Account Key**:
   ```bash
   gcloud iam service-accounts keys create vision-api-key.json \
     --iam-account=vision-api-access@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

## Success Metrics

Based on the PRD requirements:
- **Accuracy**: Extracted times match invitation times
- **Coverage**: Works for 70%+ of events with invitation links
- **Reliability**: Graceful handling of failures

### Current Performance
- **OCR Success Rate**: ~60% of events with invitation links
- **Processing Speed**: ~15 seconds for 3 emails with 14 events
- **Error Recovery**: 100% graceful degradation on failures

## Troubleshooting

### Time Extraction Fails
1. Check Vision API is enabled: `gcloud services list --enabled | grep vision`
2. Verify service account permissions: Check IAM roles
3. Test with sample image: `python test_time_extraction.py`

### Calendar Events Not Updated
1. Check calendar permissions
2. Verify service account credentials
3. Review logs for authentication errors

### Vision API Issues
1. Check API quotas in Google Cloud Console
2. Verify billing is enabled for the project
3. Review API usage and error logs

## Future Enhancements

### Potential Improvements
1. **Machine Learning**: Train custom models for Hebrew text recognition
2. **Image Enhancement**: Better preprocessing for low-quality images
3. **Pattern Learning**: Automatically detect new time formats
4. **Batch Processing**: Process multiple images in parallel
5. **Caching**: Cache extracted times to avoid reprocessing

### Integration Opportunities
1. **Email Templates**: Standardize invitation formats
2. **API Integration**: Direct access to event management systems
3. **User Feedback**: Allow manual corrections with learning

## Migration from Tesseract

This implementation has been migrated from Tesseract OCR to Google Cloud Vision API for:
- **Better Hebrew text recognition**
- **Improved accuracy and reliability**
- **No local dependencies or installation required**
- **Cloud-native scalability**
- **Better handling of various image formats and qualities** 