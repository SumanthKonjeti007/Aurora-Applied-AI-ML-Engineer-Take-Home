"""
Hybrid Extractor (The Orchestrator)

Combines Filter (rule-based) and Reasoner (LLM) for optimal quality and cost.
Triages messages: simple → Filter, complex → Reasoner
"""
from typing import List, Dict, Optional
from entity_extraction_gliner import GLiNEREntityExtractor
from llm_extractor import LLMSemanticExtractor


class HybridExtractor:
    """
    Hybrid extractor that combines rule-based (Filter) and LLM (Reasoner)

    Strategy:
    1. Run fast Filter on all messages
    2. If message is complex OR Filter found nothing → escalate to LLM Reasoner
    3. Return best results
    """

    def __init__(self, use_llm: bool = True, groq_api_key: Optional[str] = None):
        """
        Initialize hybrid extractor

        Args:
            use_llm: Enable LLM fallback for complex messages
            groq_api_key: Groq API key (optional, uses env var if not provided)
        """
        print("\n🔧 Initializing Hybrid Extractor...")

        # Initialize Filter (always available)
        print("  1/2 Loading Filter (GLiNER + spaCy)...")
        self.filter = GLiNEREntityExtractor()

        # Initialize Reasoner (optional, requires API key)
        self.reasoner = None
        self.use_llm = use_llm

        if use_llm:
            try:
                print("  2/2 Loading Reasoner (LLM via Groq)...")
                self.reasoner = LLMSemanticExtractor(api_key=groq_api_key)
            except ValueError as e:
                print(f"  ⚠️  LLM not available: {e}")
                print("  → Will use Filter only (no LLM fallback)")
                self.use_llm = False

        print("✅ Hybrid Extractor ready!")

    def is_complex_message(self, text: str) -> bool:
        """
        Detect if a message requires LLM understanding

        Complex triggers:
        - Questions with uncertain intent
        - Requests with multiple entities
        - Ambiguous phrasing

        Args:
            text: Message text

        Returns:
            True if message is complex
        """
        text_lower = text.lower()

        # Question patterns (often need semantic understanding)
        question_triggers = [
            "what are",
            "what is",
            "where can",
            "how many",
            "how much",
            "which",
            "could you",
            "can you",
            "is it possible",
            "would you",
            "i'd love",
            "i would like to know",
            "wondering",
        ]

        # Multiple entity indicators (need semantic division)
        multi_entity_triggers = [
            " for my ",
            " to the ",
            " at the ",
            " instead of ",
            " rather than ",
            " as well as ",
            " and also ",
        ]

        # Check triggers
        has_question = any(trigger in text_lower for trigger in question_triggers)
        has_multi_entity = any(trigger in text_lower for trigger in multi_entity_triggers)

        # Complex if has questions or multiple entities
        return has_question or has_multi_entity

    def extract_from_message(
        self,
        message: Dict,
        force_llm: bool = False,
        verbose: bool = False
    ) -> List[Dict]:
        """
        Extract triples using hybrid approach

        Workflow:
        1. Run Filter (fast, cheap)
        2. Triage: Is message complex OR Filter found nothing?
        3. If yes → Escalate to Reasoner (LLM)
        4. Return best results

        Args:
            message: Message dict
            force_llm: Force LLM usage (skip Filter)
            verbose: Print decision logic

        Returns:
            List of triples
        """
        text = message.get('message', '')
        user_name = message.get('user_name', 'Unknown')

        if verbose:
            print(f"\n{'='*60}")
            print(f"Hybrid extraction: {user_name}")
            print(f"Message: {text[:80]}...")

        # Skip if force_llm and no LLM available
        if force_llm and not self.use_llm:
            if verbose:
                print("  ⚠️  Force LLM requested but LLM not available")
            force_llm = False

        # Fast path: Run Filter first (unless forced to use LLM)
        filter_triples = []
        if not force_llm:
            filter_triples = self.filter.extract_from_message(message)

            if verbose:
                print(f"  Filter: {len(filter_triples)} triples")

        # Decision point: Use LLM?
        use_llm_for_this = False

        if self.use_llm:
            if force_llm:
                use_llm_for_this = True
                reason = "Forced LLM"
            elif len(filter_triples) == 0:
                use_llm_for_this = True
                reason = "Filter found nothing"
            elif self.is_complex_message(text):
                use_llm_for_this = True
                reason = "Complex message detected"

            if verbose and use_llm_for_this:
                print(f"  → Escalating to LLM ({reason})")

        # Slow path: Use LLM if needed
        if use_llm_for_this:
            llm_triples = self.reasoner.extract_triples_llm(message)

            if verbose:
                print(f"  LLM: {len(llm_triples)} triples")

            # Use LLM results if better
            if len(llm_triples) > 0:
                return llm_triples

        # Return Filter results (if LLM didn't produce better)
        return filter_triples

    def extract_from_messages_batch(
        self,
        messages: List[Dict],
        show_progress: bool = True,
        verbose: bool = False
    ) -> List[Dict]:
        """
        Extract triples from multiple messages using hybrid approach

        Args:
            messages: List of message dicts
            show_progress: Show progress
            verbose: Print decisions for each message

        Returns:
            List of all extracted triples
        """
        all_triples = []

        print(f"\n🔀 Hybrid extraction from {len(messages)} messages...")

        filter_count = 0
        llm_count = 0

        for i, message in enumerate(messages, 1):
            if show_progress and i % 50 == 0:
                print(f"   Processed {i}/{len(messages)} (Filter: {filter_count}, LLM: {llm_count})")

            # Extract with triage
            filter_result = self.filter.extract_from_message(message)

            # Triage
            use_llm = False
            if self.use_llm:
                if len(filter_result) == 0:
                    use_llm = True
                elif self.is_complex_message(message.get('message', '')):
                    use_llm = True

            if use_llm:
                triples = self.reasoner.extract_triples_llm(message)
                llm_count += 1

                # Rate limiting for Groq (30 req/min)
                if llm_count < len(messages):
                    import time
                    time.sleep(2.1)
            else:
                triples = filter_result
                filter_count += 1

            all_triples.extend(triples)

        print(f"\n✅ Extracted {len(all_triples)} triples")
        print(f"   Filter: {filter_count} messages ({filter_count/len(messages)*100:.1f}%)")
        print(f"   LLM: {llm_count} messages ({llm_count/len(messages)*100:.1f}%)")
        print(f"   Average: {len(all_triples)/len(messages):.2f} triples per message")

        return all_triples


