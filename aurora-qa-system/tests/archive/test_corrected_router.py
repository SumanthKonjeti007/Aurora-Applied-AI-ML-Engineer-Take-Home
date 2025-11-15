"""
Test Corrected LLM Router - Comprehensive Test
Tests all queries encountered with corrected routing logic
"""
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# THE CORRECTED PROMPT
CORRECTED_ROUTING_PROMPT = """You are a query router for a concierge QA system. Classify each query as LOOKUP or ANALYTICS.

**LOOKUP** - Filter and retrieve messages by specific criteria:
- Asks about specific people (contains names like Layla, Vikram, etc.)
- Filters by specific dates, locations, or attributes
- Can be answered by retrieving and reading relevant messages
- Even if query says "which clients", if it's filtering by ONE specific thing (date/location/attribute), it's LOOKUP
Examples:
  ✓ "What is Layla's phone number?"
  ✓ "Which clients have plans for January 2025?" (filter by specific date)
  ✓ "Which clients visited Paris?" (filter by specific location)
  ✓ "Are there clients who visited both Paris and Tokyo?" (filter by two locations)
  ✓ "Compare Layla and Lily's preferences" (specific named people)
  ✓ "Which clients requested private museum access?" (filter by specific service)
  ✓ "Which clients have billing issues?" (filter by specific issue type)
  ✓ "Vikram's Tokyo plans" (specific person)

**ANALYTICS** - Find patterns through aggregation, grouping, or ranking:
- Requires counting, grouping, finding commonalities, or ranking
- Keywords: "SAME", "MOST", "SIMILAR", "COMMON", "POPULAR", "how many", "count"
- Cannot be answered by simple retrieval - needs to process ALL data and aggregate
Examples:
  ✓ "Which clients requested the SAME restaurants?" (group by restaurant, find overlaps)
  ✓ "Who has the MOST restaurant bookings?" (count per user, rank)
  ✓ "What are the MOST POPULAR destinations?" (count frequency, rank)
  ✓ "What services do MULTIPLE clients prefer?" (count per service)
  ✓ "Find clients with SIMILAR preferences" (compare across all)
  ✓ "Which hotel did EVERYONE book?" (aggregate all bookings)

**Key Distinction:**
- LOOKUP = Filter/retrieve by criteria → "Find all messages matching X"
- ANALYTICS = Aggregate/group/rank → "Find patterns/commonalities across all data"

**Critical Rule:**
- If query contains SAME/MOST/SIMILAR/POPULAR/COUNT → ANALYTICS
- Otherwise, even if "which clients" → LOOKUP

Classify each query below. Respond with ONLY the query number and classification, one per line.

QUERIES:
"""

# All test queries with expected classifications
test_cases = [
    # Original user queries
    ("Which clients have plans for January 2025?", "LOOKUP", "Filter by specific date"),
    ("Which clients have both a preference and a related complaint?", "LOOKUP", "Filter by two attributes"),
    ("Which clients requested private museum access?", "LOOKUP", "Filter by specific service"),
    ("Which clients requested same restaurants?", "ANALYTICS", "SAME = aggregation needed"),
    ("What are the conflicting flight preferences of Layla and Lily?", "LOOKUP", "Specific named people"),
    ("How many cars does Vikram Desai have?", "LOOKUP", "Specific person"),
    ("What is Lorenzo Cavalli's new phone number?", "LOOKUP", "Specific person"),
    ("Which clients have both expressed a preference for something and also complained about a related service charge?", "LOOKUP", "Filter by two conditions"),

    # Challenging edge cases
    ("Show me everyone who visited Paris", "LOOKUP", "Filter by specific location"),
    ("Does anyone prefer aisle seats?", "LOOKUP", "Filter by specific preference"),
    ("What did Layla book in December?", "LOOKUP", "Specific person + date"),
    ("List all spa reservations", "LOOKUP", "Filter by specific service type"),
    ("Compare restaurant preferences across all clients", "ANALYTICS", "Compare ACROSS ALL = aggregation"),
    ("Find clients with billing issues", "LOOKUP", "Filter by specific issue"),
    ("Vikram's Tokyo plans", "LOOKUP", "Specific person + location"),
    ("Who has the most restaurant bookings?", "ANALYTICS", "MOST = ranking/counting"),
    ("Tell me about Sophia's preferences", "LOOKUP", "Specific person"),
    ("Which hotel did everyone book?", "ANALYTICS", "EVERYONE = aggregation"),
    ("Are there clients who visited both Paris and Tokyo?", "LOOKUP", "Filter by two locations"),
    ("What services does Lorenzo prefer?", "LOOKUP", "Specific person"),

    # Additional critical tests
    ("Which clients have requested reservations at the same restaurants?", "ANALYTICS", "SAME = grouping needed"),
    ("What are the most popular destinations?", "ANALYTICS", "MOST POPULAR = ranking"),
    ("Which clients visited the same hotels?", "ANALYTICS", "SAME = grouping"),
    ("Which clients are interested in art?", "LOOKUP", "Filter by interest"),
    ("Who prefers similar dining experiences?", "ANALYTICS", "SIMILAR = comparison"),
    ("Which clients complained about service?", "LOOKUP", "Filter by complaint type"),
]

