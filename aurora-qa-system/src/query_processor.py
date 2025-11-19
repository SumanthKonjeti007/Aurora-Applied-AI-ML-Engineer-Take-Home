"""
Query Processor Module

Handles query understanding, decomposition, and dynamic weight assignment.

Architecture:
- Query decomposition: Multi-entity → single-entity sub-queries (LLM-based + rule-based fallback)
- Query classification: Detect query type (entity-specific, conceptual, etc.)
- Dynamic weighting: Assign optimal weights per query type

This keeps HybridRetriever simple by handling complexity upstream.
"""
from typing import List, Dict, Optional
import re
import os
import json
from groq import Groq
# from mistralai import Mistral  # SWITCHED TO GROQ FOR BETTER RATE LIMITS
from src.name_resolver import NameResolver


class QueryProcessor:
    """
    Process user queries: decompose, classify, and assign dynamic weights

    Query Types:
    - ENTITY_SPECIFIC_PRECISE: Entity + specific attribute (e.g., "Lily's dining reservations")
    - ENTITY_SPECIFIC_BROAD: Entity + vague attribute (e.g., "Vikram's expectations")
    - CONCEPTUAL: No entity, conceptual terms (e.g., "relaxing getaway ideas")
    - AGGREGATION: Cross-entity queries (e.g., "which members have...")

    Weight Profiles:
    Each query type gets optimized weights for semantic, BM25, and graph search.
    """

    def __init__(self, name_resolver: NameResolver, use_llm: bool = True, api_key: Optional[str] = None):
        """
        Initialize query processor

        Args:
            name_resolver: NameResolver instance for entity detection
            use_llm: Whether to use LLM for decomposition/optimization (default: True)
            api_key: Mistral API key (optional, uses MISTRAL_API_KEY env var if not provided)
        """
        self.name_resolver = name_resolver
        self.use_llm = use_llm

        # Initialize LLM client if enabled
        self.llm_client = None
        if use_llm:
            try:
                api_key = api_key or os.environ.get('GROQ_API_KEY')
                if api_key:
                    self.llm_client = Groq(api_key=api_key)
                else:
                    print("⚠️  Warning: GROQ_API_KEY not found, falling back to rule-based processing")
                    self.use_llm = False
            except Exception as e:
                print(f"⚠️  Warning: Failed to initialize LLM client: {e}")
                self.use_llm = False

        # Weight profiles with balanced contributions from all three methods
        # All weights kept within similar range (0.9-1.2) with small marginal differences
        self.profiles = {
            # Entity + specific attribute (dining, service, travel)
            # Slight preference for graph (structured relationships) and BM25 (keywords)
            'ENTITY_SPECIFIC_PRECISE': {
                'semantic': 1.0,
                'bm25': 1.2,
                'graph': 1.1
            },

            # Entity + vague attribute (expectations, preferences)
            # Slight preference for BM25 and graph, semantic still contributes
            'ENTITY_SPECIFIC_BROAD': {
                'semantic': 0.9,
                'bm25': 1.2,
                'graph': 1.1
            },

            # Conceptual queries without entities
            # Slight preference for semantic (concept matching), others still contribute
            'CONCEPTUAL': {
                'semantic': 1.2,
                'bm25': 1.0,
                'graph': 0.9
            },

            # Cross-entity aggregation queries
            # ADJUSTED: Strong preference for semantic (Qdrant finds best matches)
            'AGGREGATION': {
                'semantic': 1.5,
                'bm25': 1.0,
                'graph': 0.9
            }
        }

    def route_query(self, query: str, verbose: bool = False) -> str:
        """
        Route query to appropriate pipeline using LLM classification

        Args:
            query: User query string
            verbose: Print routing decision

        Returns:
            "LOOKUP" or "ANALYTICS"
        """
        # Fallback to LOOKUP if LLM not available (safe default)
        if not self.use_llm or not self.llm_client:
            if verbose:
                print("🔀 Router: LLM not available, defaulting to LOOKUP")
            return "LOOKUP"

        # PRE-FILTER RULES: Handle edge cases before LLM
        # These patterns work better with LOOKUP than ANALYTICS
        query_lower = query.lower()

        # "What types..." queries - better with LOOKUP (LLM extracts categories)
        # ANALYTICS has limited entity database, misses diverse categories
        if any(pattern in query_lower for pattern in [
            "what types of",
            "what type of",
            "which types of",
            "what kinds of",
            "what kind of"
        ]):
            if verbose:
                print("🔀 Router: 'What types...' pattern detected → LOOKUP")
            return "LOOKUP"

        # The corrected routing prompt
        prompt = f"""You are a query router for a concierge QA system. Classify the query as LOOKUP or ANALYTICS.

**LOOKUP** - Filter and retrieve messages by specific criteria:
- Asks about specific people (contains names like Layla, Vikram, etc.)
- Filters by specific dates, locations, or attributes
- Can be answered by retrieving and reading relevant messages
- Even if query says "which clients", if it's filtering by ONE specific thing (date/location/attribute), it's LOOKUP
Examples:
  ✓ "What is Layla's phone number?"
  ✓ "Which clients have plans for January 2025?" (filter by specific date)
  ✓ "Which clients visited Paris?" (filter by specific location)
  ✓ "Are there clients who visited both Paris and Tokyo?" (filter by two locations)
  ✓ "Compare Layla and Lily's preferences" (specific named people)
  ✓ "Which clients requested private museum access?" (filter by specific service)
  ✓ "Which clients have billing issues?" (filter by specific issue type)
  ✓ "Vikram's Tokyo plans" (specific person)

**ANALYTICS** - Find patterns through aggregation, grouping, or ranking:
- Requires counting, grouping, finding commonalities, or ranking
- Keywords: "SAME", "MOST", "SIMILAR", "COMMON", "POPULAR", "how many", "count"
- Cannot be answered by simple retrieval - needs to process ALL data and aggregate
Examples:
  ✓ "Which clients requested the SAME restaurants?" (group by restaurant, find overlaps)
  ✓ "Who has the MOST restaurant bookings?" (count per user, rank)
  ✓ "What are the MOST POPULAR destinations?" (count frequency, rank)
  ✓ "What services do MULTIPLE clients prefer?" (count per service)
  ✓ "Find clients with SIMILAR preferences" (compare across all)
  ✓ "Which hotel did EVERYONE book?" (aggregate all bookings)

**Key Distinction:**
- LOOKUP = Filter/retrieve by criteria → "Find all messages matching X"
- ANALYTICS = Aggregate/group/rank → "Find patterns/commonalities across all data"

**Critical Rule:**
- If query contains SAME/MOST/SIMILAR/POPULAR/COUNT → ANALYTICS
- Otherwise, even if "which clients" → LOOKUP

User Query: "{query}"

Classify this query. Respond with ONLY one word: LOOKUP or ANALYTICS

Classification:"""

        try:
            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for deterministic routing
                max_tokens=10
            )

            classification = response.choices[0].message.content.strip().upper()

            # Validate and clean response
            if 'LOOKUP' in classification:
                classification = 'LOOKUP'
            elif 'ANALYTICS' in classification:
                classification = 'ANALYTICS'
            else:
                # Invalid response, default to safe LOOKUP
                if verbose:
                    print(f"⚠️  Router: Unexpected response '{classification}', defaulting to LOOKUP")
                return "LOOKUP"

            if verbose:
                print(f"🔀 Router: {classification}")

            return classification

        except Exception as e:
            # On error, default to LOOKUP (safe fallback)
            if verbose:
                print(f"⚠️  Router: LLM error ({str(e)[:50]}...), defaulting to LOOKUP")
            return "LOOKUP"

    def process(self, query: str, verbose: bool = False) -> List[Dict]:
        """
        Process query: route, decompose if needed, classify, assign weights

        Args:
            query: User query string
            verbose: Print processing details

        Returns:
            List of query plans:
            [
                {
                    'route': 'LOOKUP' or 'ANALYTICS',
                    'query': 'simplified query string',
                    'type': 'query type',
                    'weights': {'semantic': x, 'bm25': y, 'graph': z},
                    'reason': 'classification reasoning'
                },
                ...
            ]
        """
        if verbose:
            print(f"\n{'='*80}")
            print(f"QUERY PROCESSOR")
            print(f"{'='*80}")
            print(f"Original Query: '{query}'")

        # Step 1: Route query to appropriate pipeline
        route = self.route_query(query, verbose=verbose)

        # Step 2: If ANALYTICS, skip decomposition (analytics handles full query)
        if route == "ANALYTICS":
            if verbose:
                print(f"\nDecomposition: SKIPPED (ANALYTICS route - graph pipeline handles full query)")
            sub_queries = [query]
        # Step 3: For LOOKUP, check if aggregation query (GUARDRAIL)
        # Aggregation LOOKUP queries should NOT be decomposed
        elif self._is_aggregation_query(query):
            if verbose:
                print(f"\nDecomposition: SKIPPED (aggregation query detected)")
            sub_queries = [query]
        # Step 4: Decompose if multi-entity comparison (LLM-based if available)
        elif self.use_llm and self.llm_client:
            sub_queries = self._decompose_llm(query, verbose=verbose)
        else:
            sub_queries = self._decompose(query, verbose=verbose)

        # Step 5: Classify each sub-query and assign weights
        plans = []
        for i, sub_q in enumerate(sub_queries, 1):
            classification = self._classify(sub_q)

            plan = {
                'route': route,  # Add routing information
                'query': sub_q,
                'type': classification['type'],
                'weights': classification['weights'],
                'reason': classification['reason']
            }
            plans.append(plan)

            if verbose:
                if len(sub_queries) > 1:
                    print(f"\nSub-Query {i}: '{sub_q}'")
                print(f"  Type: {classification['type']}")
                print(f"  Weights: semantic={classification['weights']['semantic']}, "
                      f"bm25={classification['weights']['bm25']}, "
                      f"graph={classification['weights']['graph']}")
                print(f"  Reason: {classification['reason']}")

        if verbose:
            print(f"{'='*80}\n")

        return plans

    def _is_aggregation_query(self, query: str) -> bool:
        """
        Detect if query is an aggregation query (cross-entity analysis)

        Aggregation queries should NOT be decomposed as they need to analyze
        patterns across ALL users, not individual users.

        Examples:
        - "Which clients have X?"
        - "List all members who Y"
        - "How many people requested Z?"
        - "Who has both A and B?"
        - "What clients complained about X?"

        Args:
            query: User query string

        Returns:
            True if aggregation query, False otherwise
        """
        query_lower = query.lower()

        # Aggregation patterns (expanded to include 'clients', 'users', 'people')
        aggregation_patterns = [
            # Which/What patterns
            'which clients', 'which members', 'which users', 'which people',
            'what clients', 'what members', 'what users',

            # Who patterns
            'who has', 'who have', 'who had', 'who requested', 'who booked',
            'who visited', 'who complained', 'who reported', 'who expressed',
            'who mentioned', 'who needed', 'who wanted',

            # List/All patterns
            'list all clients', 'list all members', 'list all users',
            'all clients who', 'all members who', 'all users who', 'all people who',

            # Count patterns
            'how many clients', 'how many members', 'how many users', 'how many people',
            'count of clients', 'count of members',

            # Conditional patterns (BOTH/AND)
            'clients who have both', 'members who have both', 'users who have both',
            'clients with both', 'members with both',
            'have both', 'with both',
            'both', 'and also'  # Less specific but catches complex conditions
        ]

        # Check if any aggregation pattern is present
        return any(pattern in query_lower for pattern in aggregation_patterns)

    def _decompose_llm(self, query: str, verbose: bool = False) -> List[str]:
        """
        LLM-based query decomposition for multi-entity/complex queries

        Uses LLM to intelligently break down queries into atomic sub-queries.
        Handles: comparisons, conflicts, multi-user queries, complex attributes.

        Args:
            query: User query
            verbose: Print decomposition details

        Returns:
            List of sub-queries (single item if no decomposition needed)
        """
        try:
            # Get list of known users for context
            known_users = self.name_resolver.list_all_users()
            users_list = ", ".join(known_users[:10])  # First 10 users

            prompt = f"""You are a query decomposition expert. Analyze the user query and determine if it needs to be broken down into simpler sub-queries.

Query: "{query}"

Known users in the system: {users_list}

CRITICAL RULES:
1. ONLY decompose EXPLICIT COMPARISON queries between 2+ NAMED users (e.g., "Compare A and B", "Conflict between X and Y")
2. NEVER decompose AGGREGATION queries (e.g., "Which clients...", "Who has...", "List all...")
3. NEVER decompose queries with conditions like "clients who have BOTH X and Y" - these need ALL data, not per-user data
4. Each sub-query must be self-contained and answerable independently
5. Preserve the original attribute/question being asked

WHEN TO DECOMPOSE (comparison of specific named users):
✅ "What are the conflicting flight preferences of Layla and Lily?"
   → ["What are Layla Kawaguchi's flight seating preferences?", "What are Lily O'Sullivan's flight seating preferences?"]

✅ "Compare dining preferences of Thiago and Hans"
   → ["What are Thiago Monteiro's dining preferences?", "What are Hans Müller's dining preferences?"]

WHEN NOT TO DECOMPOSE (aggregation, single user, conditions):
❌ "Which clients have both expressed a preference and complained about a charge?"
   → ["{query}"]  (AGGREGATION with condition - needs ALL users' data together)

❌ "Which members requested luxury vehicles?"
   → ["{query}"]  (AGGREGATION query across all users)

❌ "Who has complained about billing issues?"
   → ["{query}"]  (AGGREGATION - finding which users match criteria)

❌ "List all clients who visited museums"
   → ["{query}"]  (AGGREGATION - collecting users who match)

❌ "What is Fatima's plan in Tokyo?"
   → ["{query}"]  (SINGLE user query, no decomposition needed)

Return ONLY a JSON array of sub-queries, nothing else:
["sub-query 1", "sub-query 2", ...]

If no decomposition needed, return: ["{query}"]"""

            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            # Handle cases where LLM adds markdown code blocks
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            sub_queries = json.loads(result_text)

            if not isinstance(sub_queries, list) or len(sub_queries) == 0:
                # Fallback to original query
                sub_queries = [query]

            if verbose:
                if len(sub_queries) > 1:
                    print(f"\nDecomposition: Multi-entity query detected (LLM-based)")
                    print(f"  Sub-queries: {len(sub_queries)}")
                    for i, sq in enumerate(sub_queries, 1):
                        print(f"    {i}. {sq}")
                else:
                    print(f"\nDecomposition: None (single query - LLM confirmed)")

            return sub_queries

        except Exception as e:
            if verbose:
                print(f"\n⚠️  LLM decomposition failed: {e}")
                print(f"   Falling back to rule-based decomposition")
            # Fallback to rule-based
            return self._decompose(query, verbose=verbose)

    def _decompose(self, query: str, verbose: bool = False) -> List[str]:
        """
        Decompose multi-entity comparison queries into single-entity queries

        Examples:
            "Compare the dining preferences of Thiago and Hans"
            → ["What are Thiago Monteiro's dining preferences?",
               "What are Hans Müller's dining preferences?"]

        Args:
            query: User query
            verbose: Print decomposition details

        Returns:
            List of sub-queries (single item if no decomposition needed)
        """
        query_lower = query.lower()

        # Detect comparison keywords
        is_comparison = any(word in query_lower for word in
                          ['compare', 'versus', 'vs', 'vs.', 'difference between',
                           'conflict', 'conflicting', 'differ', 'between'])

        if not is_comparison:
            if verbose:
                print(f"\nDecomposition: None (single query)")
            return [query]

        # Try to extract all entities mentioned in query
        entities = []
        words = query.split()

        # Try 3-word, 2-word, and 1-word combinations
        for i in range(len(words)):
            for length in [3, 2, 1]:
                if i + length <= len(words):
                    phrase = ' '.join(words[i:i+length])
                    resolved = self.name_resolver.resolve(phrase)
                    if resolved and resolved not in entities:
                        entities.append(resolved)
                        # Skip ahead to avoid overlapping matches
                        break

        # Need at least 2 entities for comparison
        if len(entities) < 2:
            if verbose:
                print(f"\nDecomposition: None (comparison detected but <2 entities found)")
            return [query]

        # Extract attribute being compared
        # Pattern: "compare [the] ATTRIBUTE of X and Y"
        attribute = None

        # Try pattern 1: "compare the X of"
        pattern1 = r"compare\s+(?:the\s+)?(.+?)\s+of"
        match = re.search(pattern1, query_lower)
        if match:
            attribute = match.group(1).strip()

        # If no attribute found, use generic "information about"
        if not attribute:
            attribute = "information about"

        # Generate sub-queries
        sub_queries = [
            f"What are {entity}'s {attribute}?"
            for entity in entities
        ]

        if verbose:
            print(f"\nDecomposition: Comparison query detected")
            print(f"  Entities found: {entities}")
            print(f"  Attribute: '{attribute}'")
            print(f"  Sub-queries: {len(sub_queries)}")

        return sub_queries

    def _classify(self, query: str) -> Dict:
        """
        Classify query type and return weights

        Classification logic:
        1. Check for aggregation keywords (which members, who has, etc.)
        2. Check for entity presence (using NameResolver)
           - If entity + specific attribute → ENTITY_SPECIFIC_PRECISE
           - If entity + vague/no attribute → ENTITY_SPECIFIC_BROAD
        3. Check for conceptual keywords (ideas, luxury, best, etc.)
        4. Default → ENTITY_SPECIFIC_BROAD

        Args:
            query: Query string (single query, not multi-entity comparison)

        Returns:
            {
                'type': 'query type',
                'weights': {'semantic': x, 'bm25': y, 'graph': z},
                'reason': 'why this classification'
            }
        """
        query_lower = query.lower()

        # Priority 1: Aggregation queries (cross-entity)
        aggregation_phrases = [
            'which members', 'which clients', 'which users', 'which people',
            'what clients', 'what members', 'what users',
            'who has', 'who have', 'who had',
            'how many people', 'how many members', 'how many clients', 'how many users',
            'list all', 'all members who', 'all clients who', 'all users who',
            'who requested', 'who booked', 'who visited', 'who complained',
            'clients who', 'members who', 'users who'
        ]

        if any(phrase in query_lower for phrase in aggregation_phrases):
            return {
                'type': 'AGGREGATION',
                'weights': self.profiles['AGGREGATION'],
                'reason': 'Cross-entity aggregation query detected'
            }

        # Priority 2: Entity-specific queries
        entity = self.name_resolver.resolve(query)

        # Debug: Try resolving from query words if full query fails
        if not entity:
            # Extract potential names from query by trying each word/phrase
            words = query.split()
            for i in range(len(words)):
                # Try 2-3 word combinations
                for length in [3, 2]:
                    if i + length <= len(words):
                        phrase = ' '.join(words[i:i+length])
                        entity = self.name_resolver.resolve(phrase)
                        if entity:
                            break
                if entity:
                    break

        if entity:
            # Check for specific attributes
            specific_attrs = [
                'dining', 'restaurant', 'food', 'meal', 'cuisine',
                'service', 'reservation', 'booking', 'rental',
                'travel', 'trip', 'flight', 'hotel', 'accommodation',
                'event', 'ticket', 'concert', 'show'
            ]

            has_specific_attr = any(attr in query_lower for attr in specific_attrs)

            if has_specific_attr:
                return {
                    'type': 'ENTITY_SPECIFIC_PRECISE',
                    'weights': self.profiles['ENTITY_SPECIFIC_PRECISE'],
                    'reason': f'Entity "{entity}" with specific attribute detected'
                }
            else:
                return {
                    'type': 'ENTITY_SPECIFIC_BROAD',
                    'weights': self.profiles['ENTITY_SPECIFIC_BROAD'],
                    'reason': f'Entity "{entity}" with broad/vague attribute'
                }

        # Priority 3: Conceptual queries (no entity)
        conceptual_keywords = [
            'ideas', 'suggestions', 'recommendations', 'recommend',
            'relaxing', 'luxury', 'best', 'top', 'favorite',
            'getaway', 'experience', 'activities', 'what to do',
            'where to go', 'places to visit'
        ]

        if any(keyword in query_lower for keyword in conceptual_keywords):
            return {
                'type': 'CONCEPTUAL',
                'weights': self.profiles['CONCEPTUAL'],
                'reason': 'Conceptual query without specific entity'
            }

        # Default: Treat as entity-specific broad
        return {
            'type': 'ENTITY_SPECIFIC_BROAD',
            'weights': self.profiles['ENTITY_SPECIFIC_BROAD'],
            'reason': 'Default classification (no clear type detected)'
        }


def test_query_processor():
    """Test query processor on sample queries"""
    from src.knowledge_graph import KnowledgeGraph

    print("="*80)
    print("QUERY PROCESSOR TEST")
    print("="*80)

    # Initialize name resolver with real user data
    print("\nInitializing name resolver...")
    kg = KnowledgeGraph()
    kg.load("data/knowledge_graph.pkl")

    name_resolver = NameResolver()
    for user_name in kg.user_index.keys():
        name_resolver.add_user(user_name)

    print(f"✅ Loaded {name_resolver.total_users} users")

    # Initialize processor
    processor = QueryProcessor(name_resolver)

    # Test queries
    test_queries = [
        "What are Vikram Desai's specific service expectations?",
        "What dining reservations has Lily O'Sullivan requested for her trip?",
        "Compare the dining preferences of Thiago Monteiro and Hans Müller",
        "Show me ideas for a relaxing getaway",
        "Which members requested luxury vehicles?"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {query}")
        print(f"{'='*80}")

        plans = processor.process(query, verbose=True)

        print(f"\nOUTPUT: {len(plans)} query plan(s)")


if __name__ == "__main__":
    test_query_processor()
