"""
Hybrid Retrieval Test Suite
Compare semantic-only vs hybrid retrieval performance
Target: 70-80% pass rate (vs 25% semantic-only)
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hybrid_retriever import HybridRetriever
from collections import defaultdict


# Same test cases as embeddings test
TEST_CASES = [
    # ========== ASSIGNMENT EXAMPLES (CRITICAL) ==========
    {
        "id": "Q1",
        "query": "When is Layla planning her trip to London?",
        "expected_user": "Layla Kawaguchi",
        "expected_keywords": ["london", "trip", "planning", "claridge"],
        "min_relevant_in_top10": 3,
        "category": "assignment_example"
    },
    {
        "id": "Q2",
        "query": "How many cars does Vikram Desai have?",
        "expected_user": "Vikram Desai",
        "expected_keywords": ["car", "bmw", "mercedes", "tesla", "vehicle"],
        "min_relevant_in_top10": 3,
        "category": "assignment_example"
    },
    {
        "id": "Q3",
        "query": "What are Amira's favorite restaurants?",
        "expected_user": "Amina Van Den Berg",  # Note: Could be Amira or Amina
        "expected_keywords": ["restaurant", "nobu", "dining", "table"],
        "min_relevant_in_top10": 2,
        "category": "assignment_example"
    },

    # ========== TEMPORAL QUERIES ==========
    {
        "id": "Q4",
        "query": "Vikram trip to Tokyo",
        "expected_user": "Vikram Desai",
        "expected_keywords": ["tokyo", "trip", "japan"],
        "min_relevant_in_top10": 2,
        "category": "temporal"
    },
    {
        "id": "Q5",
        "query": "hotel booking in Paris",
        "expected_keywords": ["paris", "hotel", "suite", "booking"],
        "min_relevant_in_top10": 5,
        "category": "location"
    },

    # ========== PREFERENCE QUERIES ==========
    {
        "id": "Q6",
        "query": "Layla flight seat preferences",
        "expected_user": "Layla Kawaguchi",
        "expected_keywords": ["seat", "aisle", "flight", "prefer"],
        "min_relevant_in_top10": 2,
        "category": "preference"
    },
    {
        "id": "Q7",
        "query": "hotel room preferences quiet",
        "expected_keywords": ["hotel", "room", "quiet", "prefer"],
        "min_relevant_in_top10": 3,
        "category": "preference"
    },

    # ========== SERVICE REQUESTS ==========
    {
        "id": "Q8",
        "query": "car service request",
        "expected_keywords": ["car", "service", "driver", "chauffeur"],
        "min_relevant_in_top10": 5,
        "category": "service"
    },
    {
        "id": "Q9",
        "query": "villa booking Santorini",
        "expected_keywords": ["villa", "santorini", "booking"],
        "min_relevant_in_top10": 2,
        "category": "accommodation"
    },

    # ========== COMPLAINT/ISSUE QUERIES ==========
    {
        "id": "Q10",
        "query": "Sophia complaint about charges",
        "expected_user": "Sophia Al-Farsi",
        "expected_keywords": ["charge", "overcharge", "bill", "complaint"],
        "min_relevant_in_top10": 3,
        "category": "complaint"
    },

    # ========== CONTACT INFO ==========
    {
        "id": "Q11",
        "query": "phone number update",
        "expected_keywords": ["phone", "number", "555", "contact"],
        "min_relevant_in_top10": 3,
        "category": "contact"
    },

    # ========== EVENT ATTENDANCE ==========
    {
        "id": "Q12",
        "query": "opera tickets Milan",
        "expected_keywords": ["opera", "milan", "tickets"],
        "min_relevant_in_top10": 2,
        "category": "event"
    },
]


def evaluate_result(msg, test_case):
    """
    Evaluate if a message is relevant to the test case

    Returns:
        relevance_score: 0.0 (not relevant) to 1.0 (highly relevant)
    """
    score = 0.0
    text = msg['message'].lower()
    user = msg['user_name']

    # Check user match (if specified)
    if test_case.get('expected_user'):
        if user == test_case['expected_user']:
            score += 0.4  # User match is strong signal

    # Check keyword matches
    keyword_matches = 0
    for keyword in test_case['expected_keywords']:
        if keyword in text:
            keyword_matches += 1

    if keyword_matches > 0:
        # Normalize by number of keywords
        keyword_score = min(keyword_matches / len(test_case['expected_keywords']), 1.0)
        score += keyword_score * 0.6

    return score


def run_test_case(retriever, test_case):
    """
    Run a single test case and evaluate results

    Returns:
        dict with test results
    """
    query = test_case['query']
    results = retriever.search(query, top_k=10, verbose=False)

    # Evaluate each result
    relevance_scores = []
    relevant_count = 0
    user_match = False

    for msg, rrf_score in results:
        relevance = evaluate_result(msg, test_case)
        relevance_scores.append(relevance)

        if relevance >= 0.5:  # Threshold for "relevant"
            relevant_count += 1

        # Check user match in top results
        if test_case.get('expected_user') and msg['user_name'] == test_case['expected_user']:
            user_match = True

    # Calculate metrics
    passed = relevant_count >= test_case['min_relevant_in_top10']

    # Recall@10: How many relevant items found in top 10?
    recall_at_10 = relevant_count / 10.0

    # Average relevance score
    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0

    return {
        'test_id': test_case['id'],
        'query': query,
        'category': test_case['category'],
        'passed': passed,
        'relevant_count': relevant_count,
        'min_required': test_case['min_relevant_in_top10'],
        'recall_at_10': recall_at_10,
        'avg_relevance': avg_relevance,
        'user_match': user_match,
        'top_results': [(msg['user_name'], msg['message'][:80], score)
                       for (msg, _), score in zip(results[:3], relevance_scores[:3])]
    }


def print_test_results(result):
    """Pretty print test results"""
    status = "✅ PASS" if result['passed'] else "❌ FAIL"

    print(f"\n{status} [{result['test_id']}] {result['query']}")
    print(f"  Category: {result['category']}")
    print(f"  Relevant: {result['relevant_count']}/{result['min_required']} required")
    print(f"  Recall@10: {result['recall_at_10']:.2f}")
    print(f"  Avg Relevance: {result['avg_relevance']:.2f}")

    if result.get('user_match') is not None:
        match_str = "✓" if result['user_match'] else "✗"
        print(f"  User Match: {match_str}")

    print(f"\n  Top 3 results:")
    for i, (user, msg, score) in enumerate(result['top_results'], 1):
        print(f"    {i}. [{score:.2f}] {user}: {msg}...")


def calculate_overall_metrics(results):
    """Calculate aggregate metrics across all tests"""
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['passed'])

    # Overall pass rate
    pass_rate = (passed_tests / total_tests) * 100

    # Average recall@10
    avg_recall = sum(r['recall_at_10'] for r in results) / total_tests

    # Average relevance score
    avg_relevance = sum(r['avg_relevance'] for r in results) / total_tests

    # Pass rate by category
    by_category = defaultdict(lambda: {'total': 0, 'passed': 0})
    for r in results:
        cat = r['category']
        by_category[cat]['total'] += 1
        if r['passed']:
            by_category[cat]['passed'] += 1

    category_stats = {
        cat: (stats['passed'] / stats['total']) * 100
        for cat, stats in by_category.items()
    }

    # Check if assignment examples passed
    assignment_results = [r for r in results if r['category'] == 'assignment_example']
    assignment_pass_rate = (sum(1 for r in assignment_results if r['passed']) / len(assignment_results)) * 100

    return {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'pass_rate': pass_rate,
        'avg_recall_at_10': avg_recall,
        'avg_relevance': avg_relevance,
        'category_stats': category_stats,
        'assignment_pass_rate': assignment_pass_rate
    }


def main():
    """Run comprehensive hybrid retrieval tests"""
    print("="*70)
    print("HYBRID RETRIEVAL TEST SUITE")
    print("="*70)

    # Load hybrid retriever
    print("\n📂 Loading hybrid retriever...")
    retriever = HybridRetriever()

    # Run all test cases
    print("\n🧪 Running test cases...")
    print("="*70)

    results = []
    for test_case in TEST_CASES:
        result = run_test_case(retriever, test_case)
        results.append(result)
        print_test_results(result)

    # Calculate overall metrics
    print("\n" + "="*70)
    print("OVERALL METRICS")
    print("="*70)

    metrics = calculate_overall_metrics(results)

    print(f"\nTotal Tests: {metrics['total_tests']}")
    print(f"Passed: {metrics['passed_tests']}/{metrics['total_tests']} ({metrics['pass_rate']:.1f}%)")
    print(f"\nAverage Recall@10: {metrics['avg_recall_at_10']:.2f}")
    print(f"Average Relevance Score: {metrics['avg_relevance']:.2f}")

    print(f"\n📊 Pass Rate by Category:")
    for category, rate in sorted(metrics['category_stats'].items()):
        print(f"  {category:25s}: {rate:5.1f}%")

    print(f"\n🎯 Assignment Examples: {metrics['assignment_pass_rate']:.1f}% pass rate")

    # Decision point
    print("\n" + "="*70)
    print("DECISION")
    print("="*70)

    threshold = 70.0

    if metrics['pass_rate'] >= threshold:
        print(f"\n✅ SUCCESS - Overall pass rate {metrics['pass_rate']:.1f}% >= {threshold}%")
        print("\n✓ Hybrid retrieval is WORKING")
        print("✓ Target 70-80% achieved!")
        print("\nNext step: Integrate LLM for answer generation")
    else:
        print(f"\n⚠️  MARGINAL - Pass rate {metrics['pass_rate']:.1f}% < {threshold}%")
        print("\nRecommendations:")
        print("  1. Review failed test cases")
        print("  2. Adjust RRF weights")
        print("  3. Improve graph search")

    # Special check for assignment examples
    if metrics['assignment_pass_rate'] < 100:
        print(f"\n⚠️  WARNING: Assignment examples not 100% ({metrics['assignment_pass_rate']:.1f}%)")
        print("   Review failed examples - these are critical for evaluation")
    else:
        print(f"\n✅ EXCELLENT: All assignment examples passed!")

    print("\n" + "="*70)

    return metrics


if __name__ == "__main__":
    main()
