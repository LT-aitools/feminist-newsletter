const CONFIG = {
  calendarName: 'מייל פמיניסטי שבועי',
  timeZone: 'Asia/Jerusalem',
  newsletterSender: 'sharon.orsh@56456773.mailchimpapp.com',
  processedLabelName: 'WomensRightsProcessed',
  defaultDuration: 120,
  defaultStartTime: '19:00',
  maxEmailsToProcess: 10,
  skipPastEvents: true
};

function normalizePlainText(content) {
  let clean = content.split('This email was sent to')[0].split('Want to change how you receive')[0];
  
  // Remove Facebook/Website/Email footer links - multiple patterns
  clean = clean.split('Facebook (https://')[0];
  clean = clean.split('** Website (https://')[0];
  clean = clean.split('** Email (mailto:')[0];
  clean = clean.split('Facebook (http://')[0];
  clean = clean.split('Website (https://')[0];
  clean = clean.split('Email (mailto:')[0];
  
  // Remove the specific footer pattern that's appearing
  clean = clean.replace(/Facebook \(https:\/\/wordpress\.us13\.list-manage\.com[^\)]*\).*$/i, '');
  clean = clean.replace(/\*\* Website \(https:\/\/wordpress\.us13\.list-manage\.com[^\)]*\).*$/i, '');
  clean = clean.replace(/\*\* Email \(mailto:[^\)]*\).*$/i, '');
  
  // More aggressive footer removal
  clean = clean.replace(/Facebook \([^)]+\)\s*\*\*.*$/i, '');
  clean = clean.replace(/\*\*\s*Website \([^)]+\).*$/i, '');
  clean = clean.replace(/\*\*\s*Email \([^)]+\).*$/i, '');
  
  // Remove other common footer patterns
  clean = clean.split('Copyright ©')[0];
  clean = clean.split('Our mailing address is:')[0];
  clean = clean.split('unsubscribe from this list')[0];
  clean = clean.split('=============================================================')[0];
  
  // Clean up any orphaned content at the beginning or end that results from splitting
  // Remove any content that starts with just punctuation and a link
  clean = clean.replace(/^\s*[\.\,\;\:]\s*\(https:\/\/[^)]*\)\s*/g, '');
  
  // Clean up any remaining orphaned punctuation at the start
  clean = clean.replace(/^\s*[\.\,\;\:\)]\s*/g, '');
  
  // Remove any remaining ** markers or separator fragments at the end
  clean = clean.replace(/\s*\*+\s*$/g, '');
  clean = clean.replace(/\s*=+\s*$/g, '');
  
  clean = clean.replace(/Facebook\[\^\$\]\*\$/i, '').trim();
  clean = clean.replace(/\r?\n|\r/g, ' ').replace(/\s+/g, ' ').trim();
  return clean;
}

function extractEventBlocksFromNewsletter(content) {
  return content.split(/(?=ביום)/g).map(l => l.trim()).filter(l => l.length > 15 && /\d{1,2}\/\d{1,2}/.test(l));
}

function parseEventBlock(block) {
  const event = {
    title: extractTitle(block),
    date: extractDate(block),
    time: CONFIG.defaultStartTime,
    duration: CONFIG.defaultDuration,
    location: extractLocation(block),
    organizer: extractOrganizer(block),
    description: block,
    isVirtual: /וירטואלי|זום|zoom|online/i.test(block),
    type: extractEventType(block)
  };

  if (!event.date) throw new Error('No valid date found');

  if (!/\d{1,2}:\d{2}/.test(block)) {
    event.title += ' (זמן מדויק של האירוע בזימון)';
  }

  return event;
}

function extractDate(block) {
  const match = block.match(/ה(\d{1,2})\/(\d{1,2})/);
  if (match) {
    const day = parseInt(match[1]);
    const month = parseInt(match[2]);
    let year = new Date().getFullYear();
    
    const eventDate = new Date(year, month - 1, day);
    const today = new Date();
    
    // If the event date is more than 30 days in the past, assume it's next year
    // But if it's within 30 days, keep it in the current year
    const daysDiff = (today - eventDate) / (1000 * 60 * 60 * 24);
    if (daysDiff > 30) {
      year++;
    }
    
    return new Date(year, month - 1, day);
  }
  return null;
}

