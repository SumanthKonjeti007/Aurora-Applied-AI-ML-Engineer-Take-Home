"""
Add user_id payload index to Qdrant collection
This enables filtering by user_id in queries
"""
import os
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType

# Qdrant configuration (matching qdrant_search.py)
QDRANT_URL = "https://64ffc9ea-bc97-48f6-97d9-7d00e5e3481d.europe-west3-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.ZpU1k_gFE_V37W19f5akrhArDSer0798azjq0ldnETo"
COLLECTION_NAME = "aurora_messages"

print("="*80)
print("ADDING user_id PAYLOAD INDEX TO QDRANT")
print("="*80)

# Connect to Qdrant
print(f"\n📡 Connecting to Qdrant Cloud...")
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=60
)
print("   ✅ Connected!")

# Create payload index for user_id (skip collection verification due to client version issues)
print(f"\n🔧 Creating payload index for 'user_id' field in collection '{COLLECTION_NAME}'...")

try:
    # Method 1: Try standard API
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="user_id",
        field_schema=PayloadSchemaType.KEYWORD,
        wait=True
    )
    print("   ✅ Index created successfully!")

except Exception as e:
    error_msg = str(e).lower()

    if "already exists" in error_msg or "exist" in error_msg:
        print("   ℹ️  Index already exists (no action needed)")
    else:
        print(f"   ⚠️  Standard method failed: {e}")
        print(f"\n🔄 Trying direct HTTP API...")

        # Method 2: Try direct HTTP API
        try:
            import requests
            url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}/index"
            headers = {
                "api-key": QDRANT_API_KEY,
                "Content-Type": "application/json"
            }
            data = {
                "field_name": "user_id",
                "field_schema": "keyword"
            }

            response = requests.put(url, json=data, headers=headers)

            if response.status_code in [200, 201]:
                print("   ✅ Index created via HTTP API!")
            elif response.status_code == 409:
                print("   ℹ️  Index already exists!")
            else:
                print(f"   ❌ HTTP API failed: {response.status_code} - {response.text}")
                raise Exception(f"Failed to create index: {response.text}")

        except Exception as e2:
            print(f"   ❌ All methods failed: {e2}")
            raise

print("\n" + "="*80)
print("✅ COMPLETE - user_id index is now ready!")
print("="*80)
print("\nUser-specific queries should now work:")
print("  - 'What are Fatima El-Tahir's plans?'")
print("  - 'Compare Layla and Lily's preferences'")
print("  - Any query mentioning specific user names")
print("="*80)
