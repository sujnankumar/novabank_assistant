"""
NovaBank Data Validator
========================
Validates referential integrity, uniqueness, and completeness across all
generated synthetic banking datasets.

Checks performed:
  - Customer ID uniqueness
  - Account ID uniqueness
  - Transaction ID uniqueness
  - Account → Customer referential integrity
  - Transaction → Account referential integrity
  - Transaction customer_id matches account customer_id
  - Loan product required fields
  - Query customer IDs exist in customers.json
  - Every query has an intent label
  - Every query log entry has a corresponding query_labels.json entry
  - processed_queries.json alignment

Usage:
  python scripts/validate_data.py
"""

import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


class ValidationReport:
    """Tracks validation checks and results."""

    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def check(self, name, condition, detail=""):
        """Record a validation check."""
        if condition:
            self.checks.append(("PASS", name, detail))
            self.passed += 1
        else:
            self.checks.append(("FAIL", name, detail))
            self.failed += 1

    def warn(self, name, detail=""):
        """Record a warning (non-fatal)."""
        self.checks.append(("WARN", name, detail))
        self.warnings += 1

    def print_report(self):
        """Print the full validation report."""
        print()
        print("=" * 70)
        print("VALIDATION REPORT")
        print("=" * 70)
        print()

        for status, name, detail in self.checks:
            icon = {"PASS": "[OK]", "FAIL": "[X]", "WARN": "[!]"}[status]
            color_label = {"PASS": "PASS", "FAIL": "FAIL", "WARN": "WARN"}[status]
            line = f"  [{color_label}] {icon} {name}"
            if detail:
                line += f" -- {detail}"
            print(line)

        print()
        print("-" * 70)
        print(f"  Total checks: {self.passed + self.failed + self.warnings}")
        print(f"  Passed:       {self.passed}")
        print(f"  Failed:       {self.failed}")
        print(f"  Warnings:     {self.warnings}")
        print("-" * 70)

        if self.failed == 0:
            print("  [OK] ALL REFERENTIAL INTEGRITY CHECKS PASSED")
        else:
            print(f"  [X] {self.failed} CHECK(S) FAILED -- review details above")

        print("=" * 70)