# Build batch prompt
prompt = CORRECTED_ROUTING_PROMPT
for i, (query, _, _) in enumerate(test_cases, 1):
    prompt += f"{i}. {query}\n"

prompt += "\nCLASSIFICATIONS (format: '1. LOOKUP' or '1. ANALYTICS'):\n"

# Call LLM
print("=" * 90)
print("CORRECTED LLM ROUTER - COMPREHENSIVE TEST")
print("=" * 90)
print(f"\nTesting {len(test_cases)} queries...")
print(f"Model: llama-3.3-70b-versatile\n")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1,
    max_tokens=600
)

classifications_text = response.choices[0].message.content.strip()

# Parse results
print("RESULTS:")
print("=" * 90)
print(f"{'#':<3} {'Expected':<10} {'Got':<10} {'Status':<7} {'Query':<50} {'Reason':<25}")
print("=" * 90)

lines = [line.strip() for line in classifications_text.split('\n') if line.strip() and '. ' in line]
results = {}

for line in lines:
    try:
        num_str, classification = line.split('. ', 1)
        num = int(num_str)
        classification = classification.strip().upper()

        if 'LOOKUP' in classification:
            classification = 'LOOKUP'
        elif 'ANALYTICS' in classification:
            classification = 'ANALYTICS'

        results[num] = classification
    except (ValueError, IndexError):
        pass

# Analyze results
correct = 0
incorrect = 0
critical_failures = []

for i, (query, expected, reason) in enumerate(test_cases, 1):
    got = results.get(i, "MISSING")
    is_correct = (got == expected)
    status = "✅" if is_correct else "❌"

    if is_correct:
        correct += 1
    else:
        incorrect += 1
        # Check if this is a critical failure
        if "same" in query.lower() or "most" in query.lower() or "popular" in query.lower():
            critical_failures.append((i, query, expected, got, reason))

    # Truncate query for display
    query_short = query[:47] + "..." if len(query) > 50 else query
    reason_short = reason[:22] + "..." if len(reason) > 25 else reason

    print(f"{i:<3} {expected:<10} {got:<10} {status:<7} {query_short:<50} {reason_short:<25}")

# Summary
print("=" * 90)
print(f"\nACCURACY: {correct}/{len(test_cases)} ({100*correct/len(test_cases):.1f}%)")
print(f"Correct: {correct}")
print(f"Incorrect: {incorrect}")

# Critical failures analysis
if critical_failures:
    print("\n" + "=" * 90)
    print("🚨 CRITICAL FAILURES (SAME/MOST/POPULAR queries)")
    print("=" * 90)
    for num, query, expected, got, reason in critical_failures:
        print(f"\n❌ Query #{num}: {query}")
        print(f"   Expected: {expected}")
        print(f"   Got:      {got}")
        print(f"   Why critical: {reason}")
        print(f"   Impact: This query CANNOT be answered by RAG - routing failure is catastrophic")
else:
    print("\n✅ NO CRITICAL FAILURES - All SAME/MOST/POPULAR queries correctly routed to ANALYTICS")

# Show the corrected prompt for reference
print("\n" + "=" * 90)
print("CORRECTED ROUTING PROMPT (for reference):")
print("=" * 90)
print(CORRECTED_ROUTING_PROMPT[:500] + "...")

print("\n" + "=" * 90)
print("✅ TEST COMPLETE")
print("=" * 90)
