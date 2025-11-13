"""
Comprehensive test to verify decomposer fix doesn't break existing functionality

Tests 3 query types:
1. Comparison query (SHOULD decompose) - Layla vs Lily
2. Aggregation with BOTH (SHOULD NOT decompose) - Fixed query
3. Simple aggregation (SHOULD NOT decompose) - Which clients have billing issues

Usage:
    export GROQ_API_KEY='your-api-key-here'
    python scripts/test_comprehensive_decomposer.py
"""
import os
from src.qa_system import QASystem

def test_query(qa, query_desc, query, expected_decompose):
    """Test a single query"""
    print("\n" + "="*80)
    print(f"TEST: {query_desc}")
    print("="*80)
    print(f"Query: {query}")
    print(f"Expected: {'DECOMPOSE' if expected_decompose else 'NO DECOMPOSITION'}")
    print("-"*80)

    result = qa.answer(query, verbose=True)

    print("\n" + "-"*80)
    print("ANSWER:")
    print(result['answer'][:300] + "..." if len(result['answer']) > 300 else result['answer'])

def main():
    print("="*80)
    print("COMPREHENSIVE DECOMPOSER TEST")
    print("="*80)
    print("\nVerifying fix doesn't break existing functionality...")

    # Initialize QA system
    print("\nInitializing QA System...")
    qa = QASystem()
    print("✅ System ready\n")

    # Test 1: Comparison query (SHOULD decompose)
    test_query(
        qa,
        "Comparison Query (SHOULD decompose)",
        "What are the conflicting flight seating preferences of Layla Kawaguchi and Lily O'Sullivan?",
        expected_decompose=True
    )

    # Test 2: Aggregation with BOTH (SHOULD NOT decompose) - The fix
    test_query(
        qa,
        "Aggregation with BOTH (SHOULD NOT decompose)",
        "Which clients have both expressed a preference and complained about a related service charge?",
        expected_decompose=False
    )

    # Test 3: Simple aggregation (SHOULD NOT decompose)
    test_query(
        qa,
        "Simple Aggregation (SHOULD NOT decompose)",
        "Which clients have had a billing issue or reported an unrecognized charge?",
        expected_decompose=False
    )

    print("\n" + "="*80)
    print("ALL TESTS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
