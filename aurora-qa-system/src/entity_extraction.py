"""
Entity Extraction Module
Extracts knowledge graph triples from messages using Llama 3.3 70B
"""
import os
import json
import re
from typing import List, Dict, Optional
from dotenv import load_dotenv
from groq import Groq
from tqdm import tqdm
import time

load_dotenv()


class EntityExtractor:
    """Extract entities and relationships from messages using LLM"""

    def __init__(self, model: str = None, api_key: str = None):
        """
        Initialize the entity extractor

        Args:
            model: LLM model name (defaults to env var LLM_MODEL)
            api_key: Groq API key (defaults to env var GROQ_API_KEY)
        """
        self.model = model or os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)

        # Prompt template for extraction
        self.extraction_prompt_template = """
Extract knowledge graph triples from this message.

User: {user_name}
Message: "{message}"
Timestamp: {timestamp}

Relationship types and rules:
- OWNS: Permanent ownership (e.g., "my Tesla", "my car", "my yacht") - NOT rentals
- RENTED/BOOKED: Temporary booking (e.g., "book a villa", "reserve a car", "need a sedan")
- PLANNING_TRIP_TO: Future travel plans (e.g., "trip to Paris", "going to London")
- VISITED: Past travel (e.g., "thanks for the trip to Tokyo", "was in Dubai")
- PREFERS: Preferences and favorites (e.g., "I prefer aisle seats", "I like quiet rooms")
- HAS_CONTACT: Contact information (phone, email, address)
- DINING_AT: Restaurant reservations (when booking a table)
- FAVORITE_RESTAURANT: Favorite restaurants (when expressing preference/love)
- ATTENDING_EVENT: Event attendance (tickets, shows, concerts, etc.)

Important rules:
1. Be precise - only extract clear, meaningful relationships
2. Past tense ("was in", "visited", "thanks for trip") = VISITED
3. Future/planning ("going to", "trip to", "book hotel in") = PLANNING_TRIP_TO
4. "my [item]" = OWNS, "book/reserve/need [item]" = RENTED/BOOKED
5. Extract specific entities (Tesla Model S, not just "car")
6. Include metadata when useful (dates, item types, quantities)
7. Don't extract vague or uncertain relationships

Return ONLY a JSON array (no explanations, no markdown):
[{{"subject":"...","relationship":"...","object":"...","metadata":{{}}}}]

Empty array if no clear relationships: []
"""

    def extract_from_message(self, message: Dict) -> List[Dict]:
        """
        Extract triples from a single message

        Args:
            message: Message dict with keys: user_name, message, timestamp

        Returns:
            List of extracted triples
        """
        prompt = self.extraction_prompt_template.format(
            user_name=message.get('user_name', 'Unknown'),
            message=message.get('message', ''),
            timestamp=message.get('timestamp', '')
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured knowledge from text. Return ONLY valid JSON arrays, no explanations or markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )

            result = response.choices[0].message.content

            # Extract JSON from response (handle markdown code blocks)
            json_str = self._extract_json(result)

            # Parse JSON
            triples = json.loads(json_str)

            # Add message_id to each triple
            for triple in triples:
                triple['message_id'] = message.get('id')
                triple['timestamp'] = message.get('timestamp')

            return triples

        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error for message {message.get('id')}: {e}")
            return []
        except Exception as e:
            print(f"⚠️  Error extracting from message {message.get('id')}: {e}")
            return []

    def extract_from_messages_batch(
        self,
        messages: List[Dict],
        batch_size: int = 1,
        delay: float = 0.1
    ) -> List[Dict]:
        """
        Extract triples from multiple messages with batching and rate limiting

        Args:
            messages: List of message dicts
            batch_size: Number of messages to process before delay (for rate limiting)
            delay: Delay in seconds between batches

        Returns:
            List of all extracted triples
        """
        all_triples = []

        print(f"\n🔍 Extracting entities from {len(messages)} messages...")
        print(f"   Model: {self.model}")
        print(f"   Batch size: {batch_size}, Delay: {delay}s\n")

        with tqdm(total=len(messages), desc="Extracting triples") as pbar:
            for i, message in enumerate(messages):
                # Extract from this message
                triples = self.extract_from_message(message)
                all_triples.extend(triples)

                # Update progress
                pbar.update(1)
                pbar.set_postfix({
                    "triples": len(all_triples),
                    "avg": f"{len(all_triples)/(i+1):.2f}"
                })

                # Rate limiting: delay after each batch
                if (i + 1) % batch_size == 0 and (i + 1) < len(messages):
                    time.sleep(delay)

        print(f"\n✅ Extracted {len(all_triples)} triples from {len(messages)} messages")
        print(f"   Average: {len(all_triples)/len(messages):.2f} triples per message")

        return all_triples

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text, handling markdown code blocks

        Args:
            text: Raw text that may contain JSON

        Returns:
            Extracted JSON string
        """
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)

        # Find JSON array
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return match.group(0)

        return text.strip()

    def save_triples(self, triples: List[Dict], filepath: str = "data/triples.json"):
        """
        Save extracted triples to file

        Args:
            triples: List of triples
            filepath: Path to save file
        """
        with open(filepath, 'w') as f:
            json.dump(triples, f, indent=2)
        print(f"✅ Saved {len(triples)} triples to {filepath}")

    def load_triples(self, filepath: str = "data/triples.json") -> List[Dict]:
        """
        Load triples from file

        Args:
            filepath: Path to load file

        Returns:
            List of triples
        """
        with open(filepath, 'r') as f:
            triples = json.load(f)
        print(f"✅ Loaded {len(triples)} triples from {filepath}")
        return triples

    def get_statistics(self, triples: List[Dict]) -> Dict:
        """
        Get statistics about extracted triples

        Args:
            triples: List of triples

        Returns:
            Statistics dict
        """
        from collections import Counter

        relationship_counts = Counter(t.get('relationship') for t in triples)
        subject_counts = Counter(t.get('subject') for t in triples)

        stats = {
            'total_triples': len(triples),
            'unique_subjects': len(subject_counts),
            'unique_relationships': len(relationship_counts),
            'relationship_distribution': dict(relationship_counts.most_common()),
            'top_subjects': dict(subject_counts.most_common(10))
        }

        return stats

    def print_statistics(self, triples: List[Dict]):
        """Print statistics about extracted triples"""
        stats = self.get_statistics(triples)

        print("\n" + "="*60)
        print("EXTRACTION STATISTICS")
        print("="*60)

        print(f"\nTotal triples: {stats['total_triples']}")
        print(f"Unique subjects: {stats['unique_subjects']}")
        print(f"Unique relationships: {stats['unique_relationships']}")

        print("\nRelationship distribution:")
        for rel, count in stats['relationship_distribution'].items():
            pct = (count / stats['total_triples']) * 100
            print(f"  {rel:25s}: {count:4d} ({pct:.1f}%)")

        print("\nTop 10 subjects:")
        for subj, count in stats['top_subjects'].items():
            print(f"  {subj:25s}: {count:4d} triples")


def main():
    """Test entity extraction on sample messages"""
    # Load messages
    with open('data/raw_messages.json') as f:
        messages = json.load(f)

    # Initialize extractor
    extractor = EntityExtractor()

    # Test on first 20 messages
    print("="*60)
    print("ENTITY EXTRACTION TEST")
    print("="*60)

    sample_messages = messages[:20]

    # Extract
    triples = extractor.extract_from_messages_batch(
        sample_messages,
        batch_size=5,
        delay=0.5
    )

    # Show sample results
    print("\n" + "="*60)
    print("SAMPLE RESULTS")
    print("="*60)

    for i, triple in enumerate(triples[:10], 1):
        print(f"\n{i}. ({triple.get('subject')}, {triple.get('relationship')}, {triple.get('object')})")
        if triple.get('metadata'):
            print(f"   Metadata: {triple.get('metadata')}")

    # Statistics
    extractor.print_statistics(triples)

    print("\n" + "="*60)
    print("✅ Entity extraction module working!")
    print("="*60)
    print("\nNext: Run on all 3,349 messages to build complete knowledge graph")


if __name__ == "__main__":
    main()
