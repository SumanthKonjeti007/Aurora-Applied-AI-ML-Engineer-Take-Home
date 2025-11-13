"""
Entity Extraction using GLiNER + spaCy (Industry-Standard Approach)
Zero API costs, processes 3,349 messages in ~20 minutes
"""
import json
import spacy
from typing import List, Dict
from gliner import GLiNER
from tqdm import tqdm
from collections import defaultdict


class GLiNEREntityExtractor:
    """Extract entities and relationships using GLiNER + spaCy dependency parsing"""

    def __init__(self, gliner_model: str = "urchade/gliner_medium-v2.1"):
        """
        Initialize the entity extractor

        Args:
            gliner_model: GLiNER model name (default: medium v2.1)
        """
        print(f"Loading GLiNER model: {gliner_model}...")
        self.gliner = GLiNER.from_pretrained(gliner_model)

        print("Loading spaCy model: en_core_web_sm...")
        self.nlp = spacy.load("en_core_web_sm")

        # Entity labels for member data domain
        self.entity_labels = [
            "person_name",      # Layla, Vikram Desai, Amira
            "location",         # London, Paris, Dubai, Bangalore
            "vehicle",          # Tesla Model S, yacht, car
            "restaurant",       # Nobu, Le Bernardin
            "accommodation",    # villa, hotel, room
            "preference",       # aisle seats, quiet rooms
            "contact_info",     # phone numbers, emails
            "event",           # concert, show, conference
            "time_reference",  # next month, tomorrow, last week
            "service",         # concierge, booking
        ]

        # Relationship type mapping based on verb patterns
        self.relationship_patterns = {
            'own': 'OWNS',
            'have': 'OWNS',
            'has': 'OWNS',
            'book': 'RENTED/BOOKED',
            'reserve': 'RENTED/BOOKED',
            'rent': 'RENTED/BOOKED',
            'need': 'RENTED/BOOKED',
            'plan': 'PLANNING_TRIP_TO',
            'going': 'PLANNING_TRIP_TO',
            'travel': 'PLANNING_TRIP_TO',
            'visit': 'VISITED',
            'visited': 'VISITED',
            'was': 'VISITED',
            'prefer': 'PREFERS',
            'like': 'PREFERS',
            'love': 'FAVORITE',
            'favorite': 'FAVORITE',
            'dining': 'DINING_AT',
            'attend': 'ATTENDING_EVENT',
        }

        print("✅ Entity extractor initialized")

    def extract_entities(self, text: str, threshold: float = 0.5) -> List[Dict]:
        """
        Extract entities from text using GLiNER

        Args:
            text: Input text
            threshold: Confidence threshold for entity extraction

        Returns:
            List of entities with labels and positions
        """
        entities = self.gliner.predict_entities(text, self.entity_labels, threshold=threshold)
        return entities

    def extract_relationships(self, text: str, entities: List[Dict], user_name: str) -> List[Dict]:
        """
        Extract relationships using spaCy dependency parsing

        Args:
            text: Input text
            entities: List of extracted entities
            user_name: User name from message metadata (ALWAYS used as subject)

        Returns:
            List of relationship triples (subject, relationship, object)
        """
        doc = self.nlp(text)
        relationships = []

        # Extract subject-verb-object patterns
        for token in doc:
            # Find subjects (grammatical subjects in message)
            if token.dep_ in ("nsubj", "nsubjpass"):
                # CRITICAL FIX: Always use user_name as subject, not message text
                # This prevents "What", "table", "flight" etc. from being subjects
                subject = user_name
                verb = token.head.text.lower()

                # Find objects related to this verb
                # CRITICAL FIX: Removed "prep" from dependency list
                # "prep" was causing prepositions ("to", "for", "in") to be extracted as objects
                for child in token.head.children:
                    if child.dep_ in ("dobj", "attr", "pobj"):  # Removed "prep"
                        obj = child.text

                        # Map verb to relationship type
                        relationship = self._map_verb_to_relationship(verb, token.head)

                        if relationship:
                            relationships.append({
                                "subject": subject,
                                "relationship": relationship,
                                "object": obj,
                                "verb": verb
                            })

        return relationships

    def _map_verb_to_relationship(self, verb: str, token) -> str:
        """
        Map verb to relationship type based on patterns

        CRITICAL FIX: Removed fallback logic based on verb tense
        This was causing "I received" → VISITED, "I suspect" → PLANNING_TRIP_TO

        Args:
            verb: The verb text
            token: The spaCy token

        Returns:
            Relationship type string or None
        """
        # Check direct verb mapping ONLY
        for pattern, rel_type in self.relationship_patterns.items():
            if pattern in verb:
                return rel_type

        # REMOVED: Verb tense fallback logic
        # Previously ANY past verb → VISITED, ANY present verb → PLANNING_TRIP_TO
        # This caused garbage: "received itinerary" → VISITED "itinerary"

        # Now: If verb not in explicit patterns, return None (ignore it)
        return None

    def extract_from_message(self, message: Dict) -> List[Dict]:
        """
        Extract entities and relationships from a single message

        Args:
            message: Message dict with keys: id, user_name, message, timestamp

        Returns:
            List of knowledge graph triples
        """
        text = message.get('message', '')
        user_name = message.get('user_name', 'Unknown')

        # Extract entities
        entities = self.extract_entities(text)

        # Extract relationships (PASS user_name to ensure it's always used as subject)
        relationships = self.extract_relationships(text, entities, user_name)

        # Build triples
        triples = []
        for rel in relationships:
            # No need to check for 'i', 'my', 'me' anymore - subject is already user_name
            triple = {
                'subject': rel['subject'],  # Already user_name from extract_relationships
                'relationship': rel['relationship'],
                'object': rel['object'],
                'message_id': message.get('id'),
                'timestamp': message.get('timestamp'),
                'metadata': {
                    'verb': rel.get('verb'),
                    'entities': [e['text'] for e in entities]
                }
            }
            triples.append(triple)

        # Extract simple patterns (possessive: "my X")
        possessive_triples = self._extract_possessive_patterns(text, user_name, message)
        triples.extend(possessive_triples)

        return triples

    def _extract_possessive_patterns(self, text: str, user_name: str, message: Dict) -> List[Dict]:
        """
        Extract ownership patterns like 'my Tesla', 'my phone number'

        CRITICAL FIX: Only extract OWNABLE entities, not concepts like "my trip" or "my reservation"

        Args:
            text: Message text
            user_name: User name
            message: Full message dict

        Returns:
            List of ownership triples
        """
        doc = self.nlp(text)
        triples = []

        # Define what types of things are actually OWNABLE
        # These are semantically ownable assets, not abstract concepts
        ownable_keywords = {
            # Vehicles
            'car', 'vehicle', 'tesla', 'bmw', 'mercedes', 'bentley', 'yacht', 'jet', 'plane',
            'bike', 'motorcycle', 'scooter', 'audi', 'porsche', 'ferrari', 'lamborghini',
            # Contact info
            'phone', 'number', 'email', 'address', 'contact',
            # Physical items
            'jacket', 'watch', 'bag', 'luggage', 'passport', 'card', 'credit', 'property',
            'villa', 'house', 'apartment', 'suite', 'office',
            # Pets
            'dog', 'cat', 'pet',
        }

        # Things that are NOT ownable (abstract concepts, services, reservations)
        non_ownable_keywords = {
            'trip', 'visit', 'stay', 'reservation', 'booking', 'flight', 'itinerary',
            'profile', 'account', 'preferences', 'statement', 'bill', 'invoice',
            'experience', 'service', 'request', 'needs', 'event'
        }

        for token in doc:
            # Look for possessive pronouns followed by nouns
            if token.dep_ == "poss" and token.text.lower() in ["my", "our"]:
                # Find the head noun
                head = token.head
                if head.pos_ in ["NOUN", "PROPN"]:
                    # Extract full noun phrase
                    noun_phrase = " ".join([t.text for t in head.subtree])
                    noun_phrase_lower = noun_phrase.lower()

                    # FIX: Check if this is actually an ownable entity
                    # Skip if it contains non-ownable keywords
                    if any(non_own in noun_phrase_lower for non_own in non_ownable_keywords):
                        continue  # Skip "my trip", "my reservation", etc.

                    # Only create OWNS triple if it's an ownable entity
                    if any(own in noun_phrase_lower for own in ownable_keywords):
                        triple = {
                            'subject': user_name,
                            'relationship': 'OWNS',
                            'object': noun_phrase,
                            'message_id': message.get('id'),
                            'timestamp': message.get('timestamp'),
                            'metadata': {'pattern': 'possessive'}
                        }
                        triples.append(triple)

        return triples

    def extract_from_messages_batch(
        self,
        messages: List[Dict],
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Extract triples from multiple messages

        Args:
            messages: List of message dicts
            show_progress: Show progress bar

        Returns:
            List of all extracted triples
        """
        all_triples = []

        print(f"\n🔍 Extracting entities from {len(messages)} messages...")
        print(f"   Using GLiNER + spaCy (local, 0 API costs)")
        print(f"   Estimated time: ~{len(messages) * 0.3 / 60:.1f} minutes\n")

        iterator = tqdm(messages, desc="Extracting") if show_progress else messages

        for message in iterator:
            triples = self.extract_from_message(message)
            all_triples.extend(triples)

        print(f"\n✅ Extracted {len(all_triples)} triples from {len(messages)} messages")
        print(f"   Average: {len(all_triples)/len(messages):.2f} triples per message")

        return all_triples

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
    extractor = GLiNEREntityExtractor()

    # Test on first 50 messages
    print("="*60)
    print("GLiNER + spaCy ENTITY EXTRACTION TEST")
    print("="*60)

    sample_messages = messages[:50]

    # Extract
    triples = extractor.extract_from_messages_batch(sample_messages)

    # Show sample results
    print("\n" + "="*60)
    print("SAMPLE RESULTS")
    print("="*60)

    for i, triple in enumerate(triples[:15], 1):
        print(f"\n{i}. ({triple.get('subject')}, {triple.get('relationship')}, {triple.get('object')})")
        if triple.get('metadata'):
            print(f"   Metadata: {triple.get('metadata')}")

    # Statistics
    extractor.print_statistics(triples)

    print("\n" + "="*60)
    print("✅ GLiNER extraction module working!")
    print("="*60)
    print("\nNext: Run on all 3,349 messages (no rate limits!)")


if __name__ == "__main__":
    main()
