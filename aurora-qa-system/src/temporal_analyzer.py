"""
Temporal Query Analyzer

Extracts date ranges from user queries.

Examples:
- "December 2025" → ("2025-12-01", "2025-12-31")
- "Q4 2024" → ("2024-10-01", "2024-12-31")
- "next month" → (calculated based on current date)

Usage:
    analyzer = TemporalAnalyzer()
    date_range = analyzer.extract_date_range("plans for December 2025")
    # Returns: ("2025-12-01", "2025-12-31")
"""
import re
import calendar
from datetime import datetime, timedelta
from typing import Optional, Tuple
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import datefinder


class TemporalAnalyzer:
    """Extract date ranges from queries"""

    def extract_date_range(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Extract date range from query

        Args:
            query: User query

        Returns:
            (start_date, end_date) in ISO format or None

        Examples:
            "December 2025" → ("2025-12-01", "2025-12-31")
            "Q4 2024" → ("2024-10-01", "2024-12-31")
            "next month" → (start of next month, end of next month)
        """
        query_lower = query.lower()

        # Strategy 1: Quarter patterns (Q1, Q2, Q3, Q4)
        quarter_range = self._extract_quarter_range(query_lower)
        if quarter_range:
            return quarter_range

        # Strategy 2: Use datefinder to extract dates
        dates = list(datefinder.find_dates(query))
        if dates:
            # Get month range for first date found
            first_date = dates[0]
            return self._get_month_range(first_date)

        # Strategy 3: Relative dates
        relative_range = self._extract_relative_range(query_lower)
        if relative_range:
            return relative_range

        return None

    def _extract_quarter_range(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Extract quarter date range

        Examples:
            "Q4 2024" → ("2024-10-01", "2024-12-31")
            "q1" → (Q1 of current year)
        """
        # Match "Q1", "Q2", "Q3", "Q4" with optional year
        match = re.search(r'q([1-4])(?:\s*(\d{4}))?', query)
        if not match:
            return None

        quarter = int(match.group(1))
        year = int(match.group(2)) if match.group(2) else datetime.now().year

        # Map quarters to month ranges
        quarter_months = {
            1: (1, 3),   # Jan-Mar
            2: (4, 6),   # Apr-Jun
            3: (7, 9),   # Jul-Sep
            4: (10, 12)  # Oct-Dec
        }

        start_month, end_month = quarter_months[quarter]

        # Start: First day of first month
        start_date = datetime(year, start_month, 1)

        # End: Last day of last month
        last_day = calendar.monthrange(year, end_month)[1]
        end_date = datetime(year, end_month, last_day)

        return (start_date.date().isoformat(), end_date.date().isoformat())

    def _get_month_range(self, date: datetime) -> Tuple[str, str]:
        """
        Get first and last day of month

        Args:
            date: Any datetime in the target month

        Returns:
            (first_day, last_day) in ISO format
        """
        # First day
        first = date.replace(day=1)

        # Last day
        last_day = calendar.monthrange(date.year, date.month)[1]
        last = date.replace(day=last_day)

        return (first.date().isoformat(), last.date().isoformat())

    def _extract_relative_range(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Extract relative date ranges

        Examples:
            "next month" → next month's date range
            "this month" → current month's date range
        """
        now = datetime.now()

        # Next month
        if 'next month' in query:
            next_month = now + relativedelta(months=1)
            return self._get_month_range(next_month)

        # This month
        if 'this month' in query:
            return self._get_month_range(now)

        # Next week
        if 'next week' in query:
            next_week_start = now + timedelta(days=7 - now.weekday())
            next_week_end = next_week_start + timedelta(days=6)
            return (next_week_start.date().isoformat(), next_week_end.date().isoformat())

        # This week
        if 'this week' in query:
            week_start = now - timedelta(days=now.weekday())
            week_end = week_start + timedelta(days=6)
            return (week_start.date().isoformat(), week_end.date().isoformat())

        return None


def test_temporal_analyzer():
    """Test temporal query analyzer"""
    print("="*80)
    print("TEMPORAL ANALYZER TEST")
    print("="*80)

    analyzer = TemporalAnalyzer()

    test_cases = [
        "Which clients have plans for December 2025?",
        "Q4 2024 bookings",
        "Show me reservations for next month",
        "Plans in January",
        "Q1 trips",
        "No dates in this query"
    ]

    for query in test_cases:
        date_range = analyzer.extract_date_range(query)
        print(f"\nQuery: {query}")
        if date_range:
            print(f"  → Range: {date_range[0]} to {date_range[1]}")
        else:
            print(f"  → No date range detected")

    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    test_temporal_analyzer()
