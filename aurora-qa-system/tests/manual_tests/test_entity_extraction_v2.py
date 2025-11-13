"""
Test entity extraction with improved prompt
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

# Sample messages for testing
test_messages = [
    messages[8],   # Phone number update
    messages[16],  # Thanks for trip
    messages[4],   # Preference (aisle seats)
    messages[9],   # Villa booking
]

print("="*60)
print("ENTITY EXTRACTION TEST V2 - Llama 3.1 8B")
print("="*60)

extraction_prompt_template = """
Extract knowledge graph triples from this message.

User: {user_name}
Message: "{message}"

Relationship types: OWNS, RENTED/BOOKED, PLANNING_TRIP_TO, VISITED, FAVORITE/PREFERS, HAS_CONTACT, DINING_AT, ATTENDING_EVENT

Return ONLY a JSON array, no explanations, no markdown:
[{{"subject":"...","relationship":"...","object":"...","metadata":{{}}}}]

If no relationships: []
"""

def extract_json(text):
    """Extract JSON from text, handling markdown code blocks"""
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)

    # Find JSON array
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return match.group(0)
    return text

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
                {"role": "system", "content": "You are a JSON extraction expert. Return ONLY valid JSON arrays, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )

        result = response.choices[0].message.content

        # Extract JSON
        json_str = extract_json(result)

        # Parse
        triples = json.loads(json_str)

        print(f"\n✅ Extracted {len(triples)} triple(s):")
        for triple in triples:
            print(f"  ({triple.get('subject')}, {triple.get('relationship')}, {triple.get('object')})")
            if triple.get('metadata'):
                print(f"    Metadata: {triple.get('metadata')}")

    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Parse Error: {e}")
        print(f"Raw output: {result}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

print("\n" + "="*60)
print("QUALITY EVALUATION")
print("="*60)
print("""
Check if:
✓ Correct relationship types (OWNS vs RENTED vs PREFERS)
✓ Proper entity extraction (names, items, locations)
✓ Useful metadata
✓ JSON format consistency

If quality is good → Proceed with Llama 3.1 8B ✅
If quality is poor → Upgrade to Llama 3.3 70B
""")
