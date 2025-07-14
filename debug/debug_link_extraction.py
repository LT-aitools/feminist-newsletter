"""
Debug script to examine link extraction from newsletter HTML.
"""
import logging
from email_handler import GmailHandler
from newsletter_processor import NewsletterProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_link_extraction():
    """Debug link extraction from newsletter emails."""
    
    print("=== DEBUGGING LINK EXTRACTION ===")
    
    # Initialize handlers
    email_handler = GmailHandler()
    processor = NewsletterProcessor()
    
    # Authenticate
    if not email_handler.authenticate():
        print("Failed to authenticate with Gmail")
        return
    
    # Get latest newsletter emails
    print("Fetching latest unread newsletter emails...")
    emails = email_handler.get_unread_newsletters()
    
    # Also get recent newsletters to find July 9th and 10th events
    print("Fetching recent newsletter emails...")
    recent_emails = email_handler.get_recent_newsletters(days_back=14)
    print(f"Found {len(recent_emails)} recent newsletter emails")
    
    # Combine unread and recent emails, removing duplicates
    all_emails = emails.copy()
    for recent_email in recent_emails:
        if not any(email['id'] == recent_email['id'] for email in all_emails):
            all_emails.append(recent_email)
    
    emails = all_emails
    
    if not emails:
        print("No unread newsletter emails found")
        return
    
    print(f"Found {len(emails)} unread newsletter emails")
    
    for i, email in enumerate(emails):
        print(f"\n--- Email {i+1}: {email['subject']} ---")
        print(f"From: {email['from']}")
        print(f"Date: {email['date']}")
        
        # Get email content
        html_content = email.get('html_content', '')
        plain_text = email.get('plain_text', '')
        
        print(f"HTML content length: {len(html_content)}")
        print(f"Plain text length: {len(plain_text)}")
        
        # Show the full plain text to see what's missing
        print("\n--- FULL PLAIN TEXT ---")
        print(plain_text)
        print("--- END PLAIN TEXT ---")
        
        # Extract links manually to see what's happening
        import re
        
        print("\n--- MANUAL LINK EXTRACTION ---")
        
        # Find all <a> tags
        a_tag_pattern = r'<a[^>]+href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>'
        a_matches = re.findall(a_tag_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        print(f"Found {len(a_matches)} total <a> tags")
        
        # Show all links with their content
        for j, (url, content) in enumerate(a_matches):
            # Remove HTML tags from content
            clean_content = re.sub(r'<[^>]+>', '', content).strip()
            print(f"Link {j+1}:")
            print(f"  URL: {url}")
            print(f"  Content: '{clean_content}'")
            print(f"  Contains 'בהזמנה': {'בהזמנה' in clean_content}")
            print(f"  Contains 'בלינק': {'בלינק' in clean_content}")
            print()
        
        # Show what the processor extracts
        print("--- PROCESSOR LINK EXTRACTION ---")
        processor_links = processor._extract_links_from_html(html_content)
        print(f"Processor extracted {len(processor_links)} links:")
        
        for j, link in enumerate(processor_links):
            print(f"  Link {j+1}:")
            print(f"    URL: {link['url']}")
            print(f"    Label: '{link['label']}'")
            print()
        
        # Extract event blocks
        print("--- EVENT BLOCKS ---")
        from text_parser import extract_event_blocks_from_newsletter
        event_blocks = extract_event_blocks_from_newsletter(plain_text)
        print(f"Found {len(event_blocks)} event blocks:")
        
        for j, block in enumerate(event_blocks):
            print(f"\nEvent Block {j+1}:")
            print(f"Content: {block[:200]}...")
            
            # Check which links should match this block
            matching_links = []
            for link in processor_links:
                if link['label'] in block:
                    matching_links.append(link)
            
            print(f"Should match {len(matching_links)} links:")
            for link in matching_links:
                print(f"  - {link['label']}: {link['url']}")
            
                    # Look for specific July 9th and 10th events
        if '9/7' in block or '10/7' in block:
            print("*** JULY 9TH OR 10TH EVENT DETECTED ***")
            print(f"Full block: {block}")
            print(f"Contains 'בהזמנה': {'בהזמנה' in block}")
            print(f"Contains 'בלינק': {'בלינק' in block}")
            print(f"Contains 'הרשמה': {'הרשמה' in block}")
        
        # Also check for the specific Hebrew text you mentioned
        if 'דובס נגד ג\'קסון' in block or 'נשים חסרות מעמד' in block:
            print("*** JULY 9TH OR 10TH EVENT BY TITLE ***")
            print(f"Full block: {block}")
            print(f"Contains 'בהזמנה': {'בהזמנה' in block}")
            print(f"Contains 'בלינק': {'בלינק' in block}")
            print(f"Contains 'הרשמה': {'הרשמה' in block}")

if __name__ == "__main__":
    debug_link_extraction() 