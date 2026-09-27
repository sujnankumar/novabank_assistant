"""
NovaBank Structured Transaction Query Parser & Date Resolver
============================================================
Extracts structured parameters (limit, date range, canonical category, account ID)
deterministically from natural-language queries.
Enforces default limit (5) and safety cap (100) server-side.
Customer identity MUST always be provided from trusted application context.
"""

import calendar
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_TRANSACTION_LIMIT: int = 5
MAX_TRANSACTION_LIMIT: int = 100

CANONICAL_CATEGORIES: List[str] = [
    "ATM",
    "Bills",
    "Education",
    "Entertainment",
    "Food",
    "Healthcare",
    "Insurance",
    "Other",
    "Salary",
    "Shopping",
    "Transfer",
    "Travel",
    "Utilities",
]

CATEGORY_KEYWORD_MAP: Dict[str, str] = {
    # Food & Dining
    "food": "Food",
    "dining": "Food",
    "restaurant": "Food",
    "restaurants": "Food",
    "groceries": "Food",
    "grocery": "Food",
    "swiggy": "Food",
    "zomato": "Food",
    "eat": "Food",
    "cafe": "Food",
    # Travel
    "travel": "Travel",
    "flight": "Travel",
    "flights": "Travel",
    "airline": "Travel",
    "airlines": "Travel",
    "hotel": "Travel",
    "hotels": "Travel",
    "uber": "Travel",
    "ola": "Travel",
    "train": "Travel",
    "railway": "Travel",
    "irctc": "Travel",
    "trip": "Travel",
    "trips": "Travel",
    # Shopping
    "shopping": "Shopping",
    "clothes": "Shopping",
    "apparel": "Shopping",
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "myntra": "Shopping",
    "store": "Shopping",
    "purchase": "Shopping",
    "purchases": "Shopping",
    # Entertainment
    "entertainment": "Entertainment",
    "movie": "Entertainment",
    "movies": "Entertainment",
    "cinema": "Entertainment",
    "netflix": "Entertainment",
    "prime": "Entertainment",
    "hotstar": "Entertainment",
    "spotify": "Entertainment",
    "concert": "Entertainment",
    "shows": "Entertainment",
    # Bills
    "bills": "Bills",
    "bill": "Bills",
    "electricity": "Bills",
    "water": "Bills",
    "gas bill": "Bills",
    "utility bill": "Bills",
    "mobile bill": "Bills",
    "recharge": "Bills",
    "broadband": "Bills",
    "wifi": "Bills",
    "postpaid": "Bills",
    # Utilities
    "utilities": "Utilities",
    "utility": "Utilities",
    # Healthcare
    "healthcare": "Healthcare",
    "health": "Healthcare",
    "medical": "Healthcare",
    "pharmacy": "Healthcare",
    "medicine": "Healthcare",
    "medicines": "Healthcare",
    "hospital": "Healthcare",
    "doctor": "Healthcare",
    "clinic": "Healthcare",
    "apollo": "Healthcare",
    # Education
    "education": "Education",
    "tuition": "Education",
    "school": "Education",
    "college": "Education",
    "university": "Education",
    "course": "Education",
    "fees": "Education",
    "books": "Education",
    "student": "Education",
    # Insurance
    "insurance": "Insurance",
    "lic": "Insurance",
    "policy premium": "Insurance",
    "premium": "Insurance",
    "health insurance": "Insurance",
    "life insurance": "Insurance",
    # ATM
    "atm": "ATM",
    "cash withdrawal": "ATM",
    "atm withdrawal": "ATM",
    "cash": "ATM",
    # Salary
    "salary": "Salary",
    "payroll": "Salary",
    "stipend": "Salary",
    "paycheck": "Salary",
    # Transfer
    "transfer": "Transfer",
    "transfers": "Transfer",
    "upi transfer": "Transfer",
    "neft": "Transfer",
    "rtgs": "Transfer",
    "imps": "Transfer",
    "sent money": "Transfer",
    "wire": "Transfer",
    # Other
    "other": "Other",
    "miscellaneous": "Other",
}

WORD_NUMBERS: Dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "fifteen": 15,
    "twenty": 20,
    "twenty-five": 25,
    "thirty": 30,
    "fifty": 50,
    "hundred": 100,
}

MONTH_NAMES: Dict[str, int] = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


