"""
Hybrid Retrieval Module
Combines semantic search, BM25 keyword search, and knowledge graph using RRF fusion

Architecture:
- Parallel retrieval from 3 sources
- Reciprocal Rank Fusion (RRF) for score combination
- Configurable method weights
"""
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from src.qdrant_search import QdrantSearch  # NEW: Replaces EmbeddingIndex
from src.temporal_analyzer import TemporalAnalyzer  # NEW: For date extraction
from src.bm25_search import BM25Search
from src.knowledge_graph import KnowledgeGraph
from src.name_resolver import NameResolver


class HybridRetriever:
    """
    Hybrid retrieval combining semantic, keyword, and graph search using RRF
    """

    def __init__(
        self,
        embedding_path: str = "data/embeddings",
        bm25_path: str = "data/bm25",
        graph_path: str = "data/knowledge_graph.pkl"
    ):
        """
        Initialize hybrid retriever

        Args:
            embedding_path: Path to embeddings index
            bm25_path: Path to BM25 index
            graph_path: Path to knowledge graph
        """
        print("\n🔧 Initializing Hybrid Retriever...")

        # Load semantic search (Qdrant with temporal filtering)
        print("  1/4 Loading semantic search (Qdrant)...")
        self.qdrant_search = QdrantSearch()

        # Load keyword search (BM25 - unchanged)
        print("  2/4 Loading keyword search (BM25)...")
        self.bm25_search = BM25Search()
        self.bm25_search.load(bm25_path)

        # Load knowledge graph (unchanged)
        print("  3/4 Loading knowledge graph...")
        self.knowledge_graph = KnowledgeGraph()
        self.knowledge_graph.load(graph_path)

        # Initialize name resolver (unchanged)
        print("  4/4 Building name resolver...")
        self.name_resolver = NameResolver()
        for user_name in self.knowledge_graph.user_index.keys():
            self.name_resolver.add_user(user_name)
        print(f"       Indexed {self.name_resolver.total_users} users")

        # Initialize temporal analyzer (NEW)
        self.temporal_analyzer = TemporalAnalyzer()

        print("✅ Hybrid Retriever ready!")

    def search(
        self,
        query: str,
        top_k: int = 10,
        semantic_top_k: int = 20,
        bm25_top_k: int = 20,
        graph_top_k: int = 10,
        rrf_k: int = 60,
        weights: Optional[Dict[str, float]] = None,
        query_type: str = "AGGREGATION",
        verbose: bool = False
    ) -> List[Tuple[Dict, float]]:
        """
        Hybrid search with RRF fusion

        Args:
            query: Search query
            top_k: Number of final results to return
            semantic_top_k: Number of results from semantic search
            bm25_top_k: Number of results from BM25
            graph_top_k: Number of results from graph
            rrf_k: RRF constant (default 60)
            weights: Method weights {'semantic': w1, 'bm25': w2, 'graph': w3}
            query_type: Query classification (AGGREGATION, ENTITY_SPECIFIC_BROAD, etc.)
            verbose: Print retrieval details

        Returns:
            List of (message, rrf_score) tuples sorted by score
        """
        # Default weights: Boost BM25 (best for keyword/user matching)
        if weights is None:
            weights = {'semantic': 0.7, 'bm25': 1.5, 'graph': 0.8}

        if verbose:
            print(f"\n🔍 Hybrid Search: '{query}'")
            print(f"   Weights: {weights}")

        # ========== USER DETECTION ==========
        # Detect user in query for filtering (e.g., "Fatima's plan" → filter to Fatima's messages)
        # Extract user names from query (same logic as _graph_search)
        users_detected = []
        query_words = query.split()
        for word in query_words:
            # Remove punctuation
            word = word.strip('.,!?;:\'"')
            resolved_name = self.name_resolver.resolve(word, fuzzy_threshold=0.85)
            if resolved_name and resolved_name not in users_detected:
                users_detected.append(resolved_name)

        user_id = None
        if users_detected:
            # Get user_id for first detected user
            user_id = self.name_resolver.get_user_id(users_detected[0])
            if verbose and user_id:
                print(f"   🔍 User filtering: {users_detected[0]} (id: {user_id[:8]}...)")

        # ========== TEMPORAL DETECTION (NEW) ==========
        # Extract date range from query for temporal filtering
        date_range = self.temporal_analyzer.extract_date_range(query)
        if verbose and date_range:
            print(f"   📅 Temporal filtering: {date_range[0]} to {date_range[1]}")

        # ========== RETRIEVAL 1: SEMANTIC SEARCH (QDRANT) ==========
        if verbose:
            print(f"\n  1/3 Semantic search (Qdrant, top {semantic_top_k})...")

        # NEW: Pass date_range to Qdrant for Filter-then-Rank
        semantic_results_raw = self.qdrant_search.search(
            query,
            top_k=semantic_top_k,
            user_id=user_id,
            date_range=date_range  # NEW: Temporal filtering
        )

        # Convert Qdrant format to hybrid retriever format
        semantic_results = [(r, r['score']) for r in semantic_results_raw]

        if verbose:
            print(f"      Retrieved {len(semantic_results)} results")
            if date_range:
                date_matches = sum(1 for r in semantic_results_raw if r['normalized_dates'])
                print(f"      Messages with dates: {date_matches}/{len(semantic_results)}")

        # ========== RETRIEVAL 2: BM25 KEYWORD SEARCH ==========
        if verbose:
            print(f"\n  2/3 BM25 keyword search (top {bm25_top_k})...")

        bm25_results = self.bm25_search.search(query, top_k=bm25_top_k, user_id=user_id)

        # POST-FILTER: Apply temporal filter to BM25 results if date_range specified
        if date_range:
            bm25_results = self._filter_by_date_range(bm25_results, date_range)

        if verbose:
            print(f"      Retrieved {len(bm25_results)} results")
            if date_range:
                print(f"      (after temporal filtering)")

        # ========== RETRIEVAL 3: KNOWLEDGE GRAPH ==========
        if verbose:
            print(f"\n  3/3 Knowledge graph search (top {graph_top_k})...")

        graph_results = self._graph_search(query, top_k=graph_top_k, verbose=verbose)

        # POST-FILTER: Apply temporal filter to Graph results if date_range specified
        if date_range:
            graph_results = self._filter_by_date_range(graph_results, date_range)

        if verbose:
            print(f"      Retrieved {len(graph_results)} results")
            if date_range:
                print(f"      (after temporal filtering)")

        # ========== RRF FUSION ==========
        if verbose:
            print(f"\n  🔀 Applying RRF fusion (k={rrf_k})...")

        fused_results = self._reciprocal_rank_fusion(
            semantic_results,
            bm25_results,
            graph_results,
            k=rrf_k,
            weights=weights
        )

        if verbose:
            print(f"      Fused {len(fused_results)} unique messages")

        # ========== DIVERSITY ENFORCEMENT (CONDITIONAL) ==========
        # Apply diversity ONLY for AGGREGATION queries to prevent user over-representation
        # For ENTITY_SPECIFIC queries, allow more messages per user for complete context

        if query_type == "AGGREGATION":
            # Aggregation queries: Need diversity across users (max 2 per user)
            diverse_results = self._diversify_by_user(fused_results, max_per_user=2, top_k=top_k)

            if verbose:
                print(f"      Applied diversity filter (AGGREGATION: max 2 per user)")
                print(f"      Returning top {len(diverse_results)}")
                user_dist = {}
                for msg, _ in diverse_results:
                    user = msg.get('user_name', 'Unknown')
                    user_dist[user] = user_dist.get(user, 0) + 1
                print(f"      User distribution: {user_dist}")

            return diverse_results

        else:
            # Entity-specific queries: Allow high user concentration for complete context
            # Use diversity with high limit (10) or just take top_k
            diverse_results = self._diversify_by_user(fused_results, max_per_user=10, top_k=top_k)

            if verbose:
                print(f"      Applied diversity filter (ENTITY_SPECIFIC: max 10 per user)")
                print(f"      Returning top {len(diverse_results)}")
                user_dist = {}
                for msg, _ in diverse_results:
                    user = msg.get('user_name', 'Unknown')
                    user_dist[user] = user_dist.get(user, 0) + 1
                print(f"      User distribution: {user_dist}")

            return diverse_results

    def _filter_by_date_range(
        self,
        results,
        date_range: Tuple[str, str]
    ):
        """
        Filter results to only include messages within the specified date range

        Args:
            results: List of (message_dict, score) tuples OR List of message_dicts
            date_range: (start_date, end_date) in ISO format

        Returns:
            Filtered list in same format as input
        """
        from datetime import datetime, timedelta

        start_date_str, end_date_str = date_range
        start = datetime.fromisoformat(start_date_str).date()
        end = datetime.fromisoformat(end_date_str).date()

        # Detect input format
        if not results:
            return results

        # Check if results are tuples (msg, score) or just dicts
        is_tuple_format = isinstance(results[0], tuple)

        filtered = []
        for item in results:
            # Extract message dict
            if is_tuple_format:
                msg, score = item
            else:
                msg = item
                score = None

            # Get normalized_dates from message
            normalized_dates = msg.get('normalized_dates', [])

            # If no dates in message, exclude it
            if not normalized_dates:
                continue

            # Check if any date in message falls within the range
            has_matching_date = False
            for date_str in normalized_dates:
                try:
                    msg_date = datetime.fromisoformat(date_str).date()
                    if start <= msg_date <= end:
                        has_matching_date = True
                        break
                except (ValueError, TypeError):
                    continue

            if has_matching_date:
                if is_tuple_format:
                    filtered.append((msg, score))
                else:
                    filtered.append(msg)

        return filtered

    def _graph_search(
        self,
        query: str,
        top_k: int = 10,
        verbose: bool = False
    ) -> List[Dict]:
        """
        Search knowledge graph for relevant messages

        Strategy:
        1. Extract user names from query (check against known users)
        2. Extract keywords for entity matching
        3. Get user relationships from graph
        4. Filter by keyword relevance

        Args:
            query: Search query
            top_k: Number of results
            verbose: Print details

        Returns:
            List of message dicts
        """
        # Extract potential user names using NameResolver
        query_lower = query.lower()

        # Strip possessive forms and punctuation for better matching
        # "Hans's" -> "Hans", "preferences?" -> "preferences"
        import re
        query_normalized = re.sub(r"'s\b", "", query_lower)  # Remove possessive 's
        query_normalized = re.sub(r'[^\w\s]', ' ', query_normalized)  # Remove punctuation

        users_found = []

        # Use NameResolver to resolve partial names and typos
        # Extract potential name words from query (skip short words and stop words)
        stop_words = {'how', 'many', 'what', 'when', 'where', 'who', 'is', 'are',
                     'the', 'a', 'an', 'does', 'do', 'have', 'has', 's', 'my', 'his', 'her'}

        query_words = query_normalized.split()

        for word in query_words:
            # Skip short words and stop words
            if len(word) <= 2 or word in stop_words:
                continue

            # Try to resolve this word as a name
            resolved_name = self.name_resolver.resolve(word, fuzzy_threshold=0.85)

            if resolved_name and resolved_name not in users_found:
                users_found.append(resolved_name)

        if verbose and users_found:
            print(f"      Users detected: {users_found}")

        # Extract keywords (simple: split and filter stop words)
        # Use normalized query to avoid punctuation in keywords
        stop_words = {'how', 'many', 'what', 'when', 'where', 'who', 'is', 'are',
                     'the', 'a', 'an', 'does', 'do', 'have', 'has', 's'}
        keywords = [word.lower() for word in query_normalized.split()
                   if word.lower() not in stop_words and len(word) > 2]

        # Normalize keywords to handle singular/plural variants
        # This helps "cars" match "car", "preferences" match "preference"
        normalized_keywords = []
        for kw in keywords:
            normalized_keywords.append(kw)  # Keep original
            # Add singular form if plural
            if kw.endswith('ies'):
                normalized_keywords.append(kw[:-3] + 'y')  # companies -> company
            elif kw.endswith('es') and not kw.endswith('sses'):
                normalized_keywords.append(kw[:-2])  # boxes -> box
            elif kw.endswith('s') and not kw.endswith('ss'):
                normalized_keywords.append(kw[:-1])  # cars -> car

        # Use normalized keywords for matching
        keywords = list(set(normalized_keywords))

        if verbose and keywords:
            print(f"      Keywords: {keywords[:5]}")

        # Detect relationship type from query intent
        # Maps query terms to graph relationship types
        relationship_mapping = {
            'prefer': 'PREFERS',
            'preference': 'PREFERS',
            'preferences': 'PREFERS',
            'favorite': 'FAVORITE',
            'favourites': 'FAVORITE',
            'favorites': 'FAVORITE',
            'own': 'OWNS',
            'owns': 'OWNS',
            'ownership': 'OWNS',
            'has': 'OWNS',
            'visit': 'VISITED',
            'visited': 'VISITED',
            'travel': 'PLANNING_TRIP_TO',
            'trip': 'PLANNING_TRIP_TO',
            'planning': 'PLANNING_TRIP_TO',
            'rent': 'RENTED/BOOKED',
            'rented': 'RENTED/BOOKED',
            'rental': 'RENTED/BOOKED',
            'book': 'RENTED/BOOKED',
            'booked': 'RENTED/BOOKED',
            'booking': 'RENTED/BOOKED',
            'bookings': 'RENTED/BOOKED',
            'reserve': 'RENTED/BOOKED',
            'reserved': 'RENTED/BOOKED',
            'reservation': 'RENTED/BOOKED',
            'reservations': 'RENTED/BOOKED',
            'attend': 'ATTENDING_EVENT',
            'attending': 'ATTENDING_EVENT',
            'event': 'ATTENDING_EVENT'
        }

        detected_rel_type = None
        for kw in keywords:
            if kw in relationship_mapping:
                detected_rel_type = relationship_mapping[kw]
                if verbose:
                    print(f"      Detected relationship type: {detected_rel_type}")
                break

        # Get messages from graph
        graph_messages = []
        seen_ids = set()

        # If we found users, get their relationships
        if users_found:
            for user_name in users_found:
                # If relationship type detected, filter by that type
                if detected_rel_type:
                    user_rels = self.knowledge_graph.get_user_relationships(user_name, detected_rel_type)
                else:
                    user_rels = self.knowledge_graph.get_user_relationships(user_name)

                for rel in user_rels:
                    msg_id = rel['message_id']
                    if msg_id in seen_ids:
                        continue

                    # Find the message
                    msg = next((m for m in self.bm25_search.messages
                              if m['id'] == msg_id), None)

                    if msg:
                        # If relationship type was detected, accept message without keyword check
                        # (e.g., "preferences" query finds PREFERS relationships even if message says "I prefer")
                        if detected_rel_type:
                            graph_messages.append(msg)
                            seen_ids.add(msg_id)
                        else:
                            # Otherwise, require keyword match
                            msg_text = msg['message'].lower()
                            if any(kw in msg_text for kw in keywords):
                                graph_messages.append(msg)
                                seen_ids.add(msg_id)

                        if len(graph_messages) >= top_k:
                            break

                if len(graph_messages) >= top_k:
                    break

        # If no user found or not enough results, search by keywords only
        if len(graph_messages) < top_k and keywords:
            for keyword in keywords:
                # Search entity index
                if keyword in self.knowledge_graph.entity_index:
                    users_with_entity = self.knowledge_graph.entity_index[keyword]

                    # FIX: If specific users were detected, only search within those users
                    # This prevents returning other users' messages when query mentions specific user
                    if users_found:
                        users_with_entity = [u for u in users_with_entity if u in users_found]

                    for user in users_with_entity:
                        user_rels = self.knowledge_graph.get_user_relationships(user)

                        # Check all relationships (not just first 5)
                        # We filter by keyword match anyway, so no risk of too many results
                        for rel in user_rels:
                            msg_id = rel['message_id']
                            if msg_id in seen_ids:
                                continue

                            msg = next((m for m in self.bm25_search.messages
                                      if m['id'] == msg_id), None)

                            if msg and keyword in msg['message'].lower():
                                graph_messages.append(msg)
                                seen_ids.add(msg_id)

                                if len(graph_messages) >= top_k:
                                    break

                        if len(graph_messages) >= top_k:
                            break

                if len(graph_messages) >= top_k:
                    break

        return graph_messages[:top_k]

    def _diversify_by_user(
        self,
        results: List[Tuple[Dict, float]],
        max_per_user: int = 2,
        top_k: int = 10
    ) -> List[Tuple[Dict, float]]:
        """
        Ensure no single user dominates results (diversity enforcement)

        Problem solved: RRF can cause user over-representation where one user's
        multiple messages crowd out correct answers from other users.

        Strategy (Round-Robin):
        1. Group messages by user
        2. Sort users by their best (earliest) RRF position
        3. Round 1: Take 1 message from each user (their best message)
        4. Round 2: Take 2nd message from each user (if they have one)
        5. Stop when we have top_k messages

        This ensures ALL users get at least 1 message before anyone gets 2.

        Example:
        - RRF positions 1-10: Lorenzo(3), Sophia(4), Amina(2), Fatima(1)
        - RRF positions 11-18: Vikram(2), Hans(2), Lily(2)

        Round-robin result:
        - Round 1: Lorenzo(1), Sophia(1), Amina(1), Fatima(1), Vikram(1), Hans(1), Lily(1) = 7 messages
        - Round 2: Lorenzo(1), Sophia(1), Amina(1) = 3 more messages
        - Total: All 7 users included ✅

        Args:
            results: List of (message, rrf_score) tuples from RRF fusion
            max_per_user: Maximum messages per user in final results (default 2)
            top_k: Number of final results to return (default 10)

        Returns:
            Diversified list of (message, rrf_score) tuples with max_per_user limit
        """
        # Track all messages by user
        user_messages = {}  # user -> [(msg, score, original_position), ...]

        for position, (msg, score) in enumerate(results):
            user = msg.get('user_name', 'Unknown')
            if user not in user_messages:
                user_messages[user] = []
            user_messages[user].append((msg, score, position))

        # Sort users by their best (earliest) RRF position
        sorted_users = sorted(
            user_messages.items(),
            key=lambda x: min(pos for _, _, pos in x[1])
        )

        # Round-robin selection
        diversified = []
        round_num = 0

        while len(diversified) < top_k and round_num < max_per_user:
            for user, messages in sorted_users:
                if round_num < len(messages):
                    msg, score, pos = messages[round_num]
                    diversified.append((msg, score, pos))

                    if len(diversified) >= top_k:
                        break

            round_num += 1

        # Sort by original RRF position to maintain relative ordering
        diversified.sort(key=lambda x: x[2])

        # Return top_k, without position info
        return [(msg, score) for msg, score, _ in diversified[:top_k]]

    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[Tuple[Dict, float]],
        bm25_results: List[Tuple[Dict, float]],
        graph_results: List[Dict],
        k: int = 60,
        weights: Dict[str, float] = None
    ) -> List[Tuple[Dict, float]]:
        """
        Reciprocal Rank Fusion algorithm

        Formula: score(msg) = Σ weight_i × 1/(k + rank_i)

        Args:
            semantic_results: List of (message, score) from semantic search
            bm25_results: List of (message, score) from BM25
            graph_results: List of messages from graph
            k: RRF constant (default 60)
            weights: Per-method weights

        Returns:
            List of (message, rrf_score) sorted by RRF score descending
        """
        if weights is None:
            weights = {'semantic': 1.0, 'bm25': 1.0, 'graph': 1.0}

        scores = defaultdict(float)
        messages = {}

        # Add semantic results
        for rank, (msg, _) in enumerate(semantic_results, start=1):
            msg_id = msg['id']
            rrf_score = weights['semantic'] * (1.0 / (k + rank))
            scores[msg_id] += rrf_score
            messages[msg_id] = msg

        # Add BM25 results
        for rank, (msg, _) in enumerate(bm25_results, start=1):
            msg_id = msg['id']
            rrf_score = weights['bm25'] * (1.0 / (k + rank))
            scores[msg_id] += rrf_score
            messages[msg_id] = msg

        # Add graph results
        for rank, msg in enumerate(graph_results, start=1):
            msg_id = msg['id']
            rrf_score = weights['graph'] * (1.0 / (k + rank))
            scores[msg_id] += rrf_score
            messages[msg_id] = msg

        # Sort by RRF score (descending)
        fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [(messages[msg_id], score) for msg_id, score in fused]

    def explain_results(
        self,
        query: str,
        top_k: int = 5
    ):
        """
        Search and explain where each result came from

        Args:
            query: Search query
            top_k: Number of results to explain
        """
        # Get detailed results
        semantic_results = self.embedding_index.search(query, top_k=20)
        bm25_results = self.bm25_search.search(query, top_k=20)
        graph_results = self._graph_search(query, top_k=10, verbose=False)

        # Build lookup tables
        semantic_ranks = {msg['id']: rank for rank, (msg, _) in enumerate(semantic_results, 1)}
        bm25_ranks = {msg['id']: rank for rank, (msg, _) in enumerate(bm25_results, 1)}
        graph_ranks = {msg['id']: rank for rank, msg in enumerate(graph_results, 1)}

        # Get hybrid results
        hybrid_results = self.search(query, top_k=top_k, verbose=False)

        print(f"\n{'='*70}")
        print(f"HYBRID SEARCH EXPLANATION")
        print(f"{'='*70}")
        print(f"\nQuery: '{query}'")
        print(f"\nTop {top_k} Results:\n")

        for i, (msg, rrf_score) in enumerate(hybrid_results, 1):
            msg_id = msg['id']

            # Get ranks from each method
            sem_rank = semantic_ranks.get(msg_id, None)
            bm25_rank = bm25_ranks.get(msg_id, None)
            graph_rank = graph_ranks.get(msg_id, None)

            print(f"{i}. [RRF={rrf_score:.4f}] {msg['user_name']}")
            print(f"   {msg['message'][:80]}...")
            print(f"   Sources: ", end="")

            sources = []
            if sem_rank:
                sources.append(f"Semantic(#{sem_rank})")
            if bm25_rank:
                sources.append(f"BM25(#{bm25_rank})")
            if graph_rank:
                sources.append(f"Graph(#{graph_rank})")

            print(" + ".join(sources) if sources else "None")
            print()


def main():
    """Demo hybrid retrieval"""
    print("="*70)
    print("HYBRID RETRIEVAL DEMO")
    print("="*70)

    # Initialize
    retriever = HybridRetriever()

    # Test query
    query = "How many cars does Vikram Desai have?"

    # Search with explanation
    retriever.explain_results(query, top_k=10)


if __name__ == "__main__":
    main()
