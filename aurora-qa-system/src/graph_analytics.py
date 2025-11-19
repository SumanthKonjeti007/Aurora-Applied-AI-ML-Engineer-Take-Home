"""
Graph Analytics Pipeline

Handles ANALYTICS queries that require aggregation, grouping, or pattern finding.
Uses Knowledge Graph for structured querying instead of RAG retrieval.

Query Flow:
1. Extract entity type from query (LLM)
2. Query graph for all relevant triples
3. Resolve entity names (group variants)
4. Aggregate (GROUP BY entity, COUNT users)
5. Generate natural language answer (LLM)
"""
import os
import json
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
# from groq import Groq  # COMMENTED OUT
from groq import Groq  # SWITCHED TO GROQ
from src.knowledge_graph import KnowledgeGraph


class GraphAnalytics:
    """
    Analytics engine for aggregation queries using Knowledge Graph

    Handles queries like:
    - "Which clients requested SAME restaurants?"
    - "Who has the MOST bookings?"
    - "What are the MOST POPULAR destinations?"
    """

    def __init__(self, knowledge_graph: KnowledgeGraph, api_key: Optional[str] = None):
        """
        Initialize Graph Analytics

        Args:
            knowledge_graph: Loaded KnowledgeGraph instance
            api_key: Mistral API key (optional, uses env var if not provided)
        """
        self.kg = knowledge_graph

        # Initialize LLM client
        api_key = api_key or os.environ.get('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        self.llm = Groq(api_key=api_key)

    def analyze(self, query: str, verbose: bool = False) -> Dict:
        """
        Analyze query using graph aggregation

        Args:
            query: User query (already classified as ANALYTICS)
            verbose: Print processing details

        Returns:
            {
                'answer': str,           # Natural language answer
                'aggregated_data': dict, # Structured aggregation results
                'entity_type': str,      # Detected entity type
                'method': str            # Aggregation method used
            }
        """
        if verbose:
            print(f"\n{'='*80}")
            print(f"GRAPH ANALYTICS PIPELINE")
            print(f"{'='*80}")
            print(f"Query: '{query}'")

        # Step 1: Extract entity type and aggregation method
        entity_type, method, keywords = self._extract_entity_info(query, verbose=verbose)

        # Step 2: Query graph for relevant triples
        triples = self._query_graph(entity_type, keywords, verbose=verbose)

        if not triples:
            return {
                'answer': f"No data found for {entity_type} in the knowledge base.",
                'aggregated_data': {},
                'entity_type': entity_type,
                'method': method
            }

        # Step 3: Aggregate data
        aggregated = self._aggregate_triples(triples, method, verbose=verbose)

        # Step 4: Generate natural language answer
        answer = self._generate_answer(query, aggregated, entity_type, method, verbose=verbose)

        if verbose:
            print(f"{'='*80}\n")

        return {
            'answer': answer,
            'aggregated_data': aggregated,
            'entity_type': entity_type,
            'method': method
        }

    def _extract_entity_info(self, query: str, verbose: bool = False) -> Tuple[str, str, List[str]]:
        """
        Extract entity type and aggregation method from query using LLM

        Args:
            query: User query
            verbose: Print extraction details

        Returns:
            (entity_type, aggregation_method, keywords)
        """
        prompt = f"""Extract information from this analytics query:

Query: "{query}"

Extract:
1. Entity type: What is the user asking about? (restaurant, hotel, destination, service, etc.)
2. Aggregation method: What type of analysis? (SAME, MOST, POPULAR, SIMILAR, COUNT)
3. Keywords: Key search terms to find relevant data

Respond in JSON format:
{{
  "entity_type": "restaurant" | "hotel" | "destination" | "service" | etc.,
  "method": "SAME" | "MOST" | "POPULAR" | "SIMILAR" | "COUNT",
  "keywords": ["keyword1", "keyword2", ...]
}}

JSON:"""

        try:
            response = self.llm.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )

            result = json.loads(response.choices[0].message.content.strip())
            entity_type = result.get('entity_type', 'entity')
            method = result.get('method', 'SAME')
            keywords = result.get('keywords', [])

            if verbose:
                print(f"\n📊 Entity Extraction:")
                print(f"   Entity type: {entity_type}")
                print(f"   Method: {method}")
                print(f"   Keywords: {keywords}")

            return entity_type, method, keywords

        except Exception as e:
            # Fallback: simple keyword extraction
            if verbose:
                print(f"⚠️  LLM extraction failed ({str(e)[:50]}), using fallback")

            query_lower = query.lower()

            # Detect entity type
            if any(word in query_lower for word in ['restaurant', 'dining', 'table']):
                entity_type = 'restaurant'
            elif any(word in query_lower for word in ['hotel', 'resort', 'room']):
                entity_type = 'hotel'
            elif any(word in query_lower for word in ['destination', 'city', 'country', 'location']):
                entity_type = 'destination'
            else:
                entity_type = 'service'

            # Detect method
            if 'similar' in query_lower or 'similarity' in query_lower:
                method = 'SIMILAR'
            elif 'same' in query_lower:
                method = 'SAME'
            elif 'most' in query_lower or 'popular' in query_lower:
                method = 'MOST'
            else:
                method = 'SAME'

            keywords = [entity_type]

            return entity_type, method, keywords

    def _query_graph(self, entity_type: str, keywords: List[str], verbose: bool = False) -> List[Dict]:
        """
        Query knowledge graph for relevant triples

        Args:
            entity_type: Type of entity to search for
            keywords: Keywords to match
            verbose: Print query details

        Returns:
            List of relevant triples
        """
        relevant_triples = []

        # Known specific entities to look for (based on entity type)
        known_entities_by_type = {
            'restaurant': [
                'Osteria Francescana', 'Eleven Madison Park', 'Le Bernardin',
                'The River Café', 'Alinea', 'The Ivy', 'Noma', 'River Café'
            ],
            'hotel': [
                'Four Seasons', 'The Peninsula', 'Park Hyatt', 'The Ritz',
                'Peninsula', 'Ritz'
            ],
            'destination': ['Paris', 'Tokyo', 'London', 'Dubai', 'New York', 'Santorini'],
            'service': ['private jet', 'yacht', 'spa', 'golf', 'museum']
        }

        # Get known entities for this type
        known_entities = known_entities_by_type.get(entity_type, [])

        # Search through all graph edges
        for u, v, data in self.kg.graph.edges(data=True):
            obj = data.get('metadata', {}).get('object', v)
            obj_lower = obj.lower()

            # Strategy 1: Match known specific entities
            matched = False
            for entity in known_entities:
                if entity.lower() in obj_lower:
                    triple = {
                        'subject': u,  # user name
                        'relationship': data.get('relationship'),
                        'object': obj,
                        'message_id': data.get('message_id'),
                        'timestamp': data.get('timestamp')
                    }
                    relevant_triples.append(triple)
                    matched = True
                    break

            # Strategy 2: If no known entities, use keyword matching
            # But be more selective - only match if keywords are substantial part
            if not matched and not known_entities:
                if any(keyword.lower() in obj_lower for keyword in keywords):
                    triple = {
                        'subject': u,
                        'relationship': data.get('relationship'),
                        'object': obj,
                        'message_id': data.get('message_id'),
                        'timestamp': data.get('timestamp')
                    }
                    relevant_triples.append(triple)

        if verbose:
            print(f"\n🔍 Graph Query:")
            print(f"   Entity type: {entity_type}")
            print(f"   Searching for known entities: {known_entities[:3]}...")
            print(f"   Found {len(relevant_triples)} triples")

        return relevant_triples

    def _aggregate_triples(self, triples: List[Dict], method: str, verbose: bool = False) -> Dict:
        """
        Aggregate triples using specified method

        Args:
            triples: List of triples from graph
            method: Aggregation method (SAME, MOST, SIMILAR, etc.)
            verbose: Print aggregation details

        Returns:
            Aggregated data structure
        """
        if method == 'SIMILAR':
            # For similarity: compute user-to-preferences mapping
            # Then the LLM can analyze overlap between users
            user_preferences = defaultdict(set)

            for triple in triples:
                user = triple['subject']
                entity = self._extract_entity_name(triple['object'])
                user_preferences[user].add(entity)

            # Convert sets to lists for JSON serialization
            aggregated = {
                user: list(prefs)
                for user, prefs in user_preferences.items()
            }

            if verbose:
                print(f"\n📈 Aggregation ({method}):")
                print(f"   Unique clients: {len(aggregated)}")
                if aggregated:
                    top_3 = list(aggregated.items())[:3]
                    for user, prefs in top_3:
                        print(f"   - {user}: {len(prefs)} preferences {prefs[:2]}")

            return aggregated

        elif method in ['SAME', 'POPULAR', 'MOST']:
            # Group by entity, count users per entity
            entity_users = defaultdict(set)

            for triple in triples:
                # Extract entity name from object (simple extraction)
                entity = self._extract_entity_name(triple['object'])
                entity_users[entity].add(triple['subject'])

            # Convert sets to lists and sort
            aggregated = {
                entity: list(users)
                for entity, users in entity_users.items()
            }

            # Filter and sort based on method
            if method == 'SAME':
                # Only entities with multiple users
                aggregated = {
                    entity: users
                    for entity, users in aggregated.items()
                    if len(users) > 1
                }
                # Sort by user count (descending)
                aggregated = dict(sorted(aggregated.items(), key=lambda x: len(x[1]), reverse=True))

            elif method in ['MOST', 'POPULAR']:
                # Sort by user count (descending)
                aggregated = dict(sorted(aggregated.items(), key=lambda x: len(x[1]), reverse=True))

            if verbose:
                print(f"\n📈 Aggregation ({method}):")
                print(f"   Unique entities: {len(aggregated)}")
                if aggregated:
                    top_3 = list(aggregated.items())[:3]
                    for entity, users in top_3:
                        print(f"   - {entity}: {len(users)} users {users[:2]}")

            return aggregated

        # Default: return raw grouped data
        return {triple['object']: [triple['subject']] for triple in triples}

    def _extract_entity_name(self, obj_text: str) -> str:
        """
        Extract canonical entity name from object text

        Args:
            obj_text: Object text from triple

        Returns:
            Canonical entity name
        """
        # List of known entities to extract (restaurants, hotels, etc.)
        # Order matters: check specific names before generic terms
        known_entities = [
            # Restaurants (most specific first)
            'Osteria Francescana', 'Eleven Madison Park', 'Le Bernardin',
            'The River Café', 'Alinea', 'The Ivy', 'Noma',
            # Hotels
            'Four Seasons', 'The Peninsula', 'Park Hyatt', 'The Ritz',
            # Cities (less specific)
            'Santorini', 'New York', 'Paris', 'Tokyo', 'London', 'Dubai',
            # Services
            'private jet', 'yacht', 'spa', 'golf', 'museum'
        ]

        obj_lower = obj_text.lower()

        # Try to find known entity (check longest/most specific first)
        for entity in known_entities:
            if entity.lower() in obj_lower:
                return entity

        # If no known entity found, try to extract proper nouns
        # Look for capitalized words (likely proper nouns)
        words = obj_text.split()
        proper_nouns = []
        for i, word in enumerate(words):
            # Skip common words
            if word.lower() in ['a', 'the', 'at', 'in', 'for', 'on', 'to', 'of', 'and']:
                continue
            # Check if capitalized
            if word and word[0].isupper():
                proper_nouns.append(word)
                # Take up to 3 consecutive capitalized words
                if len(proper_nouns) == 3:
                    break

        if proper_nouns:
            return ' '.join(proper_nouns)

        # Final fallback: return first 3-4 meaningful words
        meaningful_words = [w for w in words if w.lower() not in [
            'a', 'the', 'at', 'in', 'for', 'on', 'to', 'of', 'and', 'reservation', 'table'
        ]][:4]

        return ' '.join(meaningful_words) if meaningful_words else obj_text[:30]

    def _generate_answer(self, query: str, aggregated: Dict, entity_type: str,
                        method: str, verbose: bool = False) -> str:
        """
        Generate natural language answer from aggregated data

        Args:
            query: Original user query
            aggregated: Aggregated data
            entity_type: Entity type
            method: Aggregation method
            verbose: Print generation details

        Returns:
            Natural language answer
        """
        # Format aggregated data for LLM
        formatted_data = json.dumps(aggregated, indent=2)

        # Customize instructions based on aggregation method
        if method == "SIMILAR":
            instructions = f"""Instructions for SIMILARITY ANALYSIS:
1. Analyze which clients share the MOST overlapping preferences
2. Group clients into similarity clusters based on shared {entity_type}s
3. Calculate similarity levels:
   - Highly similar: clients who share 3+ {entity_type}s
   - Moderately similar: clients who share 2 {entity_type}s
   - Individual: clients with unique preferences
4. Present results in this format:

**Highly Similar Clients:**
- Group 1: [Client A, Client B, Client C] - All prefer: [list shared {entity_type}s]
- Group 2: [Client D, Client E] - Both prefer: [list shared {entity_type}s]

**Moderately Similar Clients:**
- [Client F, Client G] - Share: [list shared {entity_type}s]

**Key Insight:** [1-sentence summary of the main similarity pattern discovered]

5. Focus on identifying PATTERNS and GROUPINGS, not just listing all clients
6. Be specific about what makes clients similar"""

        elif method == "SAME":
            instructions = f"""Instructions for SAME ENTITY ANALYSIS:
1. List each {entity_type} that was requested by MULTIPLE clients (2 or more)
2. For each {entity_type}, clearly list which clients requested it
3. Format as:

**{entity_type.title()}s with Multiple Clients:**

- **[Entity Name 1]**: Requested by [Client A], [Client B], [Client C] (3 clients)
- **[Entity Name 2]**: Requested by [Client D], [Client E] (2 clients)

4. Sort by number of clients (most popular first)
5. Focus on exact matches - same {entity_type} name
6. If no {entity_type}s have multiple clients, state: "No {entity_type}s were requested by multiple clients."
7. Include a summary at the end: "In total, [X] {entity_type}s were shared among multiple clients." """

        elif method in ["MOST", "POPULAR"]:
            instructions = f"""Instructions for POPULARITY RANKING:
1. Rank {entity_type}s by popularity (number of clients who requested them)
2. Present as a ranked list:

**Most Popular {entity_type.title()}s:**

1. **[Entity Name 1]** - Requested by [X] clients: [Client A, Client B, Client C, ...]
2. **[Entity Name 2]** - Requested by [Y] clients: [Client D, Client E, ...]
3. **[Entity Name 3]** - Requested by [Z] clients: [Client F, Client G, ...]

3. Show at least top 5 if available
4. Include the actual client names (not just counts)
5. End with: "Total unique {entity_type}s: [N]" """

        else:
            # Default generic instructions
            instructions = f"""Instructions:
- Answer the query based on the aggregated data
- Be specific: mention {entity_type} names and client names
- If multiple {entity_type}s found, list them clearly
- Group or organize the information logically
- Keep answer concise and natural"""

        prompt = f"""You are an intelligent concierge assistant answering a query using aggregated client data.

QUESTION: "{query}"

DATA:
{formatted_data}

{instructions}

UI DISPLAY REQUIREMENTS:
- Write for a clean UI display (no technical jargon)
- Start with a summary count or key insight
- Use bullet points or numbered lists for clarity
- Keep it conversational and professional
- NEVER reference "aggregated data", "context", or "knowledge graph" - just state facts naturally

Answer:"""

        try:
            response = self.llm.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )

            answer = response.choices[0].message.content.strip()

            if verbose:
                print(f"\n💬 Answer Generated:")
                print(f"   {answer[:100]}...")

            return answer

        except Exception as e:
            # Fallback: simple formatting
            if not aggregated:
                return f"No {entity_type}s found with {method.lower()} pattern."

            lines = [f"Found {len(aggregated)} {entity_type}(s):"]
            for entity, users in list(aggregated.items())[:5]:
                lines.append(f"- {entity}: {', '.join(users[:3])} ({len(users)} total)")

            return '\n'.join(lines)


def test_graph_analytics():
    """Test Graph Analytics Pipeline"""
    print("=" * 80)
    print("GRAPH ANALYTICS PIPELINE TEST")
    print("=" * 80)

    # Load knowledge graph
    print("\nLoading knowledge graph...")
    kg = KnowledgeGraph()
    kg.load('data/knowledge_graph.pkl')

    # Initialize analytics
    analytics = GraphAnalytics(kg)

    # Test query
    query = "Which clients requested reservations at the same restaurants?"

    print(f"\nTest Query: {query}")
    print("-" * 80)

    result = analytics.analyze(query, verbose=True)

    print("\n" + "=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"\nAnswer: {result['answer']}")
    print(f"\nEntity Type: {result['entity_type']}")
    print(f"Method: {result['method']}")
    print(f"Entities Found: {len(result['aggregated_data'])}")

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_graph_analytics()