function extractTitle(block) {
  // Try multiple patterns to extract the title
  let match = block.match(/בנושא "([^"]+)"/);
  if (match) return match[1].trim();
  
  match = block.match(/בנושא \'([^\']+)\'/);
  if (match) return match[1].trim();
  
  match = block.match(/בנושא ([^.]+)\./);
  if (match) return match[1].trim();
  
  // Try to extract from quotes in general
  match = block.match(/"([^"]+)"/);
  if (match) return match[1].trim();
  
  // Try to extract event description after מפגש/הרצאה/דיון
  match = block.match(/(מפגש|הרצאה|דיון)\s+([^.]+)/);
  if (match) return match[2].trim();
  
  return 'אירוע זכויות נשים';
}

function extractLocation(block) {
  if (/וירטואלי|זום|zoom|online/i.test(block)) return 'וירטואלי';
  if (/בכנסת|הכנסת/i.test(block)) return 'ירושלים';
  
  const cities = ['תל אביב', 'ירושלים', 'חיפה', 'באר שבע'];
  for (const city of cities) if (block.includes(city)) return city;
  
  return '';
}

function extractOrganizer(block) {
  return block.includes('הוועדה לקידום מעמד האישה') ? 'הוועדה לקידום מעמד האישה' : '';
}

function extractEventType(block) {
  if (block.includes('דיון')) return 'discussion';
  if (block.includes('הרצאה')) return 'lecture';
  if (block.includes('מפגש')) return 'meeting';
  return '';
}

function createEventDescription(event) {
  return `${event.description}\n\n---\nנוצר אוטומטית מהניוזלטר הפמיניסטי השבועי`;
}

function checkForDuplicateEvent(calendar, title, date) {
  // Check for existing events on the same day with similar titles
  const startOfDay = new Date(date);
  startOfDay.setHours(0, 0, 0, 0);
  
  const endOfDay = new Date(date);
  endOfDay.setHours(23, 59, 59, 999);
  
  const existingEvents = calendar.getEvents(startOfDay, endOfDay);
  
  for (const event of existingEvents) {
    const existingTitle = event.getTitle().toLowerCase();
    const newTitle = title.toLowerCase();
    
    // Check for exact match or very similar titles
    if (existingTitle === newTitle || 
        existingTitle.includes(newTitle.substring(0, 20)) ||
        newTitle.includes(existingTitle.substring(0, 20))) {
      return event;
    }
  }
  
  return null;
}

function debugCalendarAccess() {
  Logger.log('=== DEBUGGING CALENDAR ACCESS ===');
  
  try {
    // Check if calendar exists
    const calendars = CalendarApp.getCalendarsByName(CONFIG.calendarName);
    Logger.log(`Found ${calendars.length} calendars with name: ${CONFIG.calendarName}`);
    
    if (calendars.length === 0) {
      Logger.log('❌ Calendar not found! Creating new calendar...');
      const newCalendar = CalendarApp.createCalendar(CONFIG.calendarName);
      Logger.log(`✅ Created new calendar: ${newCalendar.getName()}`);
      return newCalendar;
    }
    
    const calendar = calendars[0];
    Logger.log(`✅ Using calendar: ${calendar.getName()}`);
    Logger.log(`Calendar ID: ${calendar.getId()}`);
    
    // Test creating a simple event
    const testDate = new Date();
    testDate.setDate(testDate.getDate() + 1);
    testDate.setHours(19, 0, 0, 0);
    
    const endDate = new Date(testDate.getTime() + 2 * 60 * 60 * 1000); // 2 hours later
    
    const testEvent = calendar.createEvent(
      'Test Event - Debug',
      testDate,
      endDate,
      {
        description: 'This is a test event to verify calendar access',
        location: 'Test Location'
      }
    );
    
    Logger.log(`✅ Test event created: ${testEvent.getTitle()}`);
    Logger.log(`Event ID: ${testEvent.getId()}`);
    
    return calendar;
    
  } catch (error) {
    Logger.log(`❌ Calendar access error: ${error.message}`);
    Logger.log(`Error stack: ${error.stack}`);
    throw error;
  }
}

function debugEmailAccess() {
  Logger.log('=== DEBUGGING EMAIL ACCESS ===');
  
  try {
    const threads = GmailApp.search(`from:${CONFIG.newsletterSender}`, 0, 2);
    Logger.log(`Found ${threads.length} email threads from ${CONFIG.newsletterSender}`);
    
    if (threads.length === 0) {
      Logger.log('❌ No emails found! Check sender address.');
      return [];
    }
    
    threads.forEach((thread, index) => {
      const messages = thread.getMessages();
      const email = messages[messages.length - 1];
      
      Logger.log(`--- Email ${index + 1} ---`);
      Logger.log(`Subject: ${email.getSubject()}`);
      Logger.log(`Date: ${email.getDate()}`);
      Logger.log(`From: ${email.getFrom()}`);
      
      const plainText = email.getPlainBody();
      Logger.log(`Plain text length: ${plainText.length}`);
      Logger.log(`First 200 chars: ${plainText.substring(0, 200)}`);
    });
    
    return threads;
    
  } catch (error) {
    Logger.log(`❌ Email access error: ${error.message}`);
    throw error;
  }
}

