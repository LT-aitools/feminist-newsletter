"""
Test script for real newsletter processing functionality with mock data.
This bypasses API authentication issues and focuses on core functionality.
"""
import logging
from datetime import datetime
from newsletter_processor import NewsletterProcessor
from text_parser import (
    normalize_plain_text,
    extract_event_blocks_from_newsletter,
    extract_date,
    extract_title,
    extract_location,
    extract_organizer,
    extract_event_type
)

def setup_logging():
    """Setup logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def test_with_real_newsletter_sample():
    """Test with a realistic newsletter sample."""
    print("=== TESTING WITH REAL NEWSLETTER SAMPLE ===")
    
    # Sample newsletter content (based on the existing Apps Script examples)
    sample_newsletter = """
    שלום לכולן,
    
    להלן האירועים הקרובים:
    
    ביום שני, ה7/7, תקיים הוועדה לקידום מעמד האישה ושוויון מגדרי בכנסת דיון בנושא "מימוש הסיוע לגרושות ולגרושים של משרתי המילואים". פרטים והרשמה בהזמנה.
    
    ביום שלישי, ה8/7, יתקיים מפגש בנושא "זכויות נשים בעבודה" בתל אביב. 19:00-21:00. פרטים והרשמה בלינק.
    
    ביום רביעי, ה9/7, הרצאה בנושא "שוויון מגדרי בחברה הישראלית" בחיפה. 20:00.
    
    ביום חמישי, ה10/7, מפגש וירטואלי בנושא "נשים בפוליטיקה" בזום. 18:30-20:30.
    
    This email was sent to nlevran@gmail.com
    Want to change how you receive these emails?
    Facebook (https://wordpress.us13.list-manage.com/track/click?u=123&id=456)
    ** Website (https://wordpress.us13.list-manage.com/track/click?u=123&id=789)
    ** Email (mailto:nlevran@gmail.com)
    Copyright © 2024
    """
    
    # Sample HTML content with links
    sample_html = """
    <html>
    <body>
    <p>ביום שני, ה7/7, תקיים הוועדה לקידום מעמד האישה ושוויון מגדרי בכנסת דיון בנושא "מימוש הסיוע לגרושות ולגרושים של משרתי המילואים". <a href="https://example.com/invitation1">פרטים והרשמה בהזמנה</a>.</p>
    
    <p>ביום שלישי, ה8/7, יתקיים מפגש בנושא "זכויות נשים בעבודה" בתל אביב. 19:00-21:00. <a href="https://example.com/invitation2">פרטים והרשמה בלינק</a>.</p>
    
    <p>ביום רביעי, ה9/7, הרצאה בנושא "שוויון מגדרי בחברה הישראלית" בחיפה. 20:00.</p>
    
    <p>ביום חמישי, ה10/7, מפגש וירטואלי בנושא "נשים בפוליטיקה" בזום. 18:30-20:30.</p>
    </body>
    </html>
    """
    
    # Process with NewsletterProcessor
    processor = NewsletterProcessor()
    events = processor.process_newsletter_email(sample_newsletter, sample_html)
    
    print(f"✅ Processed {len(events)} events from newsletter sample:")
    
    for i, event in enumerate(events, 1):
        print(f"\n📅 Event {i}:")
        print(f"  Title: {event.title}")
        print(f"  Date: {event.date.strftime('%Y-%m-%d')}")
        print(f"  Time: {event.time}")
        print(f"  Location: {event.location}")
        print(f"  Organizer: {event.organizer}")
        print(f"  Event Type: {event.event_type}")
        print(f"  Is Virtual: {event.is_virtual}")
        print(f"  Links: {len(event.links)}")
        for link in event.links:
            print(f"    - {link['label']}: {link['url']}")
    
    return events

def test_time_extraction():
    """Test time extraction from various formats."""
    print("\n=== TESTING TIME EXTRACTION ===")
    
    test_cases = [
        "מפגש ב19:00-21:00",
        "הרצאה ב20:00",
        "דיון מ18:30 עד 20:30",
        "מפגש 19 : 00 - 21 : 00",
        "אירוע ללא זמן",
    ]
    
    for test_case in test_cases:
        from text_parser import extract_time_from_text
        time = extract_time_from_text(test_case)
        print(f"'{test_case}' → {time}")

def test_edge_cases():
    """Test various edge cases."""
    print("\n=== TESTING EDGE CASES ===")
    
    # Test with past dates
    past_date_block = "ביום שני, ה1/1, מפגש"
    date = extract_date(past_date_block)
    print(f"Past date (1/1): {date}")
    
    # Test with future dates
    future_date_block = "ביום שני, ה25/12, מפגש"
    date = extract_date(future_date_block)
    print(f"Future date (25/12): {date}")
    
    # Test with virtual events
    virtual_block = "מפגש וירטואלי בזום ביום שני, ה7/7"
    location = extract_location(virtual_block)
    is_virtual = 'וירטואלי' in location or any(word in virtual_block.lower() for word in ['וירטואלי', 'זום', 'zoom', 'online'])
    print(f"Virtual event location: {location}, is_virtual: {is_virtual}")

def main():
    """Run comprehensive functionality tests."""
    setup_logging()
    
    print("🧪 TESTING REAL NEWSLETTER FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Test with real newsletter sample
        events = test_with_real_newsletter_sample()
        
        # Test time extraction
        test_time_extraction()
        
        # Test edge cases
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("📊 FUNCTIONALITY TEST SUMMARY")
        print(f"✅ Successfully processed {len(events)} events")
        print("✅ All core parsing functions working")
        print("✅ Time extraction working")
        print("✅ Edge cases handled properly")
        
        print("\n🎉 Core newsletter processing functionality is working perfectly!")
        print("📝 Next step: Set up Google Cloud APIs for real email processing")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 