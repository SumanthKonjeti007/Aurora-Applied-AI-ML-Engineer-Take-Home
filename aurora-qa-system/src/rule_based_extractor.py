"""
Enhanced Rule-Based Extractor (Pure Deterministic, No LLM)

Handles 90%+ of messages using:
- spaCy dependency parsing
- Keyword-based relationship mapping
- Ownable vs non-ownable distinction
- Location NER for travel patterns

Goal: raw_messages.json → high-quality triples.json
"""
import json
import spacy
from typing import List, Dict
from tqdm import tqdm
from collections import defaultdict


class RuleBasedExtractor:
    """Pure rule-based triple extractor using spaCy"""

    def __init__(self):
        """Initialize spaCy and define relationship patterns"""
        print("Loading spaCy model: en_core_web_sm...")
        self.nlp = spacy.load("en_core_web_sm")

        # ========== RELATIONSHIP VERB PATTERNS ==========

        # RENTED/BOOKED: Common booking/request verbs
        self.booking_verbs = {
            'book', 'reserve', 'rent', 'need', 'get', 'find',
            'request', 'arrange', 'schedule', 'want'
        }

        # PREFERS: Preference verbs
        self.preference_verbs = {
            'prefer', 'like', 'enjoy', 'love'
        }

        # FAVORITE: Strong preference
        self.favorite_verbs = {
            'favorite', 'favourite', 'adore'
        }

        # PLANNING_TRIP_TO: Future travel
        self.planning_verbs = {
            'plan', 'planning', 'going', 'travel', 'traveling',
            'fly', 'flying', 'head', 'heading'
        }

        # VISITED: Past travel
        self.visited_verbs = {
            'visit', 'visited', 'was', 'went', 'stayed', 'been'
        }

        # ATTENDING_EVENT: Events
        self.event_verbs = {
            'attend', 'attending', 'watch', 'watching', 'see', 'seeing'
        }

        # ========== OWNABLE VS NON-OWNABLE ==========

        # Assets that can be owned
        self.ownable_keywords = {
            'car', 'bmw', 'tesla', 'mercedes', 'bentley', 'vehicle',
            'phone', 'number', 'email', 'address', 'contact',
            'passport', 'document', 'id', 'card',
            'villa', 'apartment', 'house', 'property',
            'yacht', 'boat', 'jet', 'plane',
            'watch', 'jewelry', 'bag', 'luggage',
            'account', 'membership', 'subscription'
        }

        # Abstract concepts (not ownable)
        self.non_ownable_keywords = {
            'trip', 'visit', 'stay', 'vacation', 'holiday',
            'reservation', 'booking', 'appointment',
            'flight', 'ticket', 'itinerary', 'schedule',
            'table', 'seat', 'room',
            'payment', 'bill', 'invoice', 'charge',
            'profile', 'preferences', 'settings',
            'request', 'inquiry', 'question'
        }

        print("✅ Rule-based extractor initialized")

    def extract_from_message(self, message: Dict) -> List[Dict]:
        """
        Extract triples from a single message

        Args:
            message: Message dict with 'user_name', 'message', 'id', 'timestamp'

        Returns:
            List of triple dicts
        """
        text = message.get('message', '')
        user_name = message.get('user_name', 'Unknown')
        message_id = message.get('id')
        timestamp = message.get('timestamp')

        if not text or not user_name:
            return []

        doc = self.nlp(text)
        triples = []

        # ========== EXTRACTION 1: POSSESSIVE OWNS ==========
        possessive_triples = self._extract_possessive_owns(doc, user_name)
        triples.extend(possessive_triples)

        # ========== EXTRACTION 2: VERB-BASED RELATIONSHIPS ==========
        verb_triples = self._extract_verb_relationships(doc, user_name)
        triples.extend(verb_triples)

        # Add metadata to all triples
        for triple in triples:
            triple['message_id'] = message_id
            triple['timestamp'] = timestamp

        return triples

    def _extract_possessive_owns(self, doc, user_name: str) -> List[Dict]:
        """
        Extract OWNS relationships from possessive patterns (my, our)

        Critical: Distinguish ownable assets from abstract concepts
        """
        triples = []

        for token in doc:
            # Match possessive pronouns: my, our, mine
            if token.text.lower() in ('my', 'our', 'mine') and token.pos_ in ('PRON', 'DET'):
                # Get the noun phrase this possessive modifies
                if token.head.pos_ in ('NOUN', 'PROPN'):
                    # Extract full noun phrase (including modifiers)
                    noun_phrase = self._get_noun_phrase(token.head)
                    noun_phrase_lower = noun_phrase.lower()

                    # Check if ownable
                    is_ownable = any(kw in noun_phrase_lower for kw in self.ownable_keywords)
                    is_non_ownable = any(kw in noun_phrase_lower for kw in self.non_ownable_keywords)

                    # Only extract if truly ownable
                    if is_ownable and not is_non_ownable:
                        triples.append({
                            'subject': user_name,
                            'relationship': 'OWNS',
                            'object': noun_phrase
                        })

        return triples

    def _extract_verb_relationships(self, doc, user_name: str) -> List[Dict]:
        """
        Extract relationships based on verb patterns and objects
        """
        triples = []

        for token in doc:
            # Find verbs with subjects
            if token.pos_ == 'VERB':
                verb_lower = token.lemma_.lower()

                # Find objects of this verb
                objects = []
                for child in token.children:
                    if child.dep_ in ('dobj', 'pobj', 'attr'):
                        obj_phrase = self._get_noun_phrase(child)
                        objects.append(obj_phrase)

                if not objects:
                    continue

                # Map verb to relationship type
                for obj in objects:
                    relationship = self._map_verb_to_relationship(
                        verb_lower, obj, doc
                    )

                    if relationship:
                        triples.append({
                            'subject': user_name,
                            'relationship': relationship,
                            'object': obj
                        })

        return triples

    def _map_verb_to_relationship(self, verb: str, obj: str, doc) -> str:
        """
        Map verb to relationship type based on semantic category

        Args:
            verb: Lemmatized verb
            obj: Object phrase
            doc: spaCy doc (for NER)

        Returns:
            Relationship type or None
        """
        # RENTED/BOOKED: Booking/request verbs
        if verb in self.booking_verbs:
            return 'RENTED/BOOKED'

        # PREFERS: Preference verbs
        if verb in self.preference_verbs:
            return 'PREFERS'

        # FAVORITE: Strong preference
        if verb in self.favorite_verbs:
            return 'FAVORITE'

        # PLANNING_TRIP_TO: Future travel (check if object is location)
        if verb in self.planning_verbs:
            if self._is_location(obj, doc):
                return 'PLANNING_TRIP_TO'
            else:
                return 'RENTED/BOOKED'  # "planning a car" = booking

        # VISITED: Past travel (check if object is location)
        if verb in self.visited_verbs:
            if self._is_location(obj, doc):
                return 'VISITED'

        # ATTENDING_EVENT: Events
        if verb in self.event_verbs:
            return 'ATTENDING_EVENT'

        return None

    def _is_location(self, phrase: str, doc) -> bool:
        """Check if phrase is a location using NER"""
        # Use spaCy NER to detect locations
        sub_doc = self.nlp(phrase)
        for ent in sub_doc.ents:
            if ent.label_ in ('GPE', 'LOC', 'FAC'):  # Geopolitical, Location, Facility
                return True

        # Common location keywords as fallback
        location_keywords = {
            'paris', 'london', 'dubai', 'tokyo', 'new york',
            'singapore', 'barcelona', 'rome', 'amsterdam'
        }
        return any(loc in phrase.lower() for loc in location_keywords)

    def _get_noun_phrase(self, token) -> str:
        """Extract full noun phrase including modifiers"""
        # Get subtree (all dependents)
        phrase_tokens = list(token.subtree)
        phrase = ' '.join([t.text for t in phrase_tokens])
        return phrase.strip()

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

        iterator = tqdm(messages, desc="Extracting") if show_progress else messages

        for message in iterator:
            triples = self.extract_from_message(message)
            all_triples.extend(triples)

        return all_triples

    def print_statistics(self, triples: List[Dict]):
        """Print extraction statistics"""
        print(f"\n{'='*60}")
        print("EXTRACTION STATISTICS")
        print(f"{'='*60}")

        print(f"\nTotal triples: {len(triples)}")

        # Group by relationship
        by_relationship = defaultdict(int)
        for triple in triples:
            by_relationship[triple['relationship']] += 1

        print(f"\nBy relationship type:")
        for rel_type in sorted(by_relationship.keys()):
            count = by_relationship[rel_type]
            print(f"  {rel_type:<25} {count:>6}")

        # Unique subjects
        subjects = set(t['subject'] for t in triples)
        print(f"\nUnique subjects: {len(subjects)}")
        print(f"Sample subjects: {list(subjects)[:10]}")

        # Unique objects
        objects = set(t['object'] for t in triples)
        print(f"\nUnique objects: {len(objects)}")
        print(f"Sample objects: {list(objects)[:10]}")

    def save_triples(self, triples: List[Dict], filepath: str):
        """Save triples to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(triples, f, indent=2)
        print(f"\n✅ Saved {len(triples)} triples to {filepath}")


def main():
    """Demo extraction"""
    print("="*60)
    print("RULE-BASED EXTRACTION DEMO")
    print("="*60)

    # Test messages
    test_messages = [
        {
            "id": "1",
            "user_name": "Vikram Desai",
            "message": "I need four front-row seats for the Lakers game.",
            "timestamp": "2024-01-01T10:00:00"
        },
        {
            "id": "2",
            "user_name": "Hans Müller",
            "message": "Can you book a table at Nobu for Friday?",
            "timestamp": "2024-01-01T11:00:00"
        },
        {
            "id": "3",
            "user_name": "Sophia Al-Farsi",
            "message": "I prefer aisle seats on flights.",
            "timestamp": "2024-01-01T12:00:00"
        },
        {
            "id": "4",
            "user_name": "Vikram Desai",
            "message": "Update my BMW registration to my new address.",
            "timestamp": "2024-01-01T13:00:00"
        },
        {
            "id": "5",
            "user_name": "Layla Kawaguchi",
            "message": "I'm planning a trip to Paris next month.",
            "timestamp": "2024-01-01T14:00:00"
        },
        {
            "id": "6",
            "user_name": "Hans Müller",
            "message": "I visited London last week.",
            "timestamp": "2024-01-01T15:00:00"
        }
    ]

    # Extract
    extractor = RuleBasedExtractor()

    print("\n" + "="*60)
    print("EXTRACTING TRIPLES")
    print("="*60)

    for msg in test_messages:
        triples = extractor.extract_from_message(msg)
        print(f"\nMessage: \"{msg['message']}\"")
        print(f"User: {msg['user_name']}")
        print(f"Triples: {len(triples)}")
        for triple in triples:
            print(f"  • ({triple['subject']}, {triple['relationship']}, {triple['object']})")

    print("\n" + "="*60)
    print("✅ Demo complete")
    print("="*60)


if __name__ == "__main__":
    main()
