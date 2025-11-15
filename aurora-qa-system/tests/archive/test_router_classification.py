"""
Test LLM Router Classification - Batch Mode
Tests routing accuracy between LOOKUP and ANALYTICS queries
"""
import os
from groq import Groq

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Test queries
test_queries = [
    # User-provided queries
    "Which clients have plans for January 2025?",
    "Which clients have both a preference and a related complaint?",
    "Which clients requested private museum access?",
    "Which clients requested same restaurants?",
    "What are the conflicting flight preferences of Layla and Lily?",
    "How many cars does Vikram Desai have?",
    "What is Lorenzo Cavalli's new phone number?",
    "Which clients have both expressed a preference for something and also complained about a related service charge?",

    # Challenging edge cases
    "Show me everyone who visited Paris",
    "Does anyone prefer aisle seats?",
    "What did Layla book in December?",
    "List all spa reservations",
    "Compare restaurant preferences across all clients",
    "Find clients with billing issues",
    "Vikram's Tokyo plans",
    "Who has the most restaurant bookings?",
    "Tell me about Sophia's preferences",
    "Which hotel did everyone book?",
    "Are there clients who visited both Paris and Tokyo?",
    "What services does Lorenzo prefer?",
]

# Batch classification prompt
prompt = f"""You are a query router for a concierge QA system. Classify each query as LOOKUP or ANALYTICS.

**LOOKUP** - Retrieve specific information about named entities:
- Asks about specific people (contains names)
- Requests facts about individuals
- Compares specific named people
Examples: "What is Layla's phone number?", "Compare Layla and Lily's preferences", "Vikram's plans"

**ANALYTICS** - Find patterns, aggregations, or commonalities across entities:
- "Which/What/Who" + plural or "everyone/anyone/all"
- Asks about groups or patterns
- Finds commonalities or aggregations
Examples: "Which clients visited Paris?", "Who has similar preferences?", "List all bookings"

**Key Distinction:**
- LOOKUP = About specific named person(s)
- ANALYTICS = About groups/patterns/everyone

Classify each query below. Respond with ONLY the query number and classification (LOOKUP or ANALYTICS), one per line.

QUERIES:
"""

for i, query in enumerate(test_queries, 1):
    prompt += f"{i}. {query}\n"

prompt += "\nCLASSIFICATIONS (format: '1. LOOKUP' or '1. ANALYTICS'):\n"

# Call LLM once for all queries
print("=" * 80)
print("LLM ROUTER CLASSIFICATION TEST")
print("=" * 80)
print(f"\nTesting {len(test_queries)} queries in batch mode...")
print(f"Model: llama-3.3-70b-versatile\n")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1,
    max_tokens=500
)

classifications = response.choices[0].message.content.strip()

# Parse results
print("RESULTS:")
print("=" * 80)
print(f"{'#':<4} {'Classification':<12} {'Query':<60}")
print("=" * 80)

# Expected classifications (for validation)
expected = {
    1: "ANALYTICS",  # Which clients have plans
    2: "ANALYTICS",  # Which clients have both
    3: "ANALYTICS",  # Which clients requested museum
    4: "ANALYTICS",  # Which clients same restaurants
    5: "LOOKUP",     # Layla and Lily comparison
    6: "LOOKUP",     # Vikram's cars
    7: "LOOKUP",     # Lorenzo's phone
    8: "ANALYTICS",  # Which clients complex condition
    9: "ANALYTICS",  # everyone who visited
    10: "ANALYTICS", # Does anyone prefer
    11: "LOOKUP",    # What did Layla book
    12: "ANALYTICS", # List all spa
    13: "ANALYTICS", # Compare all clients
    14: "ANALYTICS", # Find clients billing
    15: "LOOKUP",    # Vikram's plans
    16: "ANALYTICS", # Who has most bookings
    17: "LOOKUP",    # Sophia's preferences
    18: "ANALYTICS", # Which hotel everyone
    19: "ANALYTICS", # Clients who visited both
    20: "LOOKUP",    # Lorenzo's services
}

# Parse LLM response
lines = [line.strip() for line in classifications.split('\n') if line.strip()]
correct = 0
total = 0

for line in lines:
    if '. ' in line:
        try:
            num_str, classification = line.split('. ', 1)
            num = int(num_str)
            classification = classification.strip().upper()

            # Clean up classification (might have extra text)
            if 'LOOKUP' in classification:
                classification = 'LOOKUP'
            elif 'ANALYTICS' in classification:
                classification = 'ANALYTICS'

            query = test_queries[num - 1]
            expected_class = expected.get(num, "?")

            # Mark correct/incorrect
            is_correct = (classification == expected_class)
            marker = "✅" if is_correct else "❌"

            if is_correct:
                correct += 1
            total += 1

            print(f"{num:<4} {classification:<12} {marker} {query[:57]}")

        except (ValueError, IndexError) as e:
            print(f"Error parsing line: {line}")

# Summary
print("=" * 80)
print(f"\nACCURACY: {correct}/{total} ({100*correct/total:.1f}%)")
print(f"\nLLM Response Token Usage: ~{len(classifications.split())} tokens")

# Show misclassifications in detail
print("\n" + "=" * 80)
print("DETAILED ANALYSIS OF MISCLASSIFICATIONS:")
print("=" * 80)

lines = [line.strip() for line in classifications.split('\n') if line.strip()]
for line in lines:
    if '. ' in line:
        try:
            num_str, classification = line.split('. ', 1)
            num = int(num_str)
            classification = classification.strip().upper()

            if 'LOOKUP' in classification:
                classification = 'LOOKUP'
            elif 'ANALYTICS' in classification:
                classification = 'ANALYTICS'

            expected_class = expected.get(num, "?")

            if classification != expected_class:
                query = test_queries[num - 1]
                print(f"\n❌ Query #{num}: {query}")
                print(f"   Expected: {expected_class}")
                print(f"   Got:      {classification}")
                print(f"   Analysis: ", end="")

                if "which clients" in query.lower():
                    print("Contains 'which clients' → should be ANALYTICS")
                elif any(name in query for name in ['Layla', 'Lily', 'Vikram', 'Lorenzo', 'Sophia']):
                    print("Contains specific name → likely LOOKUP")
                else:
                    print("Edge case - needs review")
        except (ValueError, IndexError):
            pass

print("\n" + "=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)
