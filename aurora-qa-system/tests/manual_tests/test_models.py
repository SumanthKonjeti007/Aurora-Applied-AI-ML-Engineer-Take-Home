"""
Quick test to verify Groq and BGE-small setup
"""
import os
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

load_dotenv()

print("="*60)
print("MODEL SETUP VERIFICATION")
print("="*60)

# Test 1: Groq API
print("\n1. Testing Groq + Llama 3.1...")
try:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": "Say 'Hello from Llama 3.1!' in exactly 5 words."}
        ],
        temperature=0.1,
        max_tokens=50
    )

    print(f"✅ Groq API working!")
    print(f"   Model: llama-3.1-8b-instant")
    print(f"   Response: {response.choices[0].message.content}")
    print(f"   Tokens used: {response.usage.total_tokens}")

except Exception as e:
    print(f"❌ Groq API error: {e}")

# Test 2: BGE Embeddings
print("\n2. Testing BGE-small-en-v1.5...")
try:
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')

    test_texts = [
        "I need two tickets to the opera.",
        "Book a villa in Santorini.",
        "My Tesla needs service."
    ]

    embeddings = model.encode(test_texts)

    print(f"✅ BGE embeddings working!")
    print(f"   Model: BAAI/bge-small-en-v1.5")
    print(f"   Embedding shape: {embeddings.shape}")
    print(f"   Dimensions: {embeddings.shape[1]}")
    print(f"   Sample embedding (first 5 dims): {embeddings[0][:5]}")

except Exception as e:
    print(f"❌ BGE embedding error: {e}")

print("\n" + "="*60)
print("✅ SETUP COMPLETE!")
print("="*60)
print("\nConfiguration:")
print(f"  LLM: Groq + llama-3.1-8b-instant")
print(f"  Embeddings: BAAI/bge-small-en-v1.5 (384 dims)")
print(f"  Cost: $0 (FREE)")
