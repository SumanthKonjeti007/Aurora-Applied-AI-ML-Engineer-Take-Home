#!/usr/bin/env python3
"""
Comprehensive Test Suite - 8 Diverse Queries
Tests all aspects of the QA system with optimizations
"""
import os
os.environ['MISTRAL_API_KEY'] = 'tCQvPLqFgob8FOyqBcLye3duFWR3Qa2m'

from src.qa_system import QASystem
import time

# Test queries
test_queries = [
    "What is Armand Dupont's preference for in-room appliances?",
    "Compare Vikram Desai's and Hans Müller's preferences for Mercedes car service",
    "What plans did Armand Dupont have for the last weekend of December 2024?",
    "Which clients requested a personal shopper in Milan?",
    "What is the most requested high-end event: Wimbledon, the Monaco Grand Prix, or the Cannes Film Festival?",
    "Which clients requested the same luxury hotel chain?",
    "How many clients have complained about a billing issue or an unrecognized charge?",
    "How many cars does Vikram Desai have?"
]

def run_test_suite():
    print("=" * 100)
    print("COMPREHENSIVE TEST SUITE - 8 QUERIES")
    print("=" * 100)
    print(f"\nInitializing QA System with Mistral AI...")

    system = QASystem()

    print(f"✅ System ready!\n")

    results = []

    for i, query in enumerate(test_queries, 1):
        print("\n" + "=" * 100)
        print(f"TEST {i}/8: {query}")
        print("=" * 100)

        try:
            start_time = time.time()
            result = system.answer(query, verbose=False)
            elapsed = time.time() - start_time

            print(f"\n📍 ROUTE: {result['route']}")
            if 'type' in result:
                print(f"📋 TYPE: {result['type']}")

            print(f"\n💬 ANSWER:")
            print(result['answer'])

            if 'tokens' in result and result['tokens']:
                print(f"\n📊 TOKENS: {result['tokens'].get('total', 'N/A')}")

            print(f"⏱️  TIME: {elapsed:.2f}s")

            results.append({
                'query': query,
                'route': result['route'],
                'answer': result['answer'],
                'tokens': result.get('tokens', {}),
                'time': elapsed,
                'success': True
            })

            print(f"\n✅ Test {i}/8 PASSED")

        except Exception as e:
            print(f"\n❌ Test {i}/8 FAILED")
            print(f"Error: {str(e)}")
            results.append({
                'query': query,
                'success': False,
                'error': str(e)
            })

        # Small delay between queries
        if i < len(test_queries):
            time.sleep(1)

    # Summary
    print("\n" + "=" * 100)
    print("TEST SUITE SUMMARY")
    print("=" * 100)

    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed

    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")

    if passed > 0:
        avg_tokens = sum(r.get('tokens', {}).get('total', 0) for r in results if r['success']) / passed
        avg_time = sum(r.get('time', 0) for r in results if r['success']) / passed
        print(f"\nAverage Tokens per Query: {avg_tokens:.0f}")
        print(f"Average Time per Query: {avg_time:.2f}s")

    # Breakdown by route
    routes = {}
    for r in results:
        if r['success']:
            route = r.get('route', 'Unknown')
            routes[route] = routes.get(route, 0) + 1

    print(f"\nQueries by Route:")
    for route, count in routes.items():
        print(f"  {route}: {count}")

    return results

if __name__ == "__main__":
    results = run_test_suite()
