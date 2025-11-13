"""
Answer Generator Module

Generates natural language answers using LLM with retrieved context (RAG).

Architecture:
- Takes user query + retrieved context
- Constructs RAG prompt
- Calls LLM (Groq/OpenAI)
- Returns formatted answer

This is the final step in the pipeline: Query → Retrieve → Generate Answer
"""
from typing import List, Tuple, Dict, Optional
import os
from groq import Groq


class AnswerGenerator:
    """
    Generate answers using LLM with retrieved context (RAG)

    Uses Groq API with Llama 3.1 70B model for fast, high-quality responses.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize answer generator

        Args:
            api_key: Groq API key (or use GROQ_API_KEY env var)
            model: LLM model to use
        """
        self.api_key = api_key or os.environ.get('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("Groq API key required. Set GROQ_API_KEY env var or pass api_key.")

        self.model = model
        self.client = Groq(api_key=self.api_key)

    def generate(
        self,
        query: str,
        context: str,
        temperature: float = 0.3,
        max_tokens: int = 500,
        verbose: bool = False
    ) -> Dict[str, any]:
        """
        Generate answer using LLM with retrieved context

        Args:
            query: Original user query
            context: Retrieved context (formatted messages)
            temperature: LLM temperature (0.0-1.0, lower = more focused)
            max_tokens: Maximum response length
            verbose: Print generation details

        Returns:
            {
                'answer': 'Generated answer text',
                'model': 'Model used',
                'tokens': {'prompt': X, 'completion': Y, 'total': Z}
            }
        """
        if verbose:
            print(f"\n{'='*80}")
            print("ANSWER GENERATOR")
            print(f"{'='*80}")
            print(f"Query: {query}")
            print(f"Context length: {len(context)} chars")
            print(f"Model: {self.model}")
            print(f"Temperature: {temperature}")

        # Construct RAG prompt
        prompt = self._build_prompt(query, context)

        if verbose:
            print(f"Prompt length: {len(prompt)} chars")
            print(f"{'='*80}\n")

        # Call LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            answer = response.choices[0].message.content
            usage = response.usage

            result = {
                'answer': answer,
                'model': self.model,
                'tokens': {
                    'prompt': usage.prompt_tokens,
                    'completion': usage.completion_tokens,
                    'total': usage.total_tokens
                }
            }

            if verbose:
                print(f"✅ Answer generated ({usage.completion_tokens} tokens)")

            return result

        except Exception as e:
            if verbose:
                print(f"❌ Error: {str(e)}")
            raise

    def _get_system_prompt(self) -> str:
        """
        System prompt that defines the assistant's behavior

        Returns:
            System prompt string
        """
        return """You are a helpful concierge assistant for a luxury lifestyle management service.

Your role:
- Answer user questions based on the provided context (member messages and requests)
- Be concise, professional, and helpful
- If the context doesn't contain enough information, say so honestly
- For comparison questions, present information about both parties fairly
- Use specific details from the context to support your answers
- Don't make up information not present in the context

Tone: Professional, warm, and service-oriented."""

    def _build_prompt(self, query: str, context: str) -> str:
        """
        Build RAG prompt with query and context

        Args:
            query: User query
            context: Retrieved context messages

        Returns:
            Formatted prompt string
        """
        prompt = f"""Based on the following member messages and requests, please answer the user's question.

CONTEXT:
{context}

USER QUESTION:
{query}

Please provide a clear, concise answer based on the context above. If the context doesn't contain enough information to fully answer the question, acknowledge what information is available and what is missing."""

        return prompt

    def generate_with_sources(
        self,
        query: str,
        composed_results: List[Tuple[Dict, float]],
        temperature: float = 0.3,
        max_tokens: int = 500,
        verbose: bool = False
    ) -> Dict[str, any]:
        """
        Generate answer and include source messages

        Args:
            query: User query
            composed_results: List of (message, score) tuples
            temperature: LLM temperature
            max_tokens: Max response tokens
            verbose: Print details

        Returns:
            {
                'answer': 'Generated answer',
                'sources': [list of source messages],
                'model': 'Model name',
                'tokens': {usage stats}
            }
        """
        from src.result_composer import ResultComposer

        composer = ResultComposer()
        context = composer.format_context_for_llm(composed_results, include_scores=False)

        result = self.generate(query, context, temperature, max_tokens, verbose)

        # Add sources
        result['sources'] = [
            {
                'user': msg['user_name'],
                'message': msg['message'],
                'score': score
            }
            for msg, score in composed_results
        ]

        return result


def test_answer_generator():
    """Test answer generator with sample context"""
    print("="*80)
    print("ANSWER GENERATOR TEST")
    print("="*80)

    # Sample context
    sample_context = """[1] Thiago Monteiro:
I love Italian cuisine, please suggest a restaurant in New York that fits.

[2] Hans Müller:
I prefer Italian cuisine when dining in New York, note this for future bookings.

[3] Thiago Monteiro:
Please ensure the in-room dining menu has my updated seafood dietary preferences.

[4] Hans Müller:
We have dietary restrictions; make sure the restaurant is aware of gluten and dairy restrictions."""

    sample_query = "Compare the dining preferences of Thiago Monteiro and Hans Müller"

    # Initialize generator
    try:
        generator = AnswerGenerator()

        print("\n" + "="*80)
        print("TEST: Generate Answer")
        print("="*80)

        result = generator.generate(
            query=sample_query,
            context=sample_context,
            temperature=0.3,
            verbose=True
        )

        print("\n" + "="*80)
        print("GENERATED ANSWER")
        print("="*80)
        print(result['answer'])

        print("\n" + "="*80)
        print("USAGE STATS")
        print("="*80)
        print(f"Prompt tokens: {result['tokens']['prompt']}")
        print(f"Completion tokens: {result['tokens']['completion']}")
        print(f"Total tokens: {result['tokens']['total']}")
        print(f"Model: {result['model']}")

        print("\n" + "="*80)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nNote: Make sure GROQ_API_KEY environment variable is set")
        print("Or the API key is available in your environment")


if __name__ == "__main__":
    test_answer_generator()
