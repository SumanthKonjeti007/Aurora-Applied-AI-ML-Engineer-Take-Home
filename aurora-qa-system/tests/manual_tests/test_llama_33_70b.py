"""
Test Llama 3.3 70B quality for entity extraction
"""
import os
import json
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load sample messages
with open('data/raw_messages.json') as f:
    messages = json.load(f)

# Test with diverse examples
test_messages = [
    messages[8],   # Phone number
    messages[16],  # Thanks for trip (past)
    messages[4],   # Preference (aisle seats)
    messages[9],   # Villa booking (future)
    {"user_name": "Vikram Desai", "message": "My Tesla Model S needs service"},  # Ownership
    {"user_name": "Amira", "message": "I love dining at Nobu and Le Bernardin"},  # Favorite restaurants
]

print("="*60)
print("LLAMA 3.3 70B - ENTITY EXTRACTION QUALITY TEST")
print("="*60)

extraction_prompt = """
Extract knowledge graph triples from this message.

User: {user_name}
Message: "{message}"

Relationship types and rules:
- OWNS: Permanent ownership (e.g., "my Tesla", "my car") - NOT rentals
- RENTED/BOOKED: Temporary booking (e.g., "book a villa", "reserve a car")
- PLANNING_TRIP_TO: Future travel plans with location
- VISITED: Past travel (completed trips)
- PREFERS: Preferences and favorites
- HAS_CONTACT: Contact information (phone, email, address)
- DINING_AT: Restaurant reservations (when booking)
- FAVORITE_RESTAURANT: Favorite restaurants (when expressing preference)

Important:
1. Be precise - don't extract vague relationships
2. Past tense = VISITED, future/planning = PLANNING_TRIP_TO
3. "my [item]" = OWNS, "book [item]" = RENTED
4. Only extract clear, meaningful triples

Return ONLY a JSON array:
[{{"subject":"...","relationship":"...","object":"...","metadata":{{}}}}]

Empty array if no clear relationships: []
"""

def extract_json(text):
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    match = re.search(r'\[.*\]', text, re.DOTALL)
    return match.group(0) if match else text

for i, msg in enumerate(test_messages, 1):
    print(f"\n{'='*60}")
    print(f"TEST {i}: {msg.get('user_name')}")
    print(f"{'='*60}")
    print(f"Message: \"{msg['message']}\"")

    prompt = extraction_prompt.format(
        user_name=msg['user_name'],
        message=msg['message']
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured knowledge. Return ONLY valid JSON, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=400
        )

        result = response.choices[0].message.content
        json_str = extract_json(result)
        triples = json.loads(json_str)

        if len(triples) == 0:
            print("\n✓ No clear relationships found (correct)")
        else:
            print(f"\n✅ Extracted {len(triples)} triple(s):")
            for triple in triples:
                rel = triple.get('relationship')
                subj = triple.get('subject')
                obj = triple.get('object')
                meta = triple.get('metadata', {})
                print(f"  • ({subj}, {rel}, {obj})")
                if meta:
                    print(f"    └─ {meta}")

    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Error: {e}")
        print(f"Raw: {result[:200]}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

print("\n" + "="*60)
print("QUALITY ASSESSMENT")
print("="*60)
print("""
Evaluation criteria:
✓ Correct relationship classification (OWNS vs RENTED)
✓ Accurate entity extraction
✓ No hallucinations or vague triples
✓ Proper tense handling (VISITED vs PLANNING_TRIP_TO)
✓ Clean JSON output

If quality is good → Proceed with Llama 3.3 70B ✅
""")