def load_json(filename):
    """Load a JSON file from the data directory."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_text_lines(filename):
    """Load a text file and return non-empty lines."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def main():
    print("=" * 70)
    print("NovaBank Data Validator")
    print("=" * 70)

    report = ValidationReport()

    # ── Load all datasets ──────────────────────────────
    customers = load_json("customers.json")
    accounts = load_json("accounts.json")
    transactions = load_json("transactions.json")
    loans = load_json("loans.json")
    products = load_json("products.json")
    profiles = load_json("customer_profiles.json")
    labels = load_json("query_labels.json")
    processed = load_json("processed_queries.json")
    query_lines = load_text_lines("customer_query_logs.txt")

    # ── Check file existence ───────────────────────────
    datasets = {
        "customers.json": customers,
        "accounts.json": accounts,
        "transactions.json": transactions,
        "loans.json": loans,
        "products.json": products,
        "customer_profiles.json": profiles,
        "query_labels.json": labels,
        "processed_queries.json": processed,
        "customer_query_logs.txt": query_lines,
    }

    print("\nChecking file existence...")
    for name, data in datasets.items():
        report.check(f"File exists: {name}", data is not None,
                     f"NOT FOUND" if data is None else f"{len(data)} records")

    # Abort if critical files missing
    if any(v is None for v in [customers, accounts, transactions, loans]):
        report.print_report()
        return

    # ── 1. Customer ID uniqueness ──────────────────────
    print("Validating customers...")
    cust_ids = [c["customer_id"] for c in customers]
    cust_id_set = set(cust_ids)
    report.check("Customer IDs are unique",
                 len(cust_ids) == len(cust_id_set),
                 f"{len(cust_ids)} IDs, {len(cust_id_set)} unique")

    # Required fields
    required_cust_fields = ["customer_id", "name", "age", "gender", "city",
                            "occupation", "monthly_income", "credit_score", "consent"]
    all_fields_ok = all(
        all(f in c for f in required_cust_fields) for c in customers
    )
    report.check("Customers have all required fields", all_fields_ok)

    # ── 2. Account ID uniqueness ───────────────────────
    print("Validating accounts...")
    acc_ids = [a["account_id"] for a in accounts]
    acc_id_set = set(acc_ids)
    report.check("Account IDs are unique",
                 len(acc_ids) == len(acc_id_set),
                 f"{len(acc_ids)} IDs, {len(acc_id_set)} unique")

    # Every account references an existing customer
    acc_cust_ids = set(a["customer_id"] for a in accounts)
    orphan_accounts = acc_cust_ids - cust_id_set
    report.check("Every account references an existing customer",
                 len(orphan_accounts) == 0,
                 f"Orphan customer IDs: {orphan_accounts}" if orphan_accounts else "")

    # Every customer has at least one account
    custs_with_accounts = set(a["customer_id"] for a in accounts)
    custs_without = cust_id_set - custs_with_accounts
    report.check("Every customer has at least one account",
                 len(custs_without) == 0,
                 f"Customers without accounts: {custs_without}" if custs_without else "")

    # Build account lookup
    acc_lookup = {a["account_id"]: a for a in accounts}

    # ── 3. Transaction ID uniqueness ───────────────────
    print("Validating transactions...")
    txn_ids = [t["transaction_id"] for t in transactions]
    txn_id_set = set(txn_ids)
    report.check("Transaction IDs are unique",
                 len(txn_ids) == len(txn_id_set),
                 f"{len(txn_ids)} IDs, {len(txn_id_set)} unique")

    # Every transaction references an existing account
    txn_acc_ids = set(t["account_id"] for t in transactions)
    orphan_txns = txn_acc_ids - acc_id_set
    report.check("Every transaction references an existing account",
                 len(orphan_txns) == 0,
                 f"Orphan account IDs: {orphan_txns}" if orphan_txns else "")

    # Transaction customer_id matches account customer_id
    mismatches = []
    for t in transactions:
        acc = acc_lookup.get(t["account_id"])
        if acc and t["customer_id"] != acc["customer_id"]:
            mismatches.append(t["transaction_id"])
    report.check("Transaction customer_id matches account customer_id",
                 len(mismatches) == 0,
                 f"{len(mismatches)} mismatches: {mismatches[:5]}..." if mismatches else "")

    # ── 4. Loan product validation ─────────────────────
    print("Validating loan products...")
    required_loan_fields = [
        "loan_id", "loan_name", "loan_type", "minimum_amount", "maximum_amount",
        "interest_rate", "minimum_income", "minimum_credit_score", "minimum_age",
        "maximum_age", "maximum_tenure_years", "processing_fee_percent", "required_documents"
    ]
    all_loan_fields_ok = all(
        all(f in l for f in required_loan_fields) for l in loans
    )
    report.check("Loan products have all required fields", all_loan_fields_ok)

    loan_ids = [l["loan_id"] for l in loans]
    report.check("Loan IDs are unique",
                 len(loan_ids) == len(set(loan_ids)),
                 f"{len(loan_ids)} IDs")

    # Check internal consistency: min_amount < max_amount, min_age < max_age
    consistency_ok = True
    for l in loans:
        if l["minimum_amount"] >= l["maximum_amount"]:
            consistency_ok = False
        if l["minimum_age"] >= l["maximum_age"]:
            consistency_ok = False
    report.check("Loan products are internally consistent (min < max)", consistency_ok)

    # ── 5. Banking products validation ─────────────────
    print("Validating banking products...")
    if products:
        prod_ids = [p["product_id"] for p in products]
        report.check("Product IDs are unique",
                     len(prod_ids) == len(set(prod_ids)),
                     f"{len(prod_ids)} IDs")

    # ── 6. Customer profiles validation ────────────────
    print("Validating customer profiles...")
    if profiles:
        profile_cust_ids = set(p["customer_id"] for p in profiles)
        orphan_profiles = profile_cust_ids - cust_id_set
        report.check("Every profile references an existing customer",
                     len(orphan_profiles) == 0,
                     f"Orphan: {orphan_profiles}" if orphan_profiles else "")

        missing_profiles = cust_id_set - profile_cust_ids
        report.check("Every customer has a profile",
                     len(missing_profiles) == 0,
                     f"Missing: {missing_profiles}" if missing_profiles else "")

    # ── 7. Query logs validation ───────────────────────
    print("Validating customer query logs...")
    if query_lines:
        # Parse customer IDs from query lines
        query_cust_ids = set()
        parse_errors = 0
        for line in query_lines:
            parts = line.split(" | ")
            if len(parts) >= 2:
                match = re.search(r"customer=(\w+)", parts[1])
                if match:
                    query_cust_ids.add(match.group(1))
                else:
                    parse_errors += 1
            else:
                parse_errors += 1

        report.check("Query log lines are parseable",
                     parse_errors == 0,
                     f"{parse_errors} parse errors" if parse_errors else f"{len(query_lines)} lines OK")

        orphan_query_custs = query_cust_ids - cust_id_set
        report.check("Every query customer ID exists in customers.json",
                     len(orphan_query_custs) == 0,
                     f"Orphan: {orphan_query_custs}" if orphan_query_custs else "")

    # ── 8. Intent labels validation ────────────────────
    print("Validating intent labels...")
    if labels and query_lines:
        report.check("Every query has an intent label",
                     len(labels) >= len(query_lines),
                     f"{len(labels)} labels for {len(query_lines)} queries")

        label_ids = set(l["query_id"] for l in labels)
        expected_qids = set(f"Q{i:03d}" for i in range(1, len(query_lines) + 1))
        missing_labels = expected_qids - label_ids
        report.check("Every query log has a corresponding label entry",
                     len(missing_labels) == 0,
                     f"Missing: {sorted(missing_labels)[:10]}..." if missing_labels else "")

        # Check valid intents
        valid_intents = {
            "CHECK_BALANCE", "ACCOUNT_DETAILS", "TRANSACTION_HISTORY",
            "TRANSACTION_SEARCH", "SPENDING_ANALYSIS", "MONTHLY_SPENDING",
            "CATEGORY_SPENDING", "MERCHANT_SPENDING", "LOAN_INFORMATION",
            "LOAN_ELIGIBILITY", "LOAN_INTEREST_RATE", "LOAN_DOCUMENTS",
            "CREDIT_CARD_INFORMATION", "SAVINGS_INFORMATION", "FD_INFORMATION",
            "BANKING_POLICY", "CUSTOMER_PROFILE", "GENERAL_BANKING_QUERY",
            "UNKNOWN_QUERY"
        }
        actual_intents = set(l["intent"] for l in labels)
        invalid_intents = actual_intents - valid_intents
        report.check("All intents are from the defined set",
                     len(invalid_intents) == 0,
                     f"Invalid intents: {invalid_intents}" if invalid_intents else "")

    # ── 9. Processed queries validation ────────────────
    print("Validating processed queries...")
    if processed:
        report.check("processed_queries.json has entries",
                     len(processed) > 0,
                     f"{len(processed)} entries")

        # Check required fields
        required_proc_fields = ["query_id", "customer_id", "query", "tokens", "intent"]
        all_proc_ok = all(
            all(f in p for f in required_proc_fields) for p in processed
        )
        report.check("Processed queries have all required fields", all_proc_ok)

        # Check tokens are lists
        tokens_ok = all(isinstance(p.get("tokens"), list) for p in processed)
        report.check("All token fields are lists", tokens_ok)

        # Check alignment with query logs
        if query_lines:
            report.check("Processed queries count matches query log count",
                         len(processed) == len(query_lines),
                         f"{len(processed)} processed vs {len(query_lines)} log lines")

    # ── Print final report ─────────────────────────────
    report.print_report()

    # ── Print data summary ─────────────────────────────
    print()
    print("=" * 70)
    print("DATA SUMMARY")
    print("=" * 70)
    print(f"  Customers:           {len(customers) if customers else 'N/A'}")
    print(f"  Accounts:            {len(accounts) if accounts else 'N/A'}")
    print(f"  Transactions:        {len(transactions) if transactions else 'N/A'}")
    print(f"  Loan Products:       {len(loans) if loans else 'N/A'}")
    print(f"  Banking Products:    {len(products) if products else 'N/A'}")
    print(f"  Customer Profiles:   {len(profiles) if profiles else 'N/A'}")
    print(f"  Customer Query Logs: {len(query_lines) if query_lines else 'N/A'}")
    print(f"  Labeled Queries:     {len(labels) if labels else 'N/A'}")
    print(f"  Processed Queries:   {len(processed) if processed else 'N/A'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
