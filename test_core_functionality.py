"""
Test script for core newsletter processing functionality.
"""
import logging
from datetime import datetime
from text_parser import (
    normalize_plain_text,
    extract_event_blocks_from_newsletter,
    extract_date,
    extract_title,
    extract_location,
    extract_organizer,
    extract_event_type
)
from newsletter_processor import NewsletterProcessor


def setup_logging():
    """Setup logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def test_text_cleaning():
    """Test the text cleaning functionality."""
    print("=== TESTING TEXT CLEANING ===")
    
    # Sample email content with footer patterns
    sample_content = """
    ביום שני, ה7/7, תקיים הוועדה לקידום מעמד האישה ושוויון מגדרי בכנסת דיון בנושא "מימוש הסיוע לגרושות ולגרושים של משרתי המילואים". פרטים והרשמה בהזמנה.
    
    ביום שלישי, ה8/7, יתקיים מפגש בנושא "זכויות נשים בעבודה" בתל אביב.
    
    This email was sent to test@example.com
    Want to change how you receive these emails?
    Facebook (https://wordpress.us13.list-manage.com/track/click?u=123&id=456)
    ** Website (https://wordpress.us13.list-manage.com/track/click?u=123&id=789)
    ** Email (mailto:test@example.com)
    Copyright © 2024
    """
    
    cleaned = normalize_plain_text(sample_content)
    
    print("Original content length:", len(sample_content))
    print("Cleaned content length:", len(cleaned))
    print("\nCleaned content:")
    print(cleaned)
    
    # Check if footer patterns were removed
    footer_patterns = [
        'This email was sent to',
        'Want to change how you receive',
        'Facebook (https://',
        '** Website (https://',
        '** Email (mailto:',
        'Copyright ©'
    ]
    
    for pattern in footer_patterns:
        if pattern in cleaned:
            print(f"❌ Footer pattern still present: {pattern}")
        else:
            print(f"✅ Footer pattern removed: {pattern}")


def test_event_extraction():
    """Test event block extraction."""
    print("\n=== TESTING EVENT EXTRACTION ===")
    
    # Sample newsletter content
    sample_content = """
    ביום שני, ה7/7, תקיים הוועדה לקידום מעמד האישה ושוויון מגדרי בכנסת דיון בנושא "מימוש הסיוע לגרושות ולגרושים של משרתי המילואים". פרטים והרשמה בהזמנה.
    
    ביום שלישי, ה8/7, יתקיים מפגש בנושא "זכויות נשים בעבודה" בתל אביב.
    
    ביום רביעי, ה9/7, הרצאה בנושא "שוויון מגדרי בחברה הישראלית" בחיפה.
    """
    
    blocks = extract_event_blocks_from_newsletter(sample_content)
    
    print(f"Found {len(blocks)} event blocks:")
    for i, block in enumerate(blocks, 1):
        print(f"\nBlock {i}:")
        print(block)


def test_event_parsing():
    """Test individual event parsing functions."""
    print("\n=== TESTING EVENT PARSING ===")
    
    # Sample event block
    sample_block = 'ביום שני, ה7/7, תקיים הוועדה לקידום מעמד האישה ושוויון מגדרי בכנסת דיון בנושא "מימוש הסיוע לגרושות ולגרושים של משרתי המילואים". פרטים והרשמה בהזמנה.'
    
    print("Sample block:", sample_block)
    
    # Test each parsing function
    date = extract_date(sample_block)
    title = extract_title(sample_block)
    location = extract_location(sample_block)
    organizer = extract_organizer(sample_block)
    event_type = extract_event_type(sample_block)
    
    print(f"Date: {date}")
    print(f"Title: {title}")
    print(f"Location: {location}")
    print(f"Organizer: {organizer}")
    print(f"Event Type: {event_type}")


def test_full_processing():
    """Test the full newsletter processing pipeline."""
    print("\n=== TESTING FULL PROCESSING PIPELINE ===")
    
    # Sample email content
    sample_email = """
    ביום שני, ה7/7, תקיים הוועדה לקידום מעמד האישה ושוויון מגדרי בכנסת דיון בנושא "מימוש הסיוע לגרושות ולגרושים של משרתי המילואים". פרטים והרשמה בהזמנה.
    
    ביום שלישי, ה8/7, יתקיים מפגש בנושא "זכויות נשים בעבודה" בתל אביב.
    
    ביום רביעי, ה9/7, הרצאה בנושא "שוויון מגדרי בחברה הישראלית" בחיפה.
    """
    
    # Sample HTML content with links
    sample_html = """
    <html>
    <body>
    <p>ביום שני, ה7/7, תקיים הוועדה לקידום מעמד האישה ושוויון מגדרי בכנסת דיון בנושא "מימוש הסיוע לגרושות ולגרושים של משרתי המילואים". <a href="https://example.com/invitation1">פרטים והרשמה בהזמנה</a>.</p>
    
    <p>ביום שלישי, ה8/7, יתקיים מפגש בנושא "זכויות נשים בעבודה" בתל אביב. <a href="https://example.com/invitation2">פרטים והרשמה בלינק</a>.</p>
    </body>
    </html>
    """
    
    # Process with NewsletterProcessor
    processor = NewsletterProcessor()
    events = processor.process_newsletter_email(sample_email, sample_html)
    
    print(f"Processed {len(events)} events:")
    for i, event in enumerate(events, 1):
        print(f"\nEvent {i}:")
        print(f"  Title: {event.title}")
        print(f"  Date: {event.date}")
        print(f"  Time: {event.time}")
        print(f"  Location: {event.location}")
        print(f"  Organizer: {event.organizer}")
        print(f"  Event Type: {event.event_type}")
        print(f"  Is Virtual: {event.is_virtual}")
        print(f"  Links: {len(event.links)}")
        for link in event.links:
            print(f"    - {link['label']}: {link['url']}")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n=== TESTING EDGE CASES ===")
    
    # Test with no date
    no_date_block = "מפגש בנושא זכויות נשים בתל אביב"
    try:
        date = extract_date(no_date_block)
        print(f"No date block result: {date}")
    except Exception as e:
        print(f"No date block error: {e}")
    
    # Test with invalid date
    invalid_date_block = "ביום שני, ה32/13, מפגש"
    try:
        date = extract_date(invalid_date_block)
        print(f"Invalid date block result: {date}")
    except Exception as e:
        print(f"Invalid date block error: {e}")
    
    # Test with empty content
    empty_content = ""
    blocks = extract_event_blocks_from_newsletter(empty_content)
    print(f"Empty content blocks: {len(blocks)}")
    
    # Test with very short content
    short_content = "ביום שני"
    blocks = extract_event_blocks_from_newsletter(short_content)
    print(f"Short content blocks: {len(blocks)}")


def main():
    """Run all tests."""
    setup_logging()
    
    print("🧪 TESTING CORE NEWSLETTER PROCESSING FUNCTIONALITY")
    print("=" * 60)
    
    try:
        test_text_cleaning()
        test_event_extraction()
        test_event_parsing()
        test_full_processing()
        test_edge_cases()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 