"""
Temporal Metadata Extraction

Extracts and normalizes dates from messages using timestamp context.

Process:
1. Read message text + timestamp
2. Extract dates using datefinder
3. Normalize using timestamp as reference
4. Handle relative dates (next month, Q4, etc.)
5. Store normalized ISO dates

Usage:
    python scripts/extract_temporal_metadata.py
"""
import json
import datefinder
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import re
from typing import List, Optional

def normalize_dates(text: str, timestamp: str) -> List[str]:
    """
    Extract and normalize dates from text using timestamp context

    Args:
        text: Message text ("Book tickets for December 3rd")
        timestamp: ISO timestamp ("2025-07-11T03:33:23Z")

    Returns:
        List of normalized ISO dates ["2025-12-03"]

    Examples:
        text="December 3rd", timestamp="2025-07-11" → ["2025-12-03"]
        text="next month", timestamp="2025-11-15" → ["2025-12-01"]
        text="Q4 plans", timestamp="2025-08-01" → ["2025-10-01", "2025-11-01", "2025-12-01"]
    """
    try:
        # Parse reference date
        reference_date = parse(timestamp)
        normalized_dates = []

        # Strategy 1: Use datefinder with reference date
        dates_found = list(datefinder.find_dates(
            text,
            base_date=reference_date,
            strict=False
        ))

        for date in dates_found:
            normalized_dates.append(date.date().isoformat())

        # Strategy 2: Handle relative dates
        text_lower = text.lower()

        # "next month"
        if 'next month' in text_lower:
            next_month = reference_date + relativedelta(months=1)
            normalized_dates.append(next_month.replace(day=1).date().isoformat())

        # "this month"
        if 'this month' in text_lower:
            this_month = reference_date.replace(day=1)
            normalized_dates.append(this_month.date().isoformat())

        # Strategy 3: Handle quarters (Q1, Q2, Q3, Q4)
        quarter_match = re.search(r'q([1-4])', text_lower)
        if quarter_match:
            quarter = int(quarter_match.group(1))
            year = reference_date.year

            # Extract year if specified (Q4 2025)
            year_match = re.search(r'q[1-4]\s*(\d{4})', text_lower)
            if year_match:
                year = int(year_match.group(1))

            # Map quarters to months
            quarter_months = {
                1: [1, 2, 3],
                2: [4, 5, 6],
                3: [7, 8, 9],
                4: [10, 11, 12]
            }

            for month in quarter_months[quarter]:
                date = datetime(year, month, 1)
                normalized_dates.append(date.date().isoformat())

        # Deduplicate and sort
        normalized_dates = sorted(list(set(normalized_dates)))

        return normalized_dates

    except Exception as e:
        print(f"⚠️  Error extracting dates from '{text[:50]}...': {e}")
        return []


def process_messages(input_file: str, output_file: str):
    """
    Process all messages and add normalized_dates metadata

    Args:
        input_file: Path to raw_messages.json
        output_file: Path to save messages_with_dates.json
    """
    print(f"📂 Loading messages from {input_file}...")
    with open(input_file, 'r') as f:
        messages = json.load(f)

    print(f"📊 Processing {len(messages)} messages...")

    dates_extracted = 0
    for i, msg in enumerate(messages):
        # Extract and normalize dates
        normalized_dates = normalize_dates(msg['message'], msg['timestamp'])
        msg['normalized_dates'] = normalized_dates

        if normalized_dates:
            dates_extracted += 1

        # Progress
        if (i + 1) % 500 == 0:
            print(f"  Processed {i + 1}/{len(messages)} messages...")

    print(f"\n✅ Extraction complete!")
    print(f"   Total messages: {len(messages)}")
    print(f"   Messages with dates: {dates_extracted} ({dates_extracted/len(messages)*100:.1f}%)")

    # Save
    print(f"\n💾 Saving to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(messages, f, indent=2)

    print(f"✅ Saved!")

    # Show samples
    print(f"\n📋 Sample extractions:")
    samples = [msg for msg in messages if msg['normalized_dates']][:5]
    for msg in samples:
        print(f"\n  Message: {msg['message'][:60]}...")
        print(f"  Timestamp: {msg['timestamp']}")
        print(f"  Extracted: {msg['normalized_dates']}")


if __name__ == "__main__":
    import os

    # Paths
    data_dir = "data"
    input_file = os.path.join(data_dir, "raw_messages.json")
    output_file = os.path.join(data_dir, "messages_with_dates.json")

    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found!")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Please run from project root: python scripts/extract_temporal_metadata.py")
        exit(1)

    process_messages(input_file, output_file)
