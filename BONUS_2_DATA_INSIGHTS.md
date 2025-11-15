# Bonus 2: Data Insights

## What I Started With

When I first pulled the data from Aurora's API, I got 3,349 messages from 10 members spanning exactly one year (November 8, 2024 to November 8, 2025). Each message had a clean structure: user ID, user name, timestamp, and the message text itself.

**First impression:** This is remarkably clean data - no missing fields, no malformed timestamps, consistent user mappings. Perfect for building and testing a QA system without getting bogged down in data cleaning.

---

## Key Discoveries During Exploration

### 1. Service Mix: Broader Than Expected

Going into this, I assumed "luxury concierge" would be heavily restaurant-focused. The breakdown surprised me:

**What I found:**
- **Restaurant/Dining:** 498 messages (14.9%)
- **Travel/Entertainment:** 708 messages (21.1%)
- **General/Other:** 2,143 messages (64.0%)

**What this taught me:** Members use Aurora for a much wider range of services than just dining. I saw requests for:
- Private jet bookings
- Opera tickets
- Yacht rentals
- Hotel accommodations
- Payment inquiries
- General preferences

**Impact on my system:** I initially tuned my retrieval for restaurant-heavy queries. Discovering this diversity made me adjust the BM25 weighting to not over-optimize for food keywords. The hybrid approach (semantic + keyword + graph) handles this variety better than a restaurant-specific system would.

**What would enhance it:** If messages were pre-tagged by service category (dining, travel, entertainment, billing), I could route queries more intelligently and provide category-specific analytics.

---

### 2. Message Composition: Mostly Requests

Analyzing message structure revealed clear patterns:

**Breakdown:**
- **Direct questions:** 1,098 messages (32.8%) - "Can you...?" "Could you...?"
- **Action requests:** 1,594 messages (47.6%) - "Please book..." "Arrange..."
- **Statements/Preferences:** Remaining messages

**What I learned:** Users interact with Aurora primarily through requests, not conversational messages. This is different from general chatbot datasets where you see more back-and-forth dialogue.

**Examples I found:**
- "Please book a private jet to Paris for this Friday."
- "I need two tickets to the opera in Milan this Saturday."
- "Reserve two seats at the chef's table, 8:00 PM, Chez Panisse."

**Impact on my system:** This request-oriented structure is ideal for LOOKUP queries (extracting information about past requests). The challenge came with ANALYTICS queries, where I needed to count or aggregate across these action items.

---

### 3. Temporal Patterns: Uniform Distribution

The one-year dataset showed interesting temporal characteristics:

**What I observed:**
- **Average:** 9.2 messages per day
- **Range:** Consistent daily activity, no major spikes
- **Coverage:** Messages spread across all 365 days
- **Date mentions:** Only 626 messages (18.7%) explicitly mention dates/times in the text

**Examples of explicit dates:**
- "Book a villa in Santorini for the first week of December."
- "I need tickets for this Friday."
- "Reserve a table for November 15."

**The gap I noticed:** Message timestamps show when the request was sent, but most messages don't specify when the event should occur. For example:
- Message sent: March 1, 2025
- Message: "Book a table at Le Bernardin"
- Event date: Unknown

**What this taught me:** I had to build a temporal analyzer that could:
1. Extract explicit dates from text when available
2. Handle relative dates ("this Friday" → compute actual date)
3. Fall back to message timestamp when event timing is unclear

**What would enhance it:** An additional `event_date` field would eliminate ambiguity. For instance:
```json
{
  "timestamp": "2025-03-01T10:00:00Z",  // When user asked
  "event_date": "2025-03-15",           // When the reservation is for
  "message": "Book a table at Le Bernardin"
}
```

This would make temporal queries like "Where did I eat in March?" much more precise.

---

### 4. User Activity: Fairly Balanced

Looking at member engagement across the 10 users:

**Distribution range:**
- Most active user: 379 messages (11.3%)
- Least active user: ~280 messages (8.4%)
- **Spread:** About 1.3x difference

**What this means:** No extreme power users or ghost users. Everyone in the dataset is reasonably active, which makes user-specific queries viable for all members.

**Impact on my system:** When someone asks "What are Layla's dining preferences?", I have 379 messages to analyze - enough to find patterns. For less active users, I still have 280+ messages, which is sufficient for preference extraction.

**What I extracted during preprocessing:**
- User → Restaurant visits (for the knowledge graph)
- Cuisine preferences by user
- Activity patterns by user

**What would enhance it:** User profile metadata would be powerful:
- Location/timezone (to interpret "this Friday" correctly)
- Dietary restrictions (to filter irrelevant restaurants)
- VIP tier (to prioritize high-touch service responses)

---

### 5. Message Length: Concise and Actionable

Analyzing message characteristics:

**Stats:**
- **Average length:** 68 characters
- **Range:** 9 to 105 characters
- **Distribution:** Most messages are 1-2 sentences

**What I found interesting:** Users keep requests brief and clear. No long conversational messages or complex multi-part requests.

**Examples:**
- Shortest: "I want to" (9 chars) - appears incomplete
- Typical: "Can you confirm my dinner reservation at The French Laundry for four people tonight?" (87 chars)

**Edge cases discovered:** 3 messages under 20 characters that seem truncated:
- "I want to"
- "Please send"
- "I finally"

**What this taught me:** These short messages might be:
1. Incomplete submissions (user hit send accidentally)
2. Fragments from a larger conversation thread not captured here
3. Test data artifacts

**Impact on my system:** I handle these gracefully - the retriever won't match them to queries, and they don't pollute results since they lack semantic content.

**What would enhance it:** Conversation threading - if messages were grouped into conversations, I could see:
- Message 1: "I want to"
- Message 2: "...book a table at Septime for Saturday"

