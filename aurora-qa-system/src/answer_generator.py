"""
Answer Generator Module

Generates natural language answers using LLM with retrieved context (RAG).

Architecture:
- Takes user query + retrieved context
- Constructs RAG prompt
- Calls LLM (Mistral AI)
- Returns formatted answer

This is the final step in the pipeline: Query → Retrieve → Generate Answer
"""
from typing import List, Tuple, Dict, Optional
import os
from groq import Groq
# from mistralai import Mistral  # SWITCHED TO GROQ FOR BETTER RATE LIMITS


class AnswerGenerator:
    """
    Generate answers using LLM with retrieved context (RAG)

    Uses Groq API (llama-3.3-70b-versatile) for fast, high-quality responses with generous rate limits.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize answer generator

        Args:
            api_key: Groq API key (or use GROQ_API_KEY env var)
            model: LLM model to use (default: llama-3.3-70b-versatile)
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

        # Call LLM (Groq)
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
        return """You are an intelligent concierge assistant for a luxury lifestyle management service.

Your answers will be displayed directly in a UI to users, so they must be:
✓ Clear and concise (2-4 sentences for simple questions, structured lists for complex ones)
✓ Natural and conversational (avoid robotic language)
✓ Actionable (provide insights, not just raw data)
✓ Professional yet warm

MARKDOWN FORMATTING REQUIRED:
- **Use markdown** for all responses - your output will be rendered as HTML
- Use **bold** for client names and important details: **Name**
- Use bullet points with `-` or `*` for lists
- Use numbered lists `1.` when order matters
- Add line breaks between items for readability

RESPONSE FORMAT RULES:

1. SHORT ANSWERS (for simple lookups):
   - Direct answer in 1-3 sentences
   - Example: "**Vikram Desai** has requested spa services at several locations including Tokyo and Paris."

2. LISTS (for "which clients" or multiple items):
   - Use markdown bullet points with bold names
   - Keep each item concise (name + key detail)
   - Example:
     "6 clients requested a personal shopper in Milan:

     - **Vikram Desai**: Requested for the 12th
     - **Thiago Monteiro**: For an upcoming visit
     - **Hans Müller**: During his Milan visit
     - **Lorenzo Cavalli**: Looking for suggestions and recommendations
     - **Sophia Al-Farsi**: For a shopping day and tour
     - **Amina Van Den Berg**: For next weekend"

3. SUMMARIES (for preferences/patterns):
   - Lead with the key insight
   - Support with 2-3 examples using bold for names
   - Example: "Most clients prefer evening reservations. For instance, **Thiago** typically books 8 PM slots, while **Layla** prefers 7:30 PM."

4. NO DATA FOUND:
   - Be helpful, not dismissive
   - Suggest alternatives
   - Example: "I don't have specific car ownership information for Vikram Desai. However, I can see he frequently requests car services in NYC and private transfers to airports. Would you like to know more about his transportation preferences?"

CRITICAL ACCURACY RULES:

1. NEVER mention technical details:
   ✗ "Based on message 1, 5, and 8..."
   ✗ "The context shows..."
   ✗ "According to the provided data..."
   ✓ Just state the facts naturally

2. NEVER merge separate facts into new claims:
   ✗ "Client stayed at Four Seasons Tokyo" (if one message says Four Seasons, another says Tokyo)
   ✓ "Client has stayed at Four Seasons properties and visited Tokyo"

3. IF UNCERTAIN, be honest but helpful:
   ✗ "I don't have that information." (too blunt)
   ✓ "I don't see specific details about X, but I found related information about Y. Would that be helpful?"

4. AGGREGATE intelligently:
   - For "which clients" queries: List names with brief context
   - For counts: Give the number first, then details if needed
   - For comparisons: Highlight similarities/differences clearly

Tone: Professional, conversational, and helpful. Think "knowledgeable assistant" not "database query result"."""

    def _build_prompt(self, query: str, context: str) -> str:
        """
        Build RAG prompt with query and context

        Args:
            query: User query
            context: Retrieved context messages

        Returns:
            Formatted prompt string
        """
        # Detect query type for better formatting hints
        query_lower = query.lower()

        if any(word in query_lower for word in ['which', 'who', 'what clients', 'list']):
            format_hint = "\n\nFormat: Provide a markdown bullet list with **bold client names**. Lead with a count (e.g., '5 clients requested...'). Use this format:\n- **Name**: Brief detail\n- **Name**: Brief detail"
        elif any(word in query_lower for word in ['how many', 'count', 'number of']):
            format_hint = "\n\nFormat: Start with the number, then provide brief supporting details if relevant. Use **bold** for emphasis."
        elif any(word in query_lower for word in ['compare', 'difference', 'similar']):
            format_hint = "\n\nFormat: Highlight key similarities or differences. Use a comparison structure."
        elif any(word in query_lower for word in ['preference', 'prefer', 'favorite']):
            format_hint = "\n\nFormat: Summarize the preference pattern with 2-3 concrete examples."
        else:
            format_hint = "\n\nFormat: Answer directly and concisely in 2-4 sentences."

        prompt = f"""Answer this question using the client messages below.

QUESTION: {query}

CLIENT MESSAGES:
{context}
{format_hint}

IMPORTANT:
- Answer naturally (no technical references like "message 1" or "context shows")
- If information is incomplete, be helpful: acknowledge what you found and offer related info
- Focus on being useful for a UI display - clear and actionable

Answer:"""

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
