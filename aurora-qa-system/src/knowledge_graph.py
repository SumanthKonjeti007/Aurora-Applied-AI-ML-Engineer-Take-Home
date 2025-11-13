"""
Knowledge Graph Module
Build and query knowledge graph from extracted triples
"""
import json
import pickle
import networkx as nx
from typing import List, Dict, Optional, Set
from collections import defaultdict


class KnowledgeGraph:
    """Knowledge graph for member relationships and entities"""

    def __init__(self):
        """Initialize empty knowledge graph"""
        self.graph = nx.MultiDiGraph()  # Directed graph with multiple edges
        self.user_index = defaultdict(list)  # user_name -> list of triples
        self.relationship_index = defaultdict(list)  # relationship -> list of triples
        self.entity_index = defaultdict(set)  # entity -> set of users who mention it

    def _extract_keywords(self, text: str) -> Set[str]:
        """
        Extract meaningful keywords from object phrase for entity indexing

        Args:
            text: Object phrase to tokenize

        Returns:
            Set of lowercase keywords (stopwords removed)
        """
        # Stopwords to filter out
        stopwords = {
            'a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'from', 'by', 'as', 'is', 'was', 'are', 'were', 'been', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'and', 'or',
            'but', 'if', 'then', 'so', 'than', 'such', 'no', 'not', 'only',
            'own', 'same', 'too', 'very', 'just', 'now'
        }

        # Tokenize and clean
        tokens = text.lower().split()

        # Remove punctuation and filter
        keywords = set()
        for token in tokens:
            # Strip punctuation
            cleaned = token.strip('.,!?;:()[]{}"\'-')

            # Keep if:
            # - Not a stopword
            # - Length >= 2
            # - Contains at least one letter
            if (cleaned not in stopwords and
                len(cleaned) >= 2 and
                any(c.isalpha() for c in cleaned)):
                keywords.add(cleaned)

        return keywords

    def build_from_triples(self, triples: List[Dict]):
        """
        Build knowledge graph from extracted triples

        Args:
            triples: List of triple dicts with subject, relationship, object
        """
        print(f"\n🔨 Building knowledge graph from {len(triples)} triples...")

        for triple in triples:
            subject = triple.get('subject')
            relationship = triple.get('relationship')
            obj = triple.get('object')

            if not subject or not relationship or not obj:
                continue

            # Skip noise (prepositions as objects)
            noise_words = {'to', 'for', 'in', 'on', 'at', 'of', 'during', 'with', 'from'}
            if obj.lower() in noise_words:
                continue

            # Add nodes
            self.graph.add_node(subject, type='person')
            self.graph.add_node(obj, type='entity')

            # Add edge with metadata
            self.graph.add_edge(
                subject,
                obj,
                relationship=relationship,
                message_id=triple.get('message_id'),
                timestamp=triple.get('timestamp'),
                metadata=triple.get('metadata', {})
            )

            # Index by user
            self.user_index[subject].append(triple)

            # Index by relationship
            self.relationship_index[relationship].append(triple)

            # Index entities - IMPROVED: Index both full phrase AND keywords
            # Full phrase (for exact matches)
            self.entity_index[obj.lower()].add(subject)

            # Individual keywords (for partial/keyword matches)
            keywords = self._extract_keywords(obj)
            for keyword in keywords:
                self.entity_index[keyword].add(subject)

        print(f"✅ Graph built:")
        print(f"   - Nodes: {self.graph.number_of_nodes()}")
        print(f"   - Edges: {self.graph.number_of_edges()}")
        print(f"   - Users: {len(self.user_index)}")
        print(f"   - Relationship types: {len(self.relationship_index)}")

    def get_user_relationships(self, user_name: str, relationship: Optional[str] = None) -> List[Dict]:
        """
        Get all relationships for a user

        Args:
            user_name: User name to query
            relationship: Optional relationship type filter

        Returns:
            List of triples
        """
        triples = self.user_index.get(user_name, [])

        if relationship:
            triples = [t for t in triples if t['relationship'] == relationship]

        return triples

    def find_by_entity(self, entity: str) -> List[str]:
        """
        Find all users who have relationships with an entity

        Args:
            entity: Entity to search for (case-insensitive)

        Returns:
            List of user names
        """
        entity_lower = entity.lower()

        # Exact match
        if entity_lower in self.entity_index:
            return list(self.entity_index[entity_lower])

        # Partial match
        matches = set()
        for ent, users in self.entity_index.items():
            if entity_lower in ent:
                matches.update(users)

        return list(matches)

    def get_entity_context(self, entity: str) -> List[Dict]:
        """
        Get all triples mentioning an entity

        Args:
            entity: Entity to search for

        Returns:
            List of relevant triples
        """
        users = self.find_by_entity(entity)
        context = []

        for user in users:
            user_triples = self.user_index.get(user, [])
            # Filter to triples containing the entity
            for triple in user_triples:
                if entity.lower() in triple['object'].lower():
                    context.append(triple)

        return context

    def query(self, subject: Optional[str] = None,
              relationship: Optional[str] = None,
              obj: Optional[str] = None) -> List[Dict]:
        """
        Query graph with optional filters

        Args:
            subject: Filter by subject (user)
            relationship: Filter by relationship type
            obj: Filter by object (entity)

        Returns:
            List of matching triples
        """
        results = []

        # Start with all edges
        for u, v, data in self.graph.edges(data=True):
            # Apply filters
            if subject and u != subject:
                continue
            if relationship and data.get('relationship') != relationship:
                continue
            if obj and v != obj:
                continue

            results.append({
                'subject': u,
                'relationship': data.get('relationship'),
                'object': v,
                'message_id': data.get('message_id'),
                'timestamp': data.get('timestamp'),
                'metadata': data.get('metadata', {})
            })

        return results

    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'total_users': len(self.user_index),
            'relationship_counts': {
                rel: len(triples)
                for rel, triples in self.relationship_index.items()
            },
            'top_users': sorted(
                [(user, len(triples)) for user, triples in self.user_index.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        return stats

    def save(self, filepath: str = "data/knowledge_graph.pkl"):
        """Save knowledge graph to file"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'graph': self.graph,
                'user_index': dict(self.user_index),
                'relationship_index': dict(self.relationship_index),
                'entity_index': {k: list(v) for k, v in self.entity_index.items()}
            }, f)
        print(f"✅ Knowledge graph saved to {filepath}")

    def load(self, filepath: str = "data/knowledge_graph.pkl"):
        """Load knowledge graph from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.graph = data['graph']
            self.user_index = defaultdict(list, data['user_index'])
            self.relationship_index = defaultdict(list, data['relationship_index'])
            self.entity_index = defaultdict(set, {
                k: set(v) for k, v in data['entity_index'].items()
            })
        print(f"✅ Knowledge graph loaded from {filepath}")


def main():
    """Test knowledge graph building"""
    print("="*60)
    print("KNOWLEDGE GRAPH BUILDER")
    print("="*60)

    # Load triples
    print("\n📂 Loading triples...")
    with open('data/triples.json') as f:
        triples = json.load(f)
    print(f"✅ Loaded {len(triples)} triples")

    # Build graph
    kg = KnowledgeGraph()
    kg.build_from_triples(triples)

    # Show statistics
    print("\n" + "="*60)
    print("GRAPH STATISTICS")
    print("="*60)
    stats = kg.get_statistics()
    print(f"\nNodes: {stats['total_nodes']}")
    print(f"Edges: {stats['total_edges']}")
    print(f"Users: {stats['total_users']}")

    print("\nRelationship distribution:")
    for rel, count in stats['relationship_counts'].items():
        print(f"  {rel:25s}: {count:4d}")

    print("\nTop 10 most active users:")
    for user, count in stats['top_users']:
        print(f"  {user:30s}: {count:4d} relationships")

    # Test queries
    print("\n" + "="*60)
    print("TEST QUERIES")
    print("="*60)

    # Query 1: Vikram's ownership
    print("\nQuery: What does Vikram Desai own?")
    vikram_owns = kg.get_user_relationships("Vikram Desai", "OWNS")
    print(f"Found {len(vikram_owns)} items")
    for triple in vikram_owns[:5]:
        print(f"  • {triple['object']}")

    # Query 2: Who mentions London?
    print("\nQuery: Who mentions London?")
    london_users = kg.find_by_entity("London")
    print(f"Found {len(london_users)} users: {london_users[:5]}")

    # Query 3: Get London context
    print("\nQuery: London context")
    london_context = kg.get_entity_context("London")
    print(f"Found {len(london_context)} triples")
    for triple in london_context[:3]:
        print(f"  • {triple['subject']} - {triple['relationship']} - {triple['object']}")

    # Save graph
    print("\n" + "="*60)
    kg.save()

    print("\n" + "="*60)
    print("✅ Knowledge graph ready!")
    print("="*60)


if __name__ == "__main__":
    main()