def test_hybrid_extractor():
    """Test hybrid extractor decision logic"""
    print("="*80)
    print("HYBRID EXTRACTOR TEST")
    print("="*80)

    # Test messages of varying complexity
    test_messages = [
        {
            "id": "1",
            "user_name": "Hans Müller",
            "message": "I need four front-row seats for the game.",
            "expected_method": "Filter",
            "reason": "Simple booking"
        },
        {
            "id": "2",
            "user_name": "Vikram Desai",
            "message": "Can I get a Bentley for my Paris trip?",
            "expected_method": "LLM",
            "reason": "Complex (question + multiple entities)"
        },
        {
            "id": "3",
            "user_name": "Sophia Al-Farsi",
            "message": "What are the best restaurants in Paris?",
            "expected_method": "LLM",
            "reason": "Complex (question)"
        },
        {
            "id": "4",
            "user_name": "Vikram Desai",
            "message": "Change my car service to the BMW instead of the Mercedes.",
            "expected_method": "LLM",
            "reason": "Complex (multiple entities)"
        },
        {
            "id": "5",
            "user_name": "Layla Kawaguchi",
            "message": "I prefer aisle seats.",
            "expected_method": "Filter",
            "reason": "Simple preference"
        },
    ]

    # Initialize
    print("\nInitializing hybrid extractor...")
    extractor = HybridExtractor(use_llm=True)

    print("\n" + "="*80)
    print("TESTING TRIAGE LOGIC")
    print("="*80)

    for msg in test_messages:
        print(f"\n{'='*80}")
        print(f"Message: \"{msg['message']}\"")
        print(f"Expected: {msg['expected_method']} ({msg['reason']})")

        # Check complexity
        is_complex = extractor.is_complex_message(msg['message'])
        print(f"Detected: {'Complex' if is_complex else 'Simple'}")

        # Extract
        triples = extractor.extract_from_message(msg, verbose=True)

        print(f"\nResult: {len(triples)} triples")
        for triple in triples:
            print(f"  • ({triple['subject']}, {triple['relationship']}, {triple['object']})")

    print("\n" + "="*80)
    print("✅ Hybrid extractor test complete")
    print("="*80)


if __name__ == "__main__":
    test_hybrid_extractor()