function testWithRealEmail() {
  Logger.log('=== TESTING WITH REAL EMAIL ===');
  
  const threads = GmailApp.search(`from:${CONFIG.newsletterSender}`, 0, 1);
  if (threads.length === 0) {
    Logger.log('No emails found');
    return;
  }
  
  const email = threads[0].getMessages()[0];
  const plainText = normalizePlainText(email.getPlainBody());
  
  Logger.log(`Email content length: ${plainText.length}`);
  Logger.log(`First 500 chars: ${plainText.substring(0, 500)}`);
  
  const blocks = extractEventBlocksFromNewsletter(plainText);
  Logger.log(`Found ${blocks.length} event blocks`);
  
  blocks.forEach((block, index) => {
    Logger.log(`\n--- Block ${index + 1} ---`);
    Logger.log(`Content: ${block.substring(0, 200)}...`);
    
    try {
      const event = parseEventBlock(block);
      Logger.log(`✅ Parsed: ${event.title} on ${event.date}`);
    } catch (error) {
      Logger.log(`❌ Failed: ${error.message}`);
    }
  });
}

function processTwoEmailsPlainText() {
  Logger.log('=== PROCESSING 2 EMAILS WITH FIXED LINKS ===');
  
  let calendar;
  try {
    calendar = debugCalendarAccess();
  } catch (error) {
    Logger.log(`❌ Failed to access calendar: ${error.message}`);
    return;
  }
  
  let threads;
  try {
    threads = debugEmailAccess();
    if (threads.length === 0) return;
  } catch (error) {
    Logger.log(`❌ Failed to access emails: ${error.message}`);
    return;
  }

  let eventsCreated = 0;
  let eventsFailed = 0;

  for (const thread of threads) {
    Logger.log(`\\n--- Processing thread: ${thread.getFirstMessageSubject()} ---`);
    
    const messages = thread.getMessages();
    const email = messages[messages.length - 1];
    const plainText = normalizePlainText(email.getPlainBody());
    const htmlBody = email.getBody();

    const htmlLinks = [];
    const regex = /href=['\"]([^'\"]+)['\"][^>]*>([^<]+)</g;
    let match;

    while ((match = regex.exec(htmlBody)) !== null) {
      const url = match[1];
      const label = match[2].trim();
      if (label.includes('בהזמנה') || label.includes('בלינק')) {
        htmlLinks.push({ label, url });
      }
    }

    Logger.log(`Found ${htmlLinks.length} valid links (בהזמנה/בלינק)`);

    const lines = extractEventBlocksFromNewsletter(plainText);
    Logger.log(`Found ${lines.length} event blocks`);

    for (let i = 0; i < lines.length; i++) {
      const block = lines[i];
      Logger.log(`\\n--- Processing event block ${i + 1} ---`);
      Logger.log(`Block content: ${block.substring(0, 100)}...`);

      const matchingLinks = htmlLinks.filter(link => {
        return block.includes(link.label);
      }).map(link => `🔗 ${link.label}: ${link.url}`);

      const blockWithLinks = block + (matchingLinks.length ? `\\n\\nקישורים רלוונטיים:\\n${matchingLinks.join('\\n')}` : '');

      try {
        const event = parseEventBlock(blockWithLinks);
        Logger.log(`Parsed event: ${event.title}`);
        Logger.log(`Event date: ${event.date}`);

        const existingEvent = checkForDuplicateEvent(calendar, event.title, event.date);
        if (existingEvent) {
          Logger.log(`⚠️ Duplicate found: ${existingEvent.getTitle()} - SKIPPING`);
          eventsFailed++;
        } else {
          const startTime = new Date(event.date);
          startTime.setHours(19, 0, 0, 0);
          const endTime = new Date(startTime.getTime() + event.duration * 60000);

          const createdEvent = calendar.createEvent(event.title, startTime, endTime, {
            description: createEventDescription(event),
            location: event.location,
            guests: '',
          });

          Logger.log(`✅ Created event: ${createdEvent.getTitle()}`);
          eventsCreated++;
        }

      } catch (err) {
        Logger.log(`❌ Failed to create event: ${err.message}`);
        eventsFailed++;
      }
    }
  }

  Logger.log(`\\n=== SUMMARY ===`);
  Logger.log(`✅ Events created: ${eventsCreated}`);
  Logger.log(`❌ Events failed: ${eventsFailed}`);
  Logger.log('✅ PRODUCTION COMPLETE - ONLY בהזמנה / בלינק LINKS INCLUDED');
}

function listAllCalendars() {
  Logger.log('=== ALL CALENDARS ===');
  const calendars = CalendarApp.getAllCalendars();
  calendars.forEach((cal, index) => {
    Logger.log(`${index + 1}. ${cal.getName()} (ID: ${cal.getId()})`);
  });
}

function searchTestEmails() {
  Logger.log('=== SEARCHING TEST EMAILS ===');
  const threads = GmailApp.search('subject:פמיניסטי OR subject:נשים', 0, 10);
  Logger.log(`Found ${threads.length} threads with Hebrew keywords`);
  
  threads.forEach((thread, index) => {
    const subject = thread.getFirstMessageSubject();
    const sender = thread.getMessages()[0].getFrom();
    Logger.log(`${index + 1}. ${subject} (from: ${sender})`);
  });
}

function viewAllEvents() {
  Logger.log('=== VIEWING ALL EVENTS (PAST AND FUTURE) ===');
  const calendar = CalendarApp.getCalendarsByName(CONFIG.calendarName)[0];
  if (!calendar) {
    Logger.log('Calendar not found');
    return;
  }
  
  // Get events from far in the past to far in the future
  const farPast = new Date();
  farPast.setFullYear(farPast.getFullYear() - 1); // 1 year ago
  
  const farFuture = new Date();
  farFuture.setFullYear(farFuture.getFullYear() + 1); // 1 year in the future
  
  const events = calendar.getEvents(farPast, farFuture);
  
  Logger.log(`Found ${events.length} total events:`);
  events.forEach((event, index) => {
    const isPast = event.getStartTime() < new Date();
    const timeLabel = isPast ? '(PAST)' : '(FUTURE)';
    
    Logger.log(`${index + 1}. ${event.getTitle()} ${timeLabel}`);
    Logger.log(`   Date: ${event.getStartTime()}`);
    Logger.log(`   Location: ${event.getLocation()}`);
    Logger.log(`   Description length: ${event.getDescription().length} chars`);
    Logger.log('');
  });
}

function viewExistingEvents() {
  Logger.log('=== VIEWING EXISTING EVENTS ===');
  const calendar = CalendarApp.getCalendarsByName(CONFIG.calendarName)[0];
  if (!calendar) {
    Logger.log('Calendar not found');
    return;
  }
  
  const now = new Date();
  const future = new Date(now.getTime() + 60 * 24 * 60 * 60 * 1000); // 60 days
  const events = calendar.getEvents(now, future);
  
  Logger.log(`Found ${events.length} upcoming events:`);
  events.forEach((event, index) => {
    Logger.log(`${index + 1}. ${event.getTitle()}`);
    Logger.log(`   Date: ${event.getStartTime()}`);
    Logger.log(`   Location: ${event.getLocation()}`);
    Logger.log(`   Description length: ${event.getDescription().length} chars`);
    Logger.log(`   First 100 chars: ${event.getDescription().substring(0, 100)}...`);
    Logger.log('');
  });
}

function cleanupTestEvents() {
  Logger.log('=== CLEANING UP TEST EVENTS ===');
  const calendar = CalendarApp.getCalendarsByName(CONFIG.calendarName)[0];
  if (!calendar) {
    Logger.log('Calendar not found');
    return;
  }
  
  const now = new Date();
  const future = new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000); // 1 year
  const events = calendar.getEvents(now, future);
  
  let deleted = 0;
  events.forEach(event => {
    if (event.getTitle().includes('Test') || 
        event.getTitle().includes('Debug') ||
        event.getTitle().includes('(זמן מדויק של האירוע בזימון)')) {
      Logger.log(`Deleting event: ${event.getTitle()}`);
      event.deleteEvent();
      deleted++;
    }
  });
  
  Logger.log(`✅ Deleted ${deleted} test/duplicate events`);
}

