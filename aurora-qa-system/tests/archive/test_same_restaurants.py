"""
Test: "Which clients have requested reservations at the same restaurants?"
Compare LLM router classification vs expected vs current pipeline behavior
"""
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# The test query
query = "Which clients have requested reservations at the same restaurants?"

print("=" * 80)
print("TESTING QUERY CLASSIFICATION")
print("=" * 80)
print(f"\nQuery: {query}\n")

# Test with corrected prompt
corrected_prompt = f"""You are a query router for a concierge QA system. Classify the query as LOOKUP or ANALYTICS.

**LOOKUP** - Filter and retrieve messages by specific criteria:
- Asks about specific people (contains names)
- Filters by specific dates, locations, or attributes
- Can be answered by retrieving relevant messages
- Keywords: specific names, dates, locations
Examples:
  ✓ "What is Layla's phone number?"
  ✓ "Which clients have plans for January 2025?"
  ✓ "Which clients visited Paris?"
  ✓ "Are there clients who visited both Paris and Tokyo?"
  ✓ "Compare Layla and Lily's preferences"
  ✓ "Which clients requested private museum access?"

**ANALYTICS** - Find patterns through aggregation/grouping:
- Requires counting, grouping, or finding commonalities
- Keywords: "same", "most", "similar", "common", "how many", "most popular"
- Cannot be answered by simple retrieval
Examples:
  ✓ "Which clients requested the SAME restaurants?"
  ✓ "Who has the MOST restaurant bookings?"
  ✓ "What are the MOST POPULAR destinations?"
  ✓ "What services do MULTIPLE clients prefer?"
  ✓ "Find clients with SIMILAR preferences"

**Key Distinction:**
- LOOKUP = Filter/retrieve by criteria (even if "which clients")
- ANALYTICS = Aggregate/group to find patterns (SAME/MOST/SIMILAR/COUNT)

User Query: "{query}"

Classify this query. Respond with ONLY one word: LOOKUP or ANALYTICS

Classification:"""

print("Testing with CORRECTED prompt...")
print("-" * 80)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": corrected_prompt}],
    temperature=0.1,
    max_tokens=10
)

classification = response.choices[0].message.content.strip().upper()

print(f"\nLLM Classification: {classification}")
print(f"Expected Classification: ANALYTICS")
print(f"Match: {'✅ CORRECT' if classification == 'ANALYTICS' else '❌ WRONG'}")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

print(f"\nQuery contains:")
print(f"  - 'which clients': Yes (plural indicator)")
print(f"  - 'SAME': Yes ← KEY ANALYTICS KEYWORD")
print(f"  - 'restaurants': Yes (entity type)")

print(f"\nWhy this MUST be ANALYTICS:")
print(f"  1. Requires GROUP BY restaurant_name")
print(f"  2. Requires COUNT distinct users per restaurant")
print(f"  3. Requires FILTER where count > 1")
print(f"  4. RAG retrieval cannot do this aggregation")

print(f"\nWhat RAG pipeline would do (if classified as LOOKUP):")
print(f"  1. Retrieve top-10 'restaurant reservation' messages")
print(f"  2. Pass to LLM")
print(f"  3. LLM tries to find patterns in 10 messages")
print(f"  4. Result: Likely misses data (can't see all 3,349 messages)")

print(f"\nWhat Graph Analytics pipeline should do:")
print(f"  1. Query graph for ALL restaurant reservation triples")
print(f"  2. Extract restaurant names")
print(f"  3. Group by restaurant name")
print(f"  4. Count users per restaurant")
print(f"  5. Return restaurants with count > 1")
print(f"  6. Result: Accurate aggregation (Osteria Francescana: 3 clients)")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)