This would provide context for fragments.

---

### 6. Restaurant Mentions: Rich Extractable Data

When preprocessing, I looked for restaurant names and locations:

**What I extracted:**
- 659 messages (19.7%) mention restaurants, cafes, or dining venues
- Top restaurants mentioned: Le Bernardin, Chez Panisse, The French Laundry, Eleven Madison Park
- Geographic spread: Paris, New York, San Francisco, Milan, Tokyo

**Extraction challenges:**
- Capitalized sequences helped identify names
- Some messages say "a nice Italian restaurant" without naming it
- Varied formats: "Le Bernardin" vs "the restaurant Le Bernardin" vs "Le Bernardin in NYC"

**What I built from this:** The knowledge graph captures:
```
User → VISITED → Restaurant → HAS_CUISINE → Cuisine
```

This enables queries like:
- "What Italian restaurants has Layla visited?"
- "Who else has been to Le Bernardin?"

**What would enhance it:** Structured location data would be powerful:
```json
{
  "message": "Reserve a table at Le Bernardin",
  "extracted_entities": {
    "restaurant": "Le Bernardin",
    "cuisine": "French",
    "location": "New York, NY",
    "michelin_stars": 3
  }
}
```

This would enable location-based queries and quality filtering.

---

### 7. Data Consistency: Remarkably Clean

Throughout preprocessing, I tracked data quality:

**What I checked:**
- Missing fields: 0 messages
- Duplicate messages: 0 exact duplicates
- Malformed timestamps: 0
- User ID conflicts: 0 (each user_id always maps to the same user_name)
- Empty messages: 0

**What this meant for development:** I could focus on building the QA system without defensive coding for:
- Null checks on every field
- Deduplication logic
- Timestamp parsing errors
- User identity resolution

**Trade-off I recognized:** This clean data let me iterate quickly, but a production system would need validation layers for real-world messiness:
- Handling typos in user names
- Dealing with duplicate submissions
- Managing timezone inconsistencies
- Filtering spam or irrelevant messages

---

## Preprocessing Insights

### What I Extracted:

**1. Temporal Metadata:**
- Used datefinder to extract dates from message text
- Normalized to ISO format for Qdrant filtering
- Stored as `normalized_dates` array in vector DB

**2. BM25 Index:**
- Tokenized all messages
- Built keyword search index
- Weighted by TF-IDF for relevance

**3. Knowledge Graph:**
- User nodes (10)
- Restaurant nodes (extracted from messages)
- Cuisine nodes (French, Italian, Japanese, etc.)
- VISITED edges connecting users to restaurants
- HAS_CUISINE edges connecting restaurants to cuisines

**4. Vector Embeddings:**
- Used FastEmbed (BAAI/bge-small-en-v1.5)
- 384-dimension vectors
- Stored in Qdrant with user_id and normalized_dates as metadata

### What Worked Well:

The clean, consistent data made preprocessing smooth. I could pipeline:
1. Fetch from API → 2. Extract dates → 3. Build BM25 → 4. Embed → 5. Index to Qdrant

No failures, no retries, no data cleaning steps needed.

---

## Opportunities: What Would Make This Even More Powerful

If I could enhance the dataset with additional fields, here's what would unlock new capabilities:

### 1. Event Dates (Separate from Message Timestamp)
**Current:** Timestamp shows when the message was sent
**Enhanced:** Add `event_date` field for when the service is requested
**Unlocks:** Precise temporal queries ("Where did I eat on March 15?" vs "When did I request reservations in March?")

### 2. Service Category Tags
**Current:** Must infer category from message text
**Enhanced:** Pre-tag as DINING, TRAVEL, ENTERTAINMENT, BILLING, PREFERENCE
**Unlocks:** Category-specific analytics, better query routing, service-level insights

### 3. Location/Venue Metadata
**Current:** Extract restaurant names from free text (error-prone)
**Enhanced:** Structured location data with coordinates, address, cuisine
**Unlocks:** Geographic queries ("Restaurants near the Louvre"), cuisine filtering, map visualizations

### 4. Conversation Threading
**Current:** Each message is standalone
**Enhanced:** Group messages into conversation threads
**Unlocks:** Context-aware QA ("What about Italian?" knowing we were discussing User X's preferences)

### 5. Sentiment/Satisfaction Signals
**Current:** No feedback on service quality
**Enhanced:** Thumbs up/down, star ratings, sentiment tags
**Unlocks:** Preference learning ("Layla loved Le Bernardin but was disappointed with..."), quality-weighted recommendations

### 6. User Profile Context
**Current:** Just user_id and user_name
**Enhanced:** Timezone, dietary restrictions, VIP tier, preferred contact method
**Unlocks:** Personalized responses, timezone-aware date parsing, filtered recommendations

---

## Summary

The Aurora dataset provided an excellent foundation for building and testing a question-answering system. Its clean structure and consistent formatting allowed me to focus on the core challenge: building intelligent retrieval and reasoning capabilities.

**What stood out:**
- Broader service mix than expected (not just restaurants)
- Request-oriented message structure (perfect for retrieval)
- Uniform temporal distribution (good for testing, different from real user patterns)
- Rich extractable data (restaurants, cuisines, preferences)

**What I learned:**
- The gap between message timestamp and event date required careful temporal handling
- Category diversity meant I couldn't over-optimize for restaurant queries
- Clean data accelerated development but masked production challenges

**What would amplify this:**
Additional structured fields (event dates, categories, locations, user context) would enable more sophisticated analytics and personalization without requiring fragile text extraction.

This dataset struck the right balance: realistic enough to surface genuine challenges, clean enough to let me build without getting stuck on data quality issues.
