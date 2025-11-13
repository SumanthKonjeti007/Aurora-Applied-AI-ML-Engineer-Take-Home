"""
Test entity extraction with Llama 3.1 8B
"""
import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load sample messages
with open('data/raw_messages.json') as f:
    messages = json.load(f)

# Sample messages for testing
test_messages = [
    messages[8],   # Phone number update
    messages[16],  # Thanks for trip
    messages[4],   # Preference (aisle seats)
    messages[9],   # Villa booking
]

print("="*60)
print("ENTITY EXTRACTION TEST - Llama 3.1 8B")
print("="*60)

extraction_prompt_template = """
Extract knowledge graph triples from this message.

User: {user_name}
Message: "{message}"

Extract all meaningful relationships in the format:
(Subject, Relationship, Object, Metadata)

Relationship types:
- OWNS: Permanent ownership (e.g., "my Tesla", "my car")
- RENTED/BOOKED: Temporary booking/rental
- PLANNING_TRIP_TO: Future travel plans
- VISITED: Past travel
- FAVORITE/PREFERS: Preferences
- HAS_CONTACT: Contact information
- DINING_AT: Restaurant reservations
- ATTENDING_EVENT: Event attendance

Rules:
1. Subject is usually the user's name
2. Identify ownership vs rental carefully ("my" = OWNS, "book" = RENTED)
3. Extract specific entities (car model, location names, dates)
4. Include metadata like item_type, date if mentioned

Return ONLY a valid JSON array of triples:
[
  {{
    "subject": "...",
    "relationship": "...",
    "object": "...",
    "metadata": {{...}}
  }}
]

If no meaningful relationships, return empty array: []
"""

for i, msg in enumerate(test_messages, 1):
    print(f"\n{'='*60}")
    print(f"TEST {i}")
    print(f"{'='*60}")
    print(f"User: {msg['user_name']}")
    print(f"Message: {msg['message']}")

    prompt = extraction_prompt_template.format(
        user_name=msg['user_name'],
        message=msg['message']
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured knowledge from text. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )

        result = response.choices[0].message.content
        print(f"\n🤖 LLM Output:")
        print(result)

        # Try to parse JSON
        try:
            triples = json.loads(result)
            print(f"\n✅ Valid JSON! Extracted {len(triples)} triple(s)")
            for triple in triples:
                print(f"  - ({triple.get('subject')}, {triple.get('relationship')}, {triple.get('object')})")
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON Parse Error: {e}")

    except Exception as e:
        print(f"\n❌ Error: {e}")

print("\n" + "="*60)
print("EVALUATION")
print("="*60)
print("\nDoes Llama 3.1 8B extract entities correctly?")
print("If YES → Use it for all messages")
print("If NO → Upgrade to Llama 3.3 70B (still free)")
