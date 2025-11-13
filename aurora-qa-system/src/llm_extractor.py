"""
LLM-based Semantic Extractor (The Reasoner)

Uses LLM for complex messages that require true semantic understanding.
Handles semantic division (e.g., "Bentley for my Paris trip" → two separate triples)
"""
import os
import json
from typing import List, Dict, Optional
from groq import Groq


class LLMSemanticExtractor:
    """
    LLM-based extractor for complex semantic relationships
    Uses Groq (free tier: 30 req/min, 14K tokens/min)
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM extractor

        Args:
            api_key: Groq API key (or set GROQ_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')

        if not self.api_key:
            raise ValueError(
                "Groq API key required. Set GROQ_API_KEY environment variable or pass api_key parameter.\n"
                "Get free API key at: https://console.groq.com/keys"
            )

        self.client = Groq(api_key=self.api_key)

        # Use fast, capable model
        self.model = "llama-3.1-8b-instant"  # Fast, good quality

        # Define valid relationship types
        self.valid_relationships = [
            "OWNS",              # Real ownership: BMW, phone, villa
            "VISITED",           # Past location visits
            "PLANNING_TRIP_TO",  # Future travel plans
            "WANTS_TO_RENT",     # Rental requests (Bentley, yacht, villa)
            "RENTED/BOOKED",     # Completed bookings (seats, tickets, reservations)
            "PREFERS",           # Preferences (cuisine, rooms, seats)
            "FAVORITE",          # Favorites
            "ATTENDING_EVENT",   # Event attendance
        ]

        print("✅ LLM Semantic Extractor initialized (Groq/Llama-3.1-8B)")

    def extract_triples_llm(self, message: Dict) -> List[Dict]:
        """
        Extract semantic triples using LLM

        Args:
            message: Message dict with keys: id, user_name, message, timestamp

        Returns:
            List of knowledge graph triples
        """
        user_name = message.get('user_name', 'Unknown')
        text = message.get('message', '')

        if not text.strip():
            return []

        # Build prompt
        prompt = self._build_extraction_prompt(user_name, text)

        try:
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured knowledge from text. You output ONLY valid JSON, no explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=500,
            )

            # Parse response
            llm_output = response.choices[0].message.content.strip()

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in llm_output:
                llm_output = llm_output.split("```json")[1].split("```")[0].strip()
            elif "```" in llm_output:
                llm_output = llm_output.split("```")[1].split("```")[0].strip()

            # Parse JSON
            triples_data = json.loads(llm_output)

            # Build triples with metadata
            triples = []
            for triple_data in triples_data:
                triple = {
                    'subject': triple_data.get('subject', user_name),
                    'relationship': triple_data.get('relationship'),
                    'object': triple_data.get('object'),
                    'message_id': message.get('id'),
                    'timestamp': message.get('timestamp'),
                    'metadata': {
                        'extractor': 'llm',
                        'model': self.model,
                        'confidence': triple_data.get('confidence', 'high')
                    }
                }

                # Validate relationship type
                if triple['relationship'] in self.valid_relationships:
                    triples.append(triple)

            return triples

        except json.JSONDecodeError as e:
            print(f"⚠️  LLM output parsing error: {e}")
            print(f"   Raw output: {llm_output[:200]}")
            return []
        except Exception as e:
            print(f"⚠️  LLM extraction error: {e}")
            return []

    def _build_extraction_prompt(self, user_name: str, message_text: str) -> str:
        """
        Build the extraction prompt for the LLM

        Args:
            user_name: User's full name
            message_text: Message content

        Returns:
            Formatted prompt string
        """
        relationships_list = "\n".join([f"  - {rel}" for rel in self.valid_relationships])

        prompt = f"""Extract semantic knowledge triples from this concierge service message.

**User Context:**
- User name: "{user_name}"
- This name MUST be used as the subject for all triples

**Valid Relationships:**
{relationships_list}

**Task:**
Analyze the message and extract ALL distinct semantic (Subject, Relationship, Object) triples.

