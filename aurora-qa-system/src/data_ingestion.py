"""
Data Ingestion Module
Fetches all messages from the API and saves locally
"""
import os
import requests
import json
import random
from typing import List, Dict
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def fetch_all_messages(api_base_url: str, limit: int = 100, max_retries: int = 3) -> List[Dict]:
    """
    Fetch all messages from API with pagination and retry logic

    Args:
        api_base_url: Base URL of the API
        limit: Number of messages per page
        max_retries: Maximum number of retries for failed requests

    Returns:
        List of all messages
    """
    import time

    all_messages = []
    skip = 0
    consecutive_failures = 0

    print(f"Fetching messages from {api_base_url}/messages/...")

    with tqdm(desc="Fetching messages") as pbar:
        while consecutive_failures < max_retries:
            try:
                response = requests.get(
                    f"{api_base_url}/messages/",
                    params={"skip": skip, "limit": limit},
                    headers={"accept": "application/json"},
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                items = data.get('items', [])
                if not items:
                    print(f"\nNo more items at skip={skip}")
                    break

                all_messages.extend(items)
                pbar.update(len(items))
                consecutive_failures = 0  # Reset on success

                # Check if we've fetched all
                total = data.get('total', 0)
                pbar.set_postfix({"fetched": len(all_messages), "total": total})

                if len(all_messages) >= total:
                    break

                skip += limit
                time.sleep(0.1)  # Small delay to avoid rate limiting

            except requests.exceptions.HTTPError as e:
                consecutive_failures += 1
                print(f"\n⚠️  HTTP Error at skip={skip}: {e.response.status_code}")

                if consecutive_failures < max_retries:
                    wait_time = 2 ** consecutive_failures
                    print(f"Retrying in {wait_time} seconds... (attempt {consecutive_failures}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"Max retries reached. Fetched {len(all_messages)} messages.")
                    break

            except Exception as e:
                consecutive_failures += 1
                print(f"\nError at skip={skip}: {e}")

                if consecutive_failures < max_retries:
                    wait_time = 2 ** consecutive_failures
                    print(f"Retrying in {wait_time} seconds... (attempt {consecutive_failures}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"Max retries reached. Fetched {len(all_messages)} messages.")
                    break

    print(f"\n✅ Fetched {len(all_messages)} messages")
    return all_messages


def save_messages(messages: List[Dict], filepath: str = "data/raw_messages.json"):
    """Save messages to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(messages, f, indent=2)
    print(f"✅ Saved {len(messages)} messages to {filepath}")


def load_messages(filepath: str = "data/raw_messages.json") -> List[Dict]:
    """Load messages from JSON file"""
    with open(filepath, 'r') as f:
        messages = json.load(f)
    print(f"✅ Loaded {len(messages)} messages from {filepath}")
    return messages


def basic_stats(messages: List[Dict]):
    """Print basic statistics"""
    print("\n" + "="*60)
    print("📊 BASIC STATISTICS")
    print("="*60)

    print(f"\nTotal Messages: {len(messages)}")

    unique_users = set(msg['user_name'] for msg in messages)
    print(f"Unique Users: {len(unique_users)}")

    timestamps = [msg['timestamp'] for msg in messages]
    print(f"Date Range: {min(timestamps)} to {max(timestamps)}")

    message_lengths = [len(msg['message']) for msg in messages]
    avg_length = sum(message_lengths) / len(message_lengths)
    print(f"Average Message Length: {avg_length:.1f} characters")

    # Check for duplicates
    message_ids = [msg['id'] for msg in messages]
    duplicates = len(message_ids) - len(set(message_ids))
    print(f"Duplicate Messages: {duplicates}")

    # Check for missing data
    missing_fields = sum(1 for msg in messages if not all([
        msg.get('id'),
        msg.get('user_name'),
        msg.get('message')
    ]))
    print(f"Messages with Missing Fields: {missing_fields}")


def show_samples(messages: List[Dict], n: int = 10):
    """Show random sample messages"""
    print("\n" + "="*60)
    print("📝 SAMPLE MESSAGES")
    print("="*60)

    samples = random.sample(messages, min(n, len(messages)))

    for i, msg in enumerate(samples, 1):
        print(f"\n{i}. User: {msg['user_name']}")
        print(f"   Timestamp: {msg['timestamp']}")
        print(f"   Message: {msg['message']}")


def test_example_questions(messages: List[Dict]):
    """Test if we can find relevant messages for example questions"""
    print("\n" + "="*60)
    print("🔍 TESTING EXAMPLE QUESTIONS")
    print("="*60)

    test_cases = [
        {
            'question': 'When is Layla planning her trip to London?',
            'user': 'Layla',
            'keywords': ['london', 'trip']
        },
        {
            'question': 'How many cars does Vikram Desai have?',
            'user': 'Vikram Desai',
            'keywords': ['car', 'tesla', 'porsche', 'my']
        },
        {
            'question': "What are Amira's favorite restaurants?",
            'user': 'Amira',
            'keywords': ['restaurant', 'favorite', 'dining', 'dinner']
        }
    ]

    for test in test_cases:
        print(f"\n--- Question: {test['question']} ---")

        # Find relevant messages
        relevant = []
        for msg in messages:
            # Check if user matches (partial match for names)
            if test['user'].lower() in msg['user_name'].lower():
                # Check if any keyword is in message
                if any(kw in msg['message'].lower() for kw in test['keywords']):
                    relevant.append(msg)

        print(f"Found {len(relevant)} potentially relevant messages")

        # Show top 3
        for i, msg in enumerate(relevant[:3], 1):
            print(f"\n  {i}. {msg['user_name']}: {msg['message']}")

        if not relevant:
            print("  ⚠️  No relevant messages found!")


def main():
    """Main execution"""
    print("="*60)
    print("DATA INGESTION")
    print("="*60)

    # Get API URL from environment
    API_BASE_URL = os.getenv("API_BASE_URL", "https://november7-730026606190.europe-west1.run.app")
    print(f"API URL: {API_BASE_URL}\n")

    # Fetch all messages
    messages = fetch_all_messages(API_BASE_URL, limit=100)

    # Save to file
    save_messages(messages, "data/raw_messages.json")

    # Basic statistics
    basic_stats(messages)

    # Show samples
    show_samples(messages, n=10)

    # Test example questions
    test_example_questions(messages)

    print("\n" + "="*60)
    print("✅ DATA INGESTION COMPLETE!")
    print("="*60)
    print(f"\nData saved to: data/raw_messages.json")
    print(f"Total messages: {len(messages)}")
    print("\nNext step: Entity extraction and graph building")


if __name__ == "__main__":
    main()
