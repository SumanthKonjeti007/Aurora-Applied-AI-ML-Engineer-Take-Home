"""
QA System - End-to-End Pipeline

Complete RAG pipeline integrating all components:
1. QueryProcessor - Understand, classify, decompose query
2. HybridRetriever - Retrieve with dynamic weights (semantic + BM25 + graph)
3. ResultComposer - Merge/interleave results
4. AnswerGenerator - Generate final answer with LLM

Usage:
    system = QASystem()
    result = system.answer("What are Vikram's service expectations?")
    print(result['answer'])
"""
from typing import Dict, List
import os

from src.query_processor import QueryProcessor
from src.hybrid_retriever import HybridRetriever
from src.result_composer import ResultComposer
from src.answer_generator import AnswerGenerator
from src.graph_analytics import GraphAnalytics


class QASystem:
    """
    Complete Question-Answering system with dynamic retrieval

    Pipeline:
    User Query → Process → Retrieve (Dynamic Weights) → Compose → Generate Answer
    """

    def __init__(
        self,
        embedding_path: str = "data/embeddings",
        bm25_path: str = "data/bm25",
        graph_path: str = "data/knowledge_graph.pkl",
        groq_api_key: str = None
    ):
        """
        Initialize QA system with all components

        Args:
            embedding_path: Path to embeddings index
            bm25_path: Path to BM25 index
            graph_path: Path to knowledge graph
            groq_api_key: Groq API key for LLM
        """
        print("\n🚀 Initializing QA System...")
        print("="*80)

        # Initialize retriever (loads all indexes)
        self.retriever = HybridRetriever(
            embedding_path=embedding_path,
            bm25_path=bm25_path,
            graph_path=graph_path
        )

        # Initialize query processor
        print("\n  5/5 Initializing query processor...")
        self.processor = QueryProcessor(self.retriever.name_resolver)

        # Initialize result composer
        self.composer = ResultComposer()

        # Initialize answer generator
        self.generator = AnswerGenerator(api_key=groq_api_key)

        # Initialize graph analytics pipeline
        print("\n  6/6 Initializing graph analytics pipeline...")
        self.analytics = GraphAnalytics(
            knowledge_graph=self.retriever.knowledge_graph,
            api_key=groq_api_key
        )

        print("\n✅ QA System ready!")
        print("="*80)

    def answer(
        self,
        query: str,
        top_k: int = 20,
        temperature: float = 0.3,
        verbose: bool = False
    ) -> Dict:
        """
        Answer user query using full RAG pipeline

        Args:
            query: User question
            top_k: Number of context messages to retrieve (default: 20)
            temperature: LLM temperature for answer generation
            verbose: Print detailed pipeline execution

        Returns:
            {
                'query': 'Original query',
                'answer': 'Generated answer',
                'sources': [list of source messages],
                'query_plans': [decomposition & classification details],
                'tokens': {LLM token usage}
            }
        """
        if verbose:
            print(f"\n{'='*80}")
            print("QA SYSTEM - FULL PIPELINE")
            print(f"{'='*80}")
            print(f"Query: \"{query}\"")
            print(f"{'='*80}\n")

        # ========== STEP 1: QUERY PROCESSING ==========
        if verbose:
            print("STEP 1: Query Processing")
            print("-"*80)

        query_plans = self.processor.process(query, verbose=verbose)

        # ========== ROUTING: Check if ANALYTICS or LOOKUP ==========
        route = query_plans[0].get('route', 'LOOKUP')

        if route == "ANALYTICS":
            # Use Graph Analytics Pipeline
            if verbose:
                print("\n🔀 ROUTE: ANALYTICS → Using Graph Analytics Pipeline")
                print("-"*80)

            analytics_result = self.analytics.analyze(query, verbose=verbose)

            # Format as standard result
            return {
                'query': query,
                'answer': analytics_result['answer'],
                'sources': [],  # Analytics doesn't return message sources
                'query_plans': query_plans,
                'analytics_data': analytics_result['aggregated_data'],
                'route': 'ANALYTICS'
            }

        # ========== STEP 2: HYBRID RETRIEVAL (LOOKUP Route) ==========
        if verbose:
            print("\n🔀 ROUTE: LOOKUP → Using RAG Pipeline")
            print("\nSTEP 2: Hybrid Retrieval")
            print("-"*80)

        all_results = []
        for i, plan in enumerate(query_plans, 1):
            if verbose:
                print(f"\n  Retrieving for sub-query {i}/{len(query_plans)}:")
                print(f"    Query: \"{plan['query']}\"")
                print(f"    Type: {plan['type']}")
                print(f"    Weights: sem={plan['weights']['semantic']}, "
                      f"bm25={plan['weights']['bm25']}, "
                      f"graph={plan['weights']['graph']}")

            # Retrieve with dynamic weights AND query type for conditional diversity
            results = self.retriever.search(
                query=plan['query'],
                top_k=top_k,
                weights=plan['weights'],
                query_type=plan['type'],  # Pass query type for conditional diversity
                verbose=False  # Suppress retriever verbose to avoid clutter
            )

            all_results.append(results)

            if verbose:
                print(f"    Retrieved: {len(results)} results")

        # ========== STEP 3: RESULT COMPOSITION ==========
        if verbose:
            print("\nSTEP 3: Result Composition")
            print("-"*80)

        composed_results = self.composer.compose(
            all_results,
            strategy="auto",
            max_results=top_k,
            verbose=verbose
        )

        # ========== STEP 4: ANSWER GENERATION ==========
        if verbose:
            print("\nSTEP 4: Answer Generation")
            print("-"*80)

        result = self.generator.generate_with_sources(
            query=query,
            composed_results=composed_results,
            temperature=temperature,
            verbose=verbose
        )

        # Add pipeline metadata
        result['query'] = query
        result['query_plans'] = query_plans
        result['num_sources'] = len(composed_results)
        result['route'] = 'LOOKUP'

        if verbose:
            print(f"\n{'='*80}")
            print("PIPELINE COMPLETE")
            print(f"{'='*80}\n")

        return result


def main():
    """Demo QA system with sample query"""
    print("="*80)
    print("QA SYSTEM DEMO")
    print("="*80)

    # Initialize system
    system = QASystem()

    # Test query
    query = "Compare the dining preferences of Thiago Monteiro and Hans Müller"

    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print(f"{'='*80}\n")

    # Get answer
    result = system.answer(query, top_k=8, verbose=True)

    # Display answer
    print("\n" + "="*80)
    print("FINAL ANSWER")
    print("="*80)
    print(result['answer'])

    # Display sources
    print("\n" + "="*80)
    print(f"SOURCES ({len(result['sources'])} messages)")
    print("="*80)
    for i, source in enumerate(result['sources'][:5], 1):
        print(f"\n{i}. {source['user']} (score: {source['score']:.4f})")
        print(f"   {source['message'][:100]}...")

    # Display stats
    print("\n" + "="*80)
    print("PIPELINE STATS")
    print("="*80)
    print(f"Query plans: {len(result['query_plans'])}")
    print(f"Sources retrieved: {result['num_sources']}")
    print(f"LLM tokens: {result['tokens']['total']} "
          f"(prompt: {result['tokens']['prompt']}, "
          f"completion: {result['tokens']['completion']})")
    print(f"Model: {result['model']}")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