**Critical Rules:**
1. Subject is ALWAYS "{user_name}" (never use pronouns or message text)
2. Perform SEMANTIC DIVISION when needed:
   - "Bentley for my Paris trip" → TWO triples:
     * ({user_name}, WANTS_TO_RENT, Bentley)
     * ({user_name}, PLANNING_TRIP_TO, Paris)
3. Real ownership vs concepts:
   - "my BMW" → OWNS (real asset)
   - "my trip" → NOT OWNS (abstract concept)
4. Only extract SPECIFIC entities as objects:
   - ✅ "BMW", "Paris", "Italian cuisine", "front-row seats"
   - ❌ NOT: "What", "to", "for", "it"
5. Use relationship types that match the semantic intent

**Output Format:**
Return ONLY a valid JSON array of objects. Each object must have:
{{
  "subject": string (always "{user_name}"),
  "relationship": string (from valid list),
  "object": string (specific entity),
  "confidence": "high" | "medium" | "low"
}}

**Message to analyze:**
"{message_text}"

**Output (JSON only, no explanation):**"""

        return prompt

    def extract_from_messages_batch(
        self,
        messages: List[Dict],
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Extract triples from multiple messages using LLM

        Args:
            messages: List of message dicts
            show_progress: Show progress info

        Returns:
            List of all extracted triples
        """
        all_triples = []

        print(f"\n🤖 LLM Extracting from {len(messages)} messages...")
        print(f"   Model: {self.model} (via Groq)")
        print(f"   Rate limit: 30 req/min\n")

        for i, message in enumerate(messages, 1):
            if show_progress and i % 10 == 0:
                print(f"   Processed {i}/{len(messages)} messages...")

            triples = self.extract_triples_llm(message)
            all_triples.extend(triples)

            # Rate limiting (30 req/min = 2 seconds per request)
            if i < len(messages):
                import time
                time.sleep(2.1)  # Slightly over 2 seconds to be safe

        print(f"\n✅ Extracted {len(all_triples)} triples from {len(messages)} messages")
        print(f"   Average: {len(all_triples)/len(messages):.2f} triples per message")

        return all_triples


def test_llm_extractor():
    """Test LLM extractor on sample messages"""
    print("="*80)
    print("LLM SEMANTIC EXTRACTOR TEST")
    print("="*80)

    # Test messages (complex ones that broke the rule-based extractor)
    test_messages = [
        {
            "id": "test1",
            "user_name": "Vikram Desai",
            "message": "Can I get a Bentley for my Paris trip?",
            "timestamp": "2024-01-01"
        },
        {
            "id": "test2",
            "user_name": "Sophia Al-Farsi",
            "message": "What are the best restaurants in Paris?",
            "timestamp": "2024-01-01"
        },
        {
            "id": "test3",
            "user_name": "Hans Müller",
            "message": "I prefer Italian cuisine when dining in New York.",
            "timestamp": "2024-01-01"
        },
        {
            "id": "test4",
            "user_name": "Vikram Desai",
            "message": "Change my car service to the BMW instead of the Mercedes.",
            "timestamp": "2024-01-01"
        }
    ]

    # Initialize
    try:
        extractor = LLMSemanticExtractor()
    except ValueError as e:
        print(f"\n❌ {e}")
        print("\nTo test LLM extractor:")
        print("  1. Get free API key: https://console.groq.com/keys")
        print("  2. Set environment variable: export GROQ_API_KEY='your-key'")
        print("  3. Run this test again")
        return

    # Test each message
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)

    for msg in test_messages:
        print(f"\n{'='*80}")
        print(f"User: {msg['user_name']}")
        print(f"Message: \"{msg['message']}\"")
        print(f"{'='*80}")

        triples = extractor.extract_triples_llm(msg)

        print(f"\nExtracted {len(triples)} triples:")
        for triple in triples:
            print(f"  • ({triple['subject']}, {triple['relationship']}, {triple['object']})")
            if 'confidence' in triple.get('metadata', {}):
                print(f"    Confidence: {triple['metadata']['confidence']}")

    print("\n" + "="*80)
    print("✅ LLM Extractor test complete")
    print("="*80)


if __name__ == "__main__":
    test_llm_extractor()
