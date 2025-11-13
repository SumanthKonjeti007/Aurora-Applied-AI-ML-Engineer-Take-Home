"""
Knowledge Graph Testing Script
Tests graph quality, queries, and ability to support example questions
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pickle
from src.knowledge_graph import KnowledgeGraph


def test_graph_statistics():
    """Test basic graph statistics"""
    print("="*60)
    print("TEST 1: Graph Statistics")
    print("="*60)

    kg = KnowledgeGraph()
    kg.load('data/knowledge_graph.pkl')

    stats = kg.get_statistics()

    print(f"\n✓ Nodes: {stats['total_nodes']}")
    print(f"✓ Edges: {stats['total_edges']}")
    print(f"✓ Users: {stats['total_users']}")

    print("\n✓ Relationship distribution:")
    for rel, count in stats['relationship_counts'].items():
        print(f"  {rel:25s}: {count:4d}")

    assert stats['total_nodes'] > 0, "Graph has no nodes"
    assert stats['total_edges'] > 0, "Graph has no edges"
    print("\n✅ PASSED")


def test_user_queries():
    """Test user-specific queries"""
    print("\n" + "="*60)
    print("TEST 2: User Queries")
    print("="*60)

    kg = KnowledgeGraph()
    kg.load('data/knowledge_graph.pkl')

    # Test Vikram
    print("\nQuery: Vikram Desai's relationships")
    vikram_all = kg.get_user_relationships("Vikram Desai")
    vikram_owns = kg.get_user_relationships("Vikram Desai", "OWNS")

    print(f"✓ Total relationships: {len(vikram_all)}")
    print(f"✓ OWNS relationships: {len(vikram_owns)}")
    print(f"  Sample: {vikram_owns[0]['object']}")

    assert len(vikram_all) > 0, "Vikram has no relationships"
    assert len(vikram_owns) > 0, "Vikram has no OWNS relationships"
    print("✅ PASSED")


def test_entity_search():
    """Test entity-based search"""
    print("\n" + "="*60)
    print("TEST 3: Entity Search")
    print("="*60)

    kg = KnowledgeGraph()
    kg.load('data/knowledge_graph.pkl')

    # Test London
    print("\nQuery: Who mentions London?")
    london_users = kg.find_by_entity("London")
    print(f"✓ Found {len(london_users)} users")
    print(f"  Users: {london_users[:5]}")

    london_context = kg.get_entity_context("London")
    print(f"✓ Found {len(london_context)} London-related triples")

    assert len(london_users) > 0, "No users mention London"
    assert len(london_context) > 0, "No London context found"
    print("✅ PASSED")


def test_example_questions():
    """Test if graph can support answering example questions"""
    print("\n" + "="*60)
    print("TEST 4: Example Question Support")
    print("="*60)

    kg = KnowledgeGraph()
    kg.load('data/knowledge_graph.pkl')

    # Question 1: When is Layla planning her trip to London?
    print("\nQ1: When is Layla planning her trip to London?")
    layla_triples = kg.get_user_relationships("Layla Kawaguchi")
    london_triples = [t for t in layla_triples if 'london' in t['object'].lower()]
    print(f"✓ Found {len(london_triples)} London-related triples for Layla")
    for t in london_triples[:3]:
        print(f"  • {t['relationship']}: {t['object']}")

    # Question 2: How many cars does Vikram Desai have?
    print("\nQ2: How many cars does Vikram Desai have?")
    vikram_triples = kg.get_user_relationships("Vikram Desai")
    car_triples = [t for t in vikram_triples if 'car' in t['object'].lower()]
    print(f"✓ Found {len(car_triples)} car-related triples for Vikram")
    for t in car_triples[:3]:
        print(f"  • {t['relationship']}: {t['object']}")

    # Question 3: What are Amira's favorite restaurants?
    print("\nQ3: What are Amira's favorite restaurants?")
    amira_triples = kg.get_user_relationships("Amina Van Den Berg")
    restaurant_triples = [t for t in amira_triples
                         if 'restaurant' in t['object'].lower()
                         or t['relationship'] in ['FAVORITE', 'DINING_AT']]
    print(f"✓ Found {len(restaurant_triples)} restaurant-related triples for Amina")
    for t in restaurant_triples[:3]:
        print(f"  • {t['relationship']}: {t['object']}")

    print("\n✓ Graph provides CONTEXT (not full answers)")
    print("✓ Next step: Use graph to filter → retrieve messages → LLM extracts answer")
    print("✅ PASSED")


def test_graph_noise_filter():
    """Test that noise filtering is working"""
    print("\n" + "="*60)
    print("TEST 5: Noise Filtering")
    print("="*60)

    # Load raw triples
    with open('data/triples.json') as f:
        raw_triples = json.load(f)

    # Load graph triples
    kg = KnowledgeGraph()
    kg.load('data/knowledge_graph.pkl')

    # Count edges
    graph_edges = kg.graph.number_of_edges()

    print(f"\n✓ Raw triples: {len(raw_triples)}")
    print(f"✓ Graph edges: {graph_edges}")
    print(f"✓ Filtered out: {len(raw_triples) - graph_edges} ({(len(raw_triples) - graph_edges)/len(raw_triples)*100:.1f}%)")

    # Check for noise objects
    noise_count = 0
    for u, v, data in kg.graph.edges(data=True):
        if v.lower() in {'to', 'for', 'in', 'on', 'at', 'of', 'during', 'with'}:
            noise_count += 1

    print(f"✓ Noise objects in graph: {noise_count}")
    assert noise_count == 0, f"Graph still contains {noise_count} noise objects"
    print("✅ PASSED - No noise prepositions in graph")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("KNOWLEDGE GRAPH TEST SUITE")
    print("="*60)

    try:
        test_graph_statistics()
        test_user_queries()
        test_entity_search()
        test_example_questions()
        test_graph_noise_filter()

        print("\n" + "="*60)
        print("ALL TESTS PASSED ✅")
        print("="*60)
        print("\nKnowledge graph is ready for hybrid retrieval!")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    main()
