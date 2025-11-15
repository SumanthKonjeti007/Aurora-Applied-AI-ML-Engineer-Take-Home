"""Test ALL 10 queries to verify diversity filter works generically"""
import sys
from src.qa_system import QASystem

# Initialize once
print("Initializing QA System...")
qa = QASystem()
print("="*80)

# All 10 queries
queries = [
    ("Query 1", "What are Fatima El-Tahir's plans for next month?"),
    ("Query 2", "Which clients have both stated a preference and filed a complaint?"),
    ("Query 3", "Which clients requested a private tour of the Louvre?"),
    ("Query 4", "Which clients have visited both Paris and Tokyo?"),
    ("Query 5", "How many clients requested similar spa services?"),
    ("Query 6", "Who said a restaurant bill missed loyalty discounts?"),
    ("Query 7", "Who asked for opera/symphony/ballet tickets and mentioned travel dates near those events?"),
    ("Query 8", "Summarize Armand Dupont's preferences into 2 bullet points"),
    ("Query 9", "For Four Seasons Tokyo, what suite type and nights were requested?"),
    ("Query 10", "Who made urgent same-day requests?"),
]

for name, query in queries:
    print(f"\n{'='*80}")
    print(f"{name}: {query}")
    print(f"{'='*80}")
    
    result = qa.answer(query, verbose=False)
    
    # Show user distribution
    if 'retrieval_stats' in result:
        stats = result['retrieval_stats']
        user_dist = {}
        for msg in stats.get('retrieved_messages', []):
            user = msg.get('user_name', 'Unknown')
            user_dist[user] = user_dist.get(user, 0) + 1
        
        print(f"✓ Retrieved: {len(stats.get('retrieved_messages', []))} messages")
        print(f"✓ User distribution: {user_dist}")
        
        # Check if any user has > 2 messages (diversity violation)
        max_count = max(user_dist.values()) if user_dist else 0
        if max_count > 2:
            print(f"⚠️  DIVERSITY VIOLATION: One user has {max_count} messages (max should be 2)")
        else:
            print(f"✓ Diversity: OK (max {max_count} per user)")
    
    # Show brief answer
    answer = result.get('answer', 'No answer')
    print(f"\nAnswer (first 200 chars): {answer[:200]}...")

print(f"\n{'='*80}")
print("TESTING COMPLETE")
print(f"{'='*80}")
