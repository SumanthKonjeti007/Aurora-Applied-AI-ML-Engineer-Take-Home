"""
Test script to verify Blocker #3 (LLM Decomposer) fix

Tests the previously failing query:
"Which clients have both expressed a preference and complained about a related service charge?"

Expected behavior BEFORE fix:
- Incorrectly decomposed into 10 user-specific queries
- Only 1 message per user retrieved
- Insufficient context to find BOTH conditions

Expected behavior AFTER fix:
- NOT decomposed (single query)
- Top-50 messages retrieved across all users
- Enough context to verify BOTH conditions

Usage:
    export GROQ_API_KEY='your-api-key-here'
    python scripts/test_decomposer_fix.py
"""
import os
from src.qa_system import QASystem

def test_blocker3_fix():
    """Test the decomposer fix with the failing query"""

    print("="*80)
    print("BLOCKER #3 FIX TEST")
    print("="*80)
    print("\nQuery: 'Which clients have both expressed a preference and complained")
    print("        about a related service charge?'")
    print("\nExpected:")
    print("  ✅ Should NOT decompose (single aggregation query)")
    print("  ✅ Should retrieve top-k messages across ALL users")
    print("  ✅ Should provide enough context to LLM")
    print("\n" + "="*80)

    # Initialize QA system
    print("\nInitializing QA System...")
    qa = QASystem()
    print("✅ System ready\n")

    # Test query
    query = "Which clients have both expressed a preference and complained about a related service charge?"

    print("="*80)
    print("TESTING QUERY")
    print("="*80)

    result = qa.answer(query, verbose=True)

    print("\n" + "="*80)
    print("FINAL ANSWER")
    print("="*80)
    print(result['answer'])
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_blocker3_fix()
