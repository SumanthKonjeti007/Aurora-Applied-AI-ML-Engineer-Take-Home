"""
Name Resolver

Resolves partial names, typos, and variations to canonical full names.
Handles: "Sophia" → "Sophia Al-Farsi", "Al-Farsi" → "Sophia Al-Farsi"
Also maps user_name → user_id for fast ID lookups.
"""
from typing import List, Optional, Dict, Set, Tuple
from difflib import SequenceMatcher
import json
import os
import re


class NameResolver:
    """
    Resolves partial names and variations to canonical full names

    Features:
    - Partial matching: "Sophia" → "Sophia Al-Farsi"
    - Hyphenated parts: "Al-Farsi" → "Sophia Al-Farsi"
    - Case insensitive: "sophia al farsi" → "Sophia Al-Farsi"
    - Fuzzy matching: "Sofya" → "Sophia Al-Farsi" (typo tolerance)
    - Ambiguity detection: Returns multiple matches if ambiguous
    - User ID mapping: "Sophia Al-Farsi" → user_id (for fast filtering)
    """

    def __init__(self):
        """Initialize empty name resolver"""
        # Canonical storage: normalized → original
        self.canonical_names: Dict[str, str] = {}  # "sophia al-farsi" → "Sophia Al-Farsi"

        # Name parts index: part → [full names]
        self.name_parts_index: Dict[str, List[str]] = {}  # "sophia" → ["Sophia Al-Farsi"]

        # User ID mapping: user_name → user_id
        self.user_id_map: Dict[str, str] = {}  # "Sophia Al-Farsi" → "cd3a350e-..."

        # Statistics
        self.total_users = 0
        self.ambiguous_parts: Set[str] = set()  # Parts shared by multiple users

        # Stop words to exclude from name matching (common query words)
        self.stop_words = {
            'has', 'have', 'had', 'who', 'what', 'when', 'where', 'why', 'how',
            'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'than',
            'this', 'that', 'these', 'those', 'for', 'to', 'from', 'by', 'at',
            'in', 'on', 'of', 'with', 'as', 'my', 'your', 'his', 'her', 'its',
            'our', 'their', 'me', 'you', 'him', 'she', 'it', 'we', 'they', 'us',
            'them', 'get', 'got', 'give', 'gave', 'make', 'made', 'take', 'took',
            'come', 'came', 'go', 'went', 'see', 'saw', 'know', 'knew', 'think',
            'thought', 'tell', 'told', 'ask', 'asked', 'work', 'worked', 'use',
            'used', 'find', 'found', 'give', 'given', 'call', 'called', 'try',
            'tried', 'need', 'needed', 'want', 'wanted', 'let', 'put', 'mean',
            'keep', 'kept', 'begin', 'began', 'seem', 'seemed', 'help', 'helped',
            'show', 'showed', 'hear', 'heard', 'play', 'played', 'run', 'ran',
            'move', 'moved', 'live', 'lived', 'believe', 'believed', 'bring',
            'brought', 'happen', 'happened', 'write', 'wrote', 'sit', 'sat',
            'stand', 'stood', 'lose', 'lost', 'pay', 'paid', 'meet', 'met',
            'include', 'included', 'continue', 'continued', 'set', 'learn',
            'learned', 'change', 'changed', 'lead', 'led', 'understand',
            'understood', 'watch', 'watched', 'follow', 'followed', 'stop',
            'stopped', 'create', 'created', 'speak', 'spoke', 'read', 'allow',
            'allowed', 'add', 'added', 'spend', 'spent', 'grow', 'grew', 'open',
            'opened', 'walk', 'walked', 'win', 'won', 'offer', 'offered', 'number'
        }

        # Load user_index if available
        self._load_user_index()

    def _load_user_index(self):
        """Load user_index.json to build user_name → user_id mapping"""
        user_index_path = "data/user_indexed/user_index.json"
        if os.path.exists(user_index_path):
            try:
                with open(user_index_path, 'r') as f:
                    user_index = json.load(f)

                # Build reverse mapping: user_name → user_id
                for user_id, data in user_index.items():
                    user_name = data['user_name']
                    self.user_id_map[user_name] = user_id

            except Exception as e:
                # Silent fail - user_id mapping is optional
                pass

    def get_user_id(self, user_name: str) -> Optional[str]:
        """
        Get user_id for a canonical user_name

        Args:
            user_name: Canonical full name (e.g., "Sophia Al-Farsi")

        Returns:
            user_id string or None if not found
        """
        return self.user_id_map.get(user_name)

    def resolve_with_id(self, query_name: str, fuzzy_threshold: float = 0.85) -> Optional[Tuple[str, str]]:
        """
        Resolve query name to (user_name, user_id) tuple

        Args:
            query_name: Name to resolve
            fuzzy_threshold: Similarity threshold for fuzzy matching

        Returns:
            (user_name, user_id) tuple or None if no match
        """
        user_name = self.resolve(query_name, fuzzy_threshold)
        if user_name:
            user_id = self.get_user_id(user_name)
            if user_id:
                return (user_name, user_id)
        return None

    def add_user(self, full_name: str):
        """
        Index a user by their full name and all name parts

        Args:
            full_name: Full user name (e.g., "Sophia Al-Farsi")
        """
        if not full_name or not full_name.strip():
            return

        full_name = full_name.strip()
        normalized = self._normalize(full_name)

        # Add to canonical index
        self.canonical_names[normalized] = full_name
        self.total_users += 1

        # Index all name parts
        parts = self._extract_name_parts(full_name)
        for part in parts:
            part_norm = self._normalize(part)

            if part_norm not in self.name_parts_index:
                self.name_parts_index[part_norm] = []

            # Add full name if not already there
            if full_name not in self.name_parts_index[part_norm]:
                self.name_parts_index[part_norm].append(full_name)

                # Track if this part becomes ambiguous
                if len(self.name_parts_index[part_norm]) > 1:
                    self.ambiguous_parts.add(part_norm)

    def _normalize(self, text: str) -> str:
        """
        Normalize text for matching (lowercase, strip, clean spaces)

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        return re.sub(r'\s+', ' ', text.lower().strip())

    def _extract_name_parts(self, full_name: str) -> List[str]:
        """
        Extract all matchable parts from a full name

        Examples:
            "Sophia Al-Farsi" → ["Sophia", "Al-Farsi", "Al", "Farsi"]
            "Hans Müller" → ["Hans", "Müller"]

        Args:
            full_name: Full user name

        Returns:
            List of name parts
        """
        parts = []

        # Split by spaces
        words = full_name.split()

        for word in words:
            # Add the word itself
            if len(word) > 1:  # Skip single letters
                parts.append(word)

            # If hyphenated, also add sub-parts
            if '-' in word:
                sub_parts = word.split('-')
                for sub in sub_parts:
                    if len(sub) > 1:
                        parts.append(sub)

        return parts

    def resolve(self, query_name: str, fuzzy_threshold: float = 0.85) -> Optional[str]:
        """
        Resolve a query name to canonical full name

        Resolution order:
        1. Stop word check (skip common query words)
        2. Exact match (full name)
        3. Partial match (name part)
        4. Fuzzy match (typo tolerance)

        Args:
            query_name: Name to resolve (e.g., "Sophia", "Al-Farsi", "sofia")
            fuzzy_threshold: Similarity threshold for fuzzy matching (0.0-1.0)

        Returns:
            Canonical full name or None if no match
        """
        if not query_name or not query_name.strip():
            return None

        query_norm = self._normalize(query_name)

        # 0. Stop word check - skip common query words
        if query_norm in self.stop_words:
            return None

        # Additional safety: require minimum length of 3 characters
        # This prevents matching "Al", "El", "De", "La" which are common prefixes
        # Unless they're exact matches in our index
        if len(query_norm) < 3 and query_norm not in self.name_parts_index:
            return None

        # 1. Exact match (full name)
        if query_norm in self.canonical_names:
            return self.canonical_names[query_norm]

        # 2. Partial match (name part)
        if query_norm in self.name_parts_index:
            matches = self.name_parts_index[query_norm]
            if len(matches) == 1:
                return matches[0]  # Unique match
            # Ambiguous - return first (could be enhanced to return all)
            return matches[0]

        # 3. Fuzzy match (typo tolerance)
        fuzzy_match = self._fuzzy_match(query_norm, fuzzy_threshold)
        if fuzzy_match:
            return fuzzy_match

        return None

    def resolve_all(self, query_name: str, fuzzy_threshold: float = 0.85) -> List[str]:
        """
        Resolve query name to ALL matching canonical names (for ambiguous cases)

        Args:
            query_name: Name to resolve
            fuzzy_threshold: Similarity threshold for fuzzy matching

        Returns:
            List of all matching full names (empty if none)
        """
        if not query_name or not query_name.strip():
            return []

        query_norm = self._normalize(query_name)

        # 1. Exact match
        if query_norm in self.canonical_names:
            return [self.canonical_names[query_norm]]

        # 2. Partial match (return all matches)
        if query_norm in self.name_parts_index:
            return self.name_parts_index[query_norm].copy()

        # 3. Fuzzy match
        fuzzy_match = self._fuzzy_match(query_norm, fuzzy_threshold)
        if fuzzy_match:
            return [fuzzy_match]

        return []

    def _fuzzy_match(self, query_norm: str, threshold: float = 0.85) -> Optional[str]:
        """
        Find best fuzzy match using string similarity

        Fuzzy matching requirements:
        - Query must be at least 4 characters (prevents short word false positives)
        - OR first letter must match (allows typos in longer names)
        - Similarity must be >= threshold

        Args:
            query_norm: Normalized query string
            threshold: Minimum similarity score (0.0-1.0)

        Returns:
            Best matching full name or None
        """
        # Safety: only do fuzzy matching for queries >= 4 characters
        # This prevents "has" from matching "hans", "who" from matching name parts, etc.
        if len(query_norm) < 4:
            return None

        best_match = None
        best_score = 0.0

        # Check against all canonical names
        for norm_name, full_name in self.canonical_names.items():
            # Require first letter match for stricter fuzzy matching
            if query_norm[0] != norm_name[0]:
                continue

            similarity = SequenceMatcher(None, query_norm, norm_name).ratio()
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = full_name

        # Also check against name parts
        for part_norm, full_names in self.name_parts_index.items():
            # Require first letter match for stricter fuzzy matching
            if query_norm[0] != part_norm[0]:
                continue

            similarity = SequenceMatcher(None, query_norm, part_norm).ratio()
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = full_names[0]  # Take first if ambiguous

        return best_match

    def is_ambiguous(self, query_name: str) -> bool:
        """
        Check if a query name is ambiguous (matches multiple users)

        Args:
            query_name: Name to check

        Returns:
            True if matches multiple users
        """
        query_norm = self._normalize(query_name)

        if query_norm in self.name_parts_index:
            return len(self.name_parts_index[query_norm]) > 1

        return False

    def get_statistics(self) -> Dict:
        """
        Get resolver statistics

        Returns:
            Statistics dictionary
        """
        return {
            'total_users': self.total_users,
            'total_name_parts': len(self.name_parts_index),
            'ambiguous_parts': len(self.ambiguous_parts),
            'ambiguous_examples': list(self.ambiguous_parts)[:10]
        }

    def list_all_users(self) -> List[str]:
        """
        Get all canonical user names

        Returns:
            List of all full names
        """
        return list(self.canonical_names.values())


def test_name_resolver():
    """Test name resolver functionality"""
    print("="*80)
    print("NAME RESOLVER TEST")
    print("="*80)

    # Create resolver
    resolver = NameResolver()

    # Add test users
    test_users = [
        "Sophia Al-Farsi",
        "Hans Müller",
        "Vikram Desai",
        "Layla Kawaguchi",
        "Armand Dupont",
        "Lily O'Sullivan",
        "Lorenzo Cavalli",
        "Thiago Monteiro",
        "Amina Van Den Berg",
        "Fatima El-Tahir"
    ]

    print("\n📋 Adding users to resolver...")
    for user in test_users:
        resolver.add_user(user)

    stats = resolver.get_statistics()
    print(f"✅ Added {stats['total_users']} users")
    print(f"   Name parts indexed: {stats['total_name_parts']}")
    print(f"   Ambiguous parts: {stats['ambiguous_parts']}")

    # Test cases
    test_cases = [
        # Exact matches
        ("Sophia Al-Farsi", "Sophia Al-Farsi", "Exact full name"),
        ("sophia al-farsi", "Sophia Al-Farsi", "Case insensitive"),

        # Partial matches - first name
        ("Sophia", "Sophia Al-Farsi", "First name only"),
        ("Hans", "Hans Müller", "First name only"),
        ("Vikram", "Vikram Desai", "First name only"),

        # Partial matches - last name
        ("Al-Farsi", "Sophia Al-Farsi", "Last name (hyphenated)"),
        ("Müller", "Hans Müller", "Last name with umlaut"),
        ("Desai", "Vikram Desai", "Last name only"),

        # Partial matches - hyphenated parts
        ("Al", "Sophia Al-Farsi", "Hyphen first part"),
        ("Farsi", "Sophia Al-Farsi", "Hyphen second part"),

        # Case variations
        ("SOPHIA", "Sophia Al-Farsi", "Uppercase"),
        ("sophia", "Sophia Al-Farsi", "Lowercase"),
        ("SoPhIa", "Sophia Al-Farsi", "Mixed case"),

        # Fuzzy matches (typos)
        ("Sofya", "Sophia Al-Farsi", "Typo: Sofya → Sophia"),
        ("Vikam", "Vikram Desai", "Typo: Vikam → Vikram"),
        ("Muller", "Hans Müller", "Typo: Muller → Müller"),

        # Should not match
        ("John", None, "Non-existent name"),
        ("Smith", None, "Non-existent name"),
    ]

    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)

    passed = 0
    failed = 0

    for query, expected, description in test_cases:
        result = resolver.resolve(query)

        if result == expected:
            print(f"✅ PASS: '{query}' → '{result}' ({description})")
            passed += 1
        else:
            print(f"❌ FAIL: '{query}' → '{result}' (expected '{expected}') ({description})")
            failed += 1

    # Test ambiguity detection
    print("\n" + "="*80)
    print("AMBIGUITY TEST")
    print("="*80)

    # Add a user with overlapping name
    resolver.add_user("Sophie Anderson")  # "Sophie" might match "Sophia"

    print("\nChecking ambiguous matches:")
    ambiguous_queries = ["sophia", "sophie"]
    for query in ambiguous_queries:
        is_amb = resolver.is_ambiguous(query)
        all_matches = resolver.resolve_all(query)
        print(f"  '{query}': {'Ambiguous' if is_amb else 'Unique'} → {all_matches}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n✅ Passed: {passed}/{passed + failed}")
    print(f"❌ Failed: {failed}/{passed + failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("   ✅ Exact matching")
        print("   ✅ Partial matching")
        print("   ✅ Case insensitive")
        print("   ✅ Fuzzy matching (typos)")
        print("   ✅ Ambiguity detection")

    print("\n" + "="*80)


if __name__ == "__main__":
    test_name_resolver()