function cleanupAllNewsletterEvents() {
  Logger.log('=== CLEANING UP ALL NEWSLETTER EVENTS (INCLUDING PAST) ===');
  const calendar = CalendarApp.getCalendarsByName(CONFIG.calendarName)[0];
  if (!calendar) {
    Logger.log('Calendar not found');
    return;
  }
  
  // Get events from far in the past to far in the future
  const farPast = new Date();
  farPast.setFullYear(farPast.getFullYear() - 2); // 2 years ago
  
  const farFuture = new Date();
  farFuture.setFullYear(farFuture.getFullYear() + 2); // 2 years in the future
  
  const events = calendar.getEvents(farPast, farFuture);
  
  let deleted = 0;
  events.forEach(event => {
    const description = event.getDescription();
    const title = event.getTitle();
    
    // Delete if it's a newsletter event, test event, or debug event
    if (description.includes('נוצר אוטומטית מהניוזלטר הפמיניסטי השבועי') ||
        title.includes('Test') || 
        title.includes('Debug') ||
        title.includes('(זמן מדויק של האירוע בזימון)')) {
      Logger.log(`Deleting event: ${title} (${event.getStartTime()})`);
      event.deleteEvent();
      deleted++;
    }
  });
  
  Logger.log(`✅ Deleted ${deleted} newsletter events (including past events)`);
}

