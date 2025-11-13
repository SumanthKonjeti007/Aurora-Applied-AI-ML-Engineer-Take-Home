"""
Result Composer Module

Composes final context from multiple sub-query results.

Architecture:
- Interleaves results from multiple sub-queries (for balanced comparison context)
- Deduplicates messages by ID
- Formats context for LLM consumption

Use Cases:
- Single query: Return results as-is
- Multi-entity comparison: Interleave for balanced representation
- Aggregation: Merge and deduplicate
"""
from typing import List, Tuple, Dict


class ResultComposer:
    """
    Compose final context from sub-query results

    Strategies:
    - INTERLEAVE: Alternate between sub-query results (for comparisons)
    - MERGE: Combine and sort by score (for aggregations)
    - PASSTHROUGH: Single query, return as-is
    """

    def compose(
        self,
        results_list: List[List[Tuple[Dict, float]]],
        strategy: str = "auto",
        max_results: int = 10,
        verbose: bool = False
    ) -> List[Tuple[Dict, float]]:
        """
        Compose results from multiple sub-queries

        Args:
            results_list: List of result lists from each sub-query
                          Each result list contains (message, score) tuples
            strategy: Composition strategy ('auto', 'interleave', 'merge', 'passthrough')
            max_results: Maximum number of results to return
            verbose: Print composition details

        Returns:
            List of (message, score) tuples for LLM context
        """
        if verbose:
            print(f"\n{'='*80}")
            print("RESULT COMPOSER")
            print(f"{'='*80}")
            print(f"Input: {len(results_list)} sub-query result set(s)")
            for i, results in enumerate(results_list, 1):
                print(f"  Sub-query {i}: {len(results)} results")

        # Auto-select strategy
        if strategy == "auto":
            if len(results_list) == 1:
                strategy = "passthrough"
            elif len(results_list) >= 2:
                strategy = "interleave"
            else:
                strategy = "merge"

        if verbose:
            print(f"Strategy: {strategy.upper()}")

        # Apply strategy
        if strategy == "passthrough":
            composed = self._passthrough(results_list[0], max_results)
        elif strategy == "interleave":
            composed = self._interleave(results_list, max_results)
        elif strategy == "merge":
            composed = self._merge(results_list, max_results)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        if verbose:
            print(f"Output: {len(composed)} results")

            # Show entity distribution
            entity_counts = {}
            for msg, _ in composed:
                user = msg['user_name']
                entity_counts[user] = entity_counts.get(user, 0) + 1

            print(f"\nEntity distribution:")
            for user, count in sorted(entity_counts.items(), key=lambda x: -x[1])[:5]:
                print(f"  {user}: {count} messages")

            print(f"{'='*80}\n")

        return composed

    def _passthrough(
        self,
        results: List[Tuple[Dict, float]],
        max_results: int
    ) -> List[Tuple[Dict, float]]:
        """
        Passthrough strategy: Return results as-is

        Use for: Single sub-query (no composition needed)
        """
        return results[:max_results]

    def _interleave(
        self,
        results_list: List[List[Tuple[Dict, float]]],
        max_results: int
    ) -> List[Tuple[Dict, float]]:
        """
        Interleave strategy: Round-robin from each sub-query

        Use for: Comparison queries (ensures balanced entity representation)

        Example:
            results_list = [
                [msg1_thiago, msg2_thiago, msg3_thiago],
                [msg1_hans, msg2_hans, msg3_hans]
            ]

            Output: [msg1_thiago, msg1_hans, msg2_thiago, msg2_hans, ...]
        """
        composed = []
        seen_ids = set()

        # Find max length
        max_len = max(len(results) for results in results_list) if results_list else 0

        # Interleave round-robin
        for i in range(max_len):
            for results in results_list:
                if i < len(results):
                    msg, score = results[i]

                    # Deduplicate by message ID
                    if msg['id'] not in seen_ids:
                        composed.append((msg, score))
                        seen_ids.add(msg['id'])

                        if len(composed) >= max_results:
                            return composed

        return composed

    def _merge(
        self,
        results_list: List[List[Tuple[Dict, float]]],
        max_results: int
    ) -> List[Tuple[Dict, float]]:
        """
        Merge strategy: Combine all results and sort by score

        Use for: Aggregation queries (prioritize highest scored results)
        """
        # Flatten all results
        all_results = []
        seen_ids = set()

        for results in results_list:
            for msg, score in results:
                # Deduplicate
                if msg['id'] not in seen_ids:
                    all_results.append((msg, score))
                    seen_ids.add(msg['id'])

        # Sort by score (descending)
        all_results.sort(key=lambda x: x[1], reverse=True)

        return all_results[:max_results]

    def format_context_for_llm(
        self,
        composed_results: List[Tuple[Dict, float]],
        include_scores: bool = False
    ) -> str:
        """
        Format composed results into text context for LLM

        Args:
            composed_results: List of (message, score) tuples
            include_scores: Whether to include relevance scores in context

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, (msg, score) in enumerate(composed_results, 1):
            user = msg['user_name']
            message = msg['message']

            if include_scores:
                context_parts.append(
                    f"[{i}] {user} (relevance: {score:.3f}):\n{message}"
                )
            else:
                context_parts.append(
                    f"[{i}] {user}:\n{message}"
                )

        return "\n\n".join(context_parts)


def test_result_composer():
    """Test ResultComposer with sample data"""
    print("="*80)
    print("RESULT COMPOSER TEST")
    print("="*80)

    composer = ResultComposer()

    # Create sample results
    thiago_results = [
        ({'id': 't1', 'user_name': 'Thiago Monteiro', 'message': 'I love Italian cuisine'}, 0.95),
        ({'id': 't2', 'user_name': 'Thiago Monteiro', 'message': 'Book a table at a Michelin restaurant'}, 0.90),
        ({'id': 't3', 'user_name': 'Thiago Monteiro', 'message': 'I prefer seafood for dinner'}, 0.85),
    ]

    hans_results = [
        ({'id': 'h1', 'user_name': 'Hans Müller', 'message': 'I prefer Italian cuisine when dining'}, 0.92),
        ({'id': 'h2', 'user_name': 'Hans Müller', 'message': 'Best private dining experiences?'}, 0.88),
        ({'id': 'h3', 'user_name': 'Hans Müller', 'message': 'We have dietary restrictions - gluten free'}, 0.82),
    ]

    # Test 1: Single query (passthrough)
    print("\n" + "="*80)
    print("TEST 1: PASSTHROUGH (Single Query)")
    print("="*80)
    composed = composer.compose([thiago_results], verbose=True)
    print(f"Result: {len(composed)} messages (expected 3)")

    # Test 2: Comparison (interleave)
    print("\n" + "="*80)
    print("TEST 2: INTERLEAVE (Comparison Query)")
    print("="*80)
    composed = composer.compose([thiago_results, hans_results], verbose=True)
    print(f"Result: {len(composed)} messages")
    print("Expected order: Thiago, Hans, Thiago, Hans, ...")
    print("\nActual order:")
    for i, (msg, score) in enumerate(composed, 1):
        print(f"  {i}. {msg['user_name']}: {msg['message'][:50]}...")

    # Test 3: Format for LLM
    print("\n" + "="*80)
    print("TEST 3: FORMAT FOR LLM")
    print("="*80)
    context = composer.format_context_for_llm(composed[:4], include_scores=False)
    print(context)

    print("\n" + "="*80)


if __name__ == "__main__":
    test_result_composer()