def extract_limit(query: str) -> Tuple[int, bool, Optional[int]]:
    """
    Extracts explicit transaction limit or falls back to DEFAULT_TRANSACTION_LIMIT.
    Enforces MAX_TRANSACTION_LIMIT safety cap.

    Returns:
        (effective_limit: int, was_capped: bool, original_requested: Optional[int])
    """
    q_lower = query.lower().replace(",", "")

    # 1. Digits followed by or near transaction patterns
    patterns = [
        r"\b(\d+)\s*(?:most\s*)?(?:recent\s*)?(?:past\s*)?(?:latest\s*)?(?:[\w\s]+\s+)?transactions?\b",
        r"(?:show|give|display|fetch|get|list|see)(?:\s+me)?(?:\s+my)?\s+(\d+)\b",
        r"\blast\s+(\d+)\b",
        r"\b(\d+)\s+transactions?\b",
    ]
    for pat in patterns:
        m = re.search(pat, q_lower)
        if m:
            val = int(m.group(1))
            if val > MAX_TRANSACTION_LIMIT:
                return MAX_TRANSACTION_LIMIT, True, val
            return max(1, val), False, val

    # 2. Check written number words
    for word, num in sorted(WORD_NUMBERS.items(), key=lambda x: -len(x[0])):
        pat = rf"\b{word}\s*(?:most\s*)?(?:recent\s*)?(?:past\s*)?(?:latest\s*)?(?:[\w\s]+\s+)?transactions?\b"
        if re.search(pat, q_lower):
            if num > MAX_TRANSACTION_LIMIT:
                return MAX_TRANSACTION_LIMIT, True, num
            return max(1, num), False, num

        pat2 = rf"(?:show|give|display|fetch|get|list)(?:\s+me)?(?:\s+my)?\s+{word}\b"
        if re.search(pat2, q_lower):
            if num > MAX_TRANSACTION_LIMIT:
                return MAX_TRANSACTION_LIMIT, True, num
            return max(1, num), False, num

    return DEFAULT_TRANSACTION_LIMIT, False, None


def extract_category(query: str) -> Optional[str]:
    """
    Matches query against canonical transaction categories using keyword mapping.
    """
    q_lower = query.lower()
    for phrase, canon in sorted(CATEGORY_KEYWORD_MAP.items(), key=lambda x: -len(x[0])):
        pattern = rf"\b{re.escape(phrase)}s?\b"
        if re.search(pattern, q_lower):
            return canon
    return None