function testSingleEvent() {
  Logger.log('=== TESTING SINGLE EVENT CREATION ===');
  
  const sampleText = `ביום שני, ה7/7, תקיים הוועדה לקידום מעמד האישה ושוויון מגדרי בכנסת דיון בנושא "מימוש הסיוע לגרושות ולגרושים של משרתי המילואים". פרטים והרשמה בהזמנה.`;
  
  const calendar = CalendarApp.getCalendarsByName(CONFIG.calendarName)[0];
  
  try {
    const event = parseEventBlock(sampleText);
    Logger.log(`✅ Parsed: ${event.title}`);
    Logger.log(`Date: ${event.date}`);
    Logger.log(`Location: ${event.location}`);
    
    const startTime = new Date(event.date);
    startTime.setHours(19, 0, 0, 0);
    const endTime = new Date(startTime.getTime() + event.duration * 60000);
    
    const createdEvent = calendar.createEvent(event.title, startTime, endTime, {
      description: createEventDescription(event),
      location: event.location,
    });
    
    Logger.log(`✅ Created test event: ${createdEvent.getTitle()}`);
    Logger.log(`Event ID: ${createdEvent.getId()}`);
    
  } catch (error) {
    Logger.log(`❌ Failed: ${error.message}`);
  }
}

function testTextCleaning() {
  Logger.log('=== TESTING TEXT CLEANING ===');
  
  const threads = GmailApp.search(`from:${CONFIG.newsletterSender}`, 0, 1);
  if (threads.length === 0) {
    Logger.log('No emails found');
    return;
  }
  
  const email = threads[0].getMessages()[0];
  const originalText = email.getPlainBody();
  const cleanedText = normalizePlainText(originalText);
  
  Logger.log(`Original text length: ${originalText.length}`);
  Logger.log(`Cleaned text length: ${cleanedText.length}`);
  Logger.log('');
  Logger.log('=== ORIGINAL TEXT (first 500 chars) ===');
  Logger.log(originalText.substring(0, 500));
  Logger.log('');
  Logger.log('=== CLEANED TEXT (first 500 chars) ===');
  Logger.log(cleanedText.substring(0, 500));
  Logger.log('');
  Logger.log('=== ORIGINAL TEXT (last 500 chars) ===');
  Logger.log(originalText.substring(originalText.length - 500));
  Logger.log('');
  Logger.log('=== CLEANED TEXT (last 500 chars) ===');
  Logger.log(cleanedText.substring(cleanedText.length - 500));
  Logger.log('');
  
  // Check if problematic text still exists
  const hasFooter = cleanedText.includes('Facebook (https://') || 
                   cleanedText.includes('** Website (https://') || 
                   cleanedText.includes('** Email (mailto:');
  
  Logger.log(`Footer still present: ${hasFooter}`);
}

function runDiagnostics() {
  Logger.log('=== STARTING FULL DIAGNOSTICS ===');
  
  try {
    // Test 1: Calendar Access
    debugCalendarAccess();
    
    // Test 2: Email Access  
    debugEmailAccess();
    
    // Test 3: Event Parsing
    testWithRealEmail();
    
    // Test 4: List all calendars
    listAllCalendars();
    
    // Test 5: Search for Hebrew emails
    searchTestEmails();
    
  } catch (error) {
    Logger.log(`❌ Diagnostics failed: ${error.message}`);
  }
  
  Logger.log('=== DIAGNOSTICS COMPLETE ===');
}