"""
NovaBank Query Preprocessor
============================
Reads customer_query_logs.txt, parses each entry, tokenizes the query text,
loads intent labels from query_labels.json, and produces processed_queries.json.

Uses a simple regex-based tokenizer — no external NLP dependencies required.

Usage:
  python scripts/preprocess_queries.py
"""

import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def parse_query_log(filepath):
    """
    Parse customer_query_logs.txt.
    
    Expected format per line:
      2026-09-01 09:15:21 | customer=CUST001 | What is my current account balance?
    
    Returns a list of dicts with keys: query_id, timestamp, customer_id, query.
    """
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            parts = line.split(" | ")
            if len(parts) < 3:
                print(f"  WARNING: Skipping malformed line {idx}: {line[:60]}...")
                continue

            timestamp = parts[0].strip()
            customer_part = parts[1].strip()
            query = " | ".join(parts[2:]).strip()  # Handle queries with | in them

            # Extract customer ID
            match = re.match(r"customer=(\w+)", customer_part)
            if not match:
                print(f"  WARNING: Cannot parse customer ID on line {idx}")
                continue

            customer_id = match.group(1)

            entries.append({
                "query_id": f"Q{idx:03d}",
                "timestamp": timestamp,
                "customer_id": customer_id,
                "query": query
            })

    return entries


def tokenize(text):
    """
    Simple tokenizer: lowercases text, removes punctuation, splits on whitespace.
    Returns a list of token strings.
    """
    # Lowercase
    text = text.lower()
    # Remove punctuation (keep apostrophes within words like "what's")
    text = re.sub(r"[^\w\s']", "", text)
    # Remove standalone apostrophes and split contractions
    text = re.sub(r"'s\b", "", text)  # Remove possessive 's
    text = re.sub(r"'\b|\b'", "", text)  # Remove leading/trailing apostrophes
    # Split on whitespace and filter empty
    tokens = [t for t in text.split() if t]
    return tokens


def load_labels(filepath):
    """Load query labels from JSON file and return as dict keyed by query_id."""
    with open(filepath, "r", encoding="utf-8") as f:
        labels = json.load(f)
    return {label["query_id"]: label for label in labels}


def main():
    print("=" * 60)
    print("NovaBank Query Preprocessor")
    print("=" * 60)
    print()

    # File paths
    log_path = os.path.join(DATA_DIR, "customer_query_logs.txt")
    labels_path = os.path.join(DATA_DIR, "query_labels.json")
    output_path = os.path.join(DATA_DIR, "processed_queries.json")

    # Check input files exist
    for path, name in [(log_path, "customer_query_logs.txt"), (labels_path, "query_labels.json")]:
        if not os.path.exists(path):
            print(f"ERROR: {name} not found at {path}")
            print("Please run generate_data.py first.")
            return

    # Parse query logs
    print("Parsing customer_query_logs.txt...")
    entries = parse_query_log(log_path)
    print(f"  Parsed {len(entries)} query entries.")

    # Load labels
    print("Loading query_labels.json...")
    labels = load_labels(labels_path)
    print(f"  Loaded {len(labels)} intent labels.")

    # Process each query
    print("Tokenizing and labeling queries...")
    processed = []
    unmatched = 0

    for entry in entries:
        qid = entry["query_id"]
        tokens = tokenize(entry["query"])

        # Look up intent label
        label_info = labels.get(qid)
        intent = label_info["intent"] if label_info else "UNKNOWN_QUERY"
        if not label_info:
            unmatched += 1

        processed.append({
            "query_id": qid,
            "customer_id": entry["customer_id"],
            "timestamp": entry["timestamp"],
            "query": entry["query"],
            "tokens": tokens,
            "intent": intent
        })

    # Save output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    print("Preprocessing Summary")
    print("=" * 60)
    print(f"  Total queries processed: {len(processed)}")
    print(f"  Queries with intent labels: {len(processed) - unmatched}")
    print(f"  Queries without labels: {unmatched}")
    print(f"  Output saved to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