def extract_account_id(query: str) -> Optional[str]:
    """
    Extracts explicit account ID if mentioned in the query (e.g. ACC001).
    """
    m = re.search(r"\b(acc\d{3})\b", query, flags=re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return None


def resolve_date_range(
    query: str,
    ref_date: Optional[datetime] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Resolves natural-language date phrases into deterministic YYYY-MM-DD bounds.

    Returns:
        (start_date: Optional[str], end_date: Optional[str], label: Optional[str])
    """
    ref = ref_date or datetime.now()
    q_lower = query.lower()

    # A. This month: 1st of current month through reference date
    if "this month" in q_lower or "current month" in q_lower:
        start_date = ref.replace(day=1).strftime("%Y-%m-%d")
        end_date = ref.strftime("%Y-%m-%d")
        label = f"this month ({ref.strftime('%B %Y')})"
        return start_date, end_date, label

    # B. Last month: 1st to last day of previous calendar month
    if "last month" in q_lower or "previous month" in q_lower or "past month" in q_lower:
        if ref.month == 1:
            prev_year = ref.year - 1
            prev_month = 12
        else:
            prev_year = ref.year
            prev_month = ref.month - 1
        _, last_day = calendar.monthrange(prev_year, prev_month)
        start_date = f"{prev_year:04d}-{prev_month:02d}-01"
        end_date = f"{prev_year:04d}-{prev_month:02d}-{last_day:02d}"
        month_name = calendar.month_name[prev_month]
        label = f"last month ({month_name} {prev_year})"
        return start_date, end_date, label

    # C. This year: Jan 1 of current year through reference date
    if "this year" in q_lower or "current year" in q_lower:
        start_date = f"{ref.year:04d}-01-01"
        end_date = ref.strftime("%Y-%m-%d")
        label = f"this year ({ref.year})"
        return start_date, end_date, label

    # D. Last year: Jan 1 of previous year through Dec 31 of previous year
    if "last year" in q_lower or "previous year" in q_lower:
        prev_year = ref.year - 1
        start_date = f"{prev_year:04d}-01-01"
        end_date = f"{prev_year:04d}-{12:02d}-31"
        label = f"last year ({prev_year})"
        return start_date, end_date, label

    # G1. Day-month range: e.g. "from 1 August to 15 August" or "between 1 August and 15 August"
    m_day_range = re.search(
        r"\b(?:from|between)\s+(\d{1,2})\s+([a-z]+)\s+(?:to|and)\s+(\d{1,2})\s+([a-z]+)(?:\s+(\d{4}))?\b",
        q_lower,
    )
    if m_day_range:
        d1 = int(m_day_range.group(1))
        m1_name = m_day_range.group(2)
        d2 = int(m_day_range.group(3))
        m2_name = m_day_range.group(4)
        yr_str = m_day_range.group(5)
        if m1_name in MONTH_NAMES and m2_name in MONTH_NAMES:
            mo1 = MONTH_NAMES[m1_name]
            mo2 = MONTH_NAMES[m2_name]
            yr = int(yr_str) if yr_str else ref.year
            start_date = f"{yr:04d}-{mo1:02d}-{d1:02d}"
            end_date = f"{yr:04d}-{mo2:02d}-{d2:02d}"
            return start_date, end_date, f"{d1} {m1_name.title()} - {d2} {m2_name.title()} {yr}"

    # G2. Month day range: e.g. "between June 1 and June 30" or "from June 1 to June 30"
    m_range2 = re.search(
        r"\b(?:from|between)\s+([a-z]+)\s+(\d{1,2})\s+(?:to|and)\s+(?:[a-z]+\s+)?(\d{1,2})(?:\s+(\d{4}))?\b",
        q_lower,
    )
    if m_range2:
        m_name = m_range2.group(1)
        d1 = int(m_range2.group(2))
        d2 = int(m_range2.group(3))
        yr_str = m_range2.group(4)
        if m_name in MONTH_NAMES:
            mo = MONTH_NAMES[m_name]
            yr = int(yr_str) if yr_str else ref.year
            start_date = f"{yr:04d}-{mo:02d}-{d1:02d}"
            end_date = f"{yr:04d}-{mo:02d}-{d2:02d}"
            return start_date, end_date, f"{m_name.title()} {d1} - {d2}, {yr}"

    # G3. Month range: e.g. "from June to August" or "between June and August"
    m_mo_range = re.search(
        r"\b(?:from|between)\s+([a-z]+)\s+(?:to|and)\s+([a-z]+)(?:\s+(\d{4}))?\b",
        q_lower,
    )
    if m_mo_range:
        m1_name = m_mo_range.group(1)
        m2_name = m_mo_range.group(2)
        yr_str = m_mo_range.group(3)
        if m1_name in MONTH_NAMES and m2_name in MONTH_NAMES:
            mo1 = MONTH_NAMES[m1_name]
            mo2 = MONTH_NAMES[m2_name]
            yr = int(yr_str) if yr_str else ref.year
            _, last_d2 = calendar.monthrange(yr, mo2)
            start_date = f"{yr:04d}-{mo1:02d}-01"
            end_date = f"{yr:04d}-{mo2:02d}-{last_d2:02d}"
            return start_date, end_date, f"{m1_name.title()} to {m2_name.title()} {yr}"

    # F. Specific month + year: e.g. "August 2025" or "in Aug 2025"
    m_mo_yr = re.search(r"\b([a-z]+)\s+(\d{4})\b", q_lower)
    if m_mo_yr:
        m_name = m_mo_yr.group(1)
        yr = int(m_mo_yr.group(2))
        if m_name in MONTH_NAMES:
            mo = MONTH_NAMES[m_name]
            _, last_day = calendar.monthrange(yr, mo)
            start_date = f"{yr:04d}-{mo:02d}-01"
            end_date = f"{yr:04d}-{mo:02d}-{last_day:02d}"
            return start_date, end_date, f"{calendar.month_name[mo]} {yr}"

    # E. Specific month without year: e.g. "in August", "for August", "August transactions"
    for m_name, mo in MONTH_NAMES.items():
        pat = rf"\b(?:in|for|of|during)\s+{m_name}\b|\b{m_name}\s+(?:transactions?|activity|spending)\b"
        if re.search(pat, q_lower):
            # If month <= current month, use current year; else use previous year
            if mo <= ref.month:
                yr = ref.year
            else:
                yr = ref.year - 1
            _, last_day = calendar.monthrange(yr, mo)
            start_date = f"{yr:04d}-{mo:02d}-01"
            end_date = f"{yr:04d}-{mo:02d}-{last_day:02d}"
            return start_date, end_date, f"{calendar.month_name[mo]} {yr}"

    return None, None, None


def parse_transaction_query(
    query: str,
    customer_id: Optional[str] = None,
    ref_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Parses a user query into structured transaction parameters.

    Returns dict with keys:
        - customer_id: Optional[str] (strictly preserved from trusted context)
        - limit: int (default 5, capped at 100)
        - category: Optional[str] (canonical category name)
        - start_date: Optional[str] (YYYY-MM-DD)
        - end_date: Optional[str] (YYYY-MM-DD)
        - account_id: Optional[str] (e.g. ACC001)
        - sort: str ("desc")
        - date_label: Optional[str] (human readable label for filters)
        - was_capped: bool (True if user asked for > 100)
        - original_limit: Optional[int] (requested limit before safety cap)
    """
    limit, was_capped, original_limit = extract_limit(query)
    category = extract_category(query)
    start_date, end_date, date_label = resolve_date_range(query, ref_date=ref_date)
    account_id = extract_account_id(query)

    return {
        "customer_id": customer_id,
        "limit": limit,
        "category": category,
        "start_date": start_date,
        "end_date": end_date,
        "account_id": account_id,
        "sort": "desc",
        "date_label": date_label,
        "was_capped": was_capped,
        "original_limit": original_limit,
    }
