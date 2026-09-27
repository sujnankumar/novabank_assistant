"""
NovaBank Knowledge Base Validator
==================================
Validates the knowledge base documents for:
  1. File existence (all 12 documents)
  2. Metadata.json completeness and correctness
  3. Required sections in each document
  4. Consistency of rates/limits between policy docs and structured data (loans.json, products.json)

Usage:
  python scripts/validate_knowledge_base.py
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(BASE_DIR, "knowledge_base")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Expected documents
EXPECTED_DOCUMENTS = [
    "01_home_loan_policy.md",
    "02_personal_loan_policy.md",
    "03_education_loan_policy.md",
    "04_vehicle_loan_policy.md",
    "05_credit_card_policy.md",
    "06_savings_account_policy.md",
    "07_fixed_deposit_policy.md",
    "08_transaction_policy.md",
    "09_account_management_policy.md",
    "10_fraud_and_security_policy.md",
    "11_customer_service_policy.md",
    "12_general_banking_faq.md",
]

# Required sections per document type
REQUIRED_SECTIONS = {
    "01_home_loan_policy.md": ["Eligibility", "Interest Rate", "Required Documents", "Processing Fee", "Prepayment", "Frequently Asked Questions"],
    "02_personal_loan_policy.md": ["Eligibility", "Interest Rate", "Required Documents", "Processing Fee", "Prepayment", "Frequently Asked Questions"],
    "03_education_loan_policy.md": ["Eligibility", "Interest Rate", "Required Documents", "Moratorium", "Frequently Asked Questions"],
    "04_vehicle_loan_policy.md": ["Eligibility", "Interest Rate", "Required Documents", "Down Payment", "Frequently Asked Questions"],
    "05_credit_card_policy.md": ["Eligibility", "Annual Fee", "Interest", "Reward", "Frequently Asked Questions"],
    "06_savings_account_policy.md": ["Eligibility", "Interest Rate", "Minimum Balance", "Dormant", "Frequently Asked Questions"],
    "07_fixed_deposit_policy.md": ["Eligibility", "Interest Rate", "Premature Withdrawal", "Maturity", "Frequently Asked Questions"],
    "08_transaction_policy.md": ["Transaction", "Dispute", "Failed", "Pending", "Frequently Asked Questions"],
    "09_account_management_policy.md": ["Account Opening", "Profile", "Dormant", "Closure", "Frequently Asked Questions"],
    "10_fraud_and_security_policy.md": ["Phishing", "Password", "OTP", "Reporting", "Frequently Asked Questions"],
    "11_customer_service_policy.md": ["Support Channel", "Complaint", "Escalation", "Frequently Asked Questions"],
    "12_general_banking_faq.md": ["savings account", "fixed deposit", "EMI", "credit score", "interest rate"],
}


class ValidationReport:
    """Tracks validation checks and results."""

    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def check(self, name, condition, detail=""):
        if condition:
            self.checks.append(("PASS", name, detail))
            self.passed += 1
        else:
            self.checks.append(("FAIL", name, detail))
            self.failed += 1

    def warn(self, name, detail=""):
        self.checks.append(("WARN", name, detail))
        self.warnings += 1

    def print_report(self):
        print()
        print("=" * 70)
        print("KNOWLEDGE BASE VALIDATION REPORT")
        print("=" * 70)
        print()

        for status, name, detail in self.checks:
            icon = {"PASS": "[OK]", "FAIL": "[X]", "WARN": "[!]"}[status]
            line = f"  [{status}] {icon} {name}"
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
            print("  [OK] ALL KNOWLEDGE BASE VALIDATION CHECKS PASSED")
        else:
            print(f"  [X] {self.failed} CHECK(S) FAILED -- review details above")

        print("=" * 70)


def load_json(directory, filename):
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_document(filename):
    path = os.path.join(KB_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def count_words(text):
    return len(text.split())


def find_rates_in_text(text):
    """Extract percentage values from text (e.g., '8.50%', '8.25%')."""
    return set(re.findall(r'(\d+\.\d+)%', text))


def find_amounts_in_text(text):
    """Extract INR amounts mentioned in text."""
    # Match patterns like 'INR 30,000', 'INR 75000', 'INR 5,00,000'
    amounts = []
    for match in re.finditer(r'INR\s*([\d,]+)', text):
        amount_str = match.group(1).replace(",", "")
        try:
            amounts.append(int(amount_str))
        except ValueError:
            pass
    return set(amounts)


def main():
    print("=" * 70)
    print("NovaBank Knowledge Base Validator")
    print("=" * 70)

    report = ValidationReport()

    # ── 1. Check document existence ────────────────────
    print("\nChecking document existence...")
    documents = {}
    for doc in EXPECTED_DOCUMENTS:
        content = read_document(doc)
        documents[doc] = content
        report.check(f"Document exists: {doc}", content is not None)

    # ── 2. Check metadata.json ─────────────────────────
    print("Checking metadata.json...")
    metadata = load_json(KB_DIR, "metadata.json")
    report.check("metadata.json exists", metadata is not None)

    if metadata:
        report.check("metadata.json has 12 entries",
                      len(metadata) == 12,
                      f"Found {len(metadata)} entries")

        # Check required metadata fields
        required_meta_fields = ["document_id", "filename", "title", "category", "version", "source", "synthetic"]
        all_meta_ok = True
        for entry in metadata:
            if not all(f in entry for f in required_meta_fields):
                all_meta_ok = False
                break
        report.check("All metadata entries have required fields", all_meta_ok)

        # Check all metadata filenames match expected documents
        meta_filenames = set(e["filename"] for e in metadata)
        expected_set = set(EXPECTED_DOCUMENTS)
        report.check("Metadata filenames match expected documents",
                      meta_filenames == expected_set,
                      f"Missing: {expected_set - meta_filenames}" if meta_filenames != expected_set else "")

        # Check all are marked synthetic
        all_synthetic = all(e.get("synthetic") is True for e in metadata)
        report.check("All metadata entries marked as synthetic", all_synthetic)

    # ── 3. Check required sections ─────────────────────
    print("Checking required sections...")
    for doc, required in REQUIRED_SECTIONS.items():
        content = documents.get(doc)
        if not content:
            continue
        content_lower = content.lower()
        missing = [s for s in required if s.lower() not in content_lower]
        report.check(f"Required sections in {doc}",
                     len(missing) == 0,
                     f"Missing: {missing}" if missing else "")

    # ── 4. Check word counts ───────────────────────────
    print("Checking word counts...")
    total_words = 0
    doc_words = {}
    for doc in EXPECTED_DOCUMENTS:
        content = documents.get(doc)
        if content:
            wc = count_words(content)
            doc_words[doc] = wc
            total_words += wc
            # Warn if under 800 words
            if wc < 800:
                report.warn(f"Word count for {doc}", f"Only {wc} words (expected 1000+)")
        else:
            doc_words[doc] = 0

    # ── 5. Consistency checks with loans.json ──────────
    print("Checking consistency with loans.json...")
    loans = load_json(DATA_DIR, "loans.json")
    if loans:
        loan_lookup = {l["loan_id"]: l for l in loans}

        # Check home loan policy rates
        home_content = documents.get("01_home_loan_policy.md", "")
        if home_content:
            home_rates = find_rates_in_text(home_content)
            for lid in ["LOAN001", "LOAN002", "LOAN011"]:
                loan = loan_lookup.get(lid)
                if loan:
                    rate_str = f"{loan['interest_rate']:.2f}" if loan['interest_rate'] != int(loan['interest_rate']) else f"{loan['interest_rate']:.1f}0"
                    # Handle both 8.50 and 8.5 formats
                    rate_found = (f"{loan['interest_rate']:.2f}" in home_rates or
                                  f"{loan['interest_rate']}" in home_rates or
                                  str(loan['interest_rate']) in home_rates)
                    report.check(f"Home loan doc mentions {lid} rate ({loan['interest_rate']}%)",
                                 rate_found,
                                 f"Rate {loan['interest_rate']}% not found in document" if not rate_found else "")

        # Check personal loan policy rates
        personal_content = documents.get("02_personal_loan_policy.md", "")
        if personal_content:
            for lid in ["LOAN003", "LOAN004", "LOAN005", "LOAN012"]:
                loan = loan_lookup.get(lid)
                if loan:
                    rate_str = str(loan['interest_rate'])
                    personal_rates = find_rates_in_text(personal_content)
                    rate_found = any(str(loan['interest_rate']) in r or f"{loan['interest_rate']:.2f}" in r
                                     for r in personal_rates) or rate_str in personal_content
                    report.check(f"Personal loan doc mentions {lid} rate ({loan['interest_rate']}%)",
                                 rate_found,
                                 f"Rate not found" if not rate_found else "")

        # Check education loan policy rates
        edu_content = documents.get("03_education_loan_policy.md", "")
        if edu_content:
            for lid in ["LOAN006", "LOAN007"]:
                loan = loan_lookup.get(lid)
                if loan:
                    rate_found = str(loan['interest_rate']) in edu_content
                    report.check(f"Education loan doc mentions {lid} rate ({loan['interest_rate']}%)",
                                 rate_found,
                                 f"Rate not found" if not rate_found else "")

        # Check vehicle loan policy rates
        vehicle_content = documents.get("04_vehicle_loan_policy.md", "")
        if vehicle_content:
            for lid in ["LOAN008", "LOAN009", "LOAN010"]:
                loan = loan_lookup.get(lid)
                if loan:
                    rate_found = str(loan['interest_rate']) in vehicle_content
                    report.check(f"Vehicle loan doc mentions {lid} rate ({loan['interest_rate']}%)",
                                 rate_found,
                                 f"Rate not found" if not rate_found else "")

        # Check loan min income consistency
        for lid in ["LOAN001", "LOAN003", "LOAN006"]:
            loan = loan_lookup.get(lid)
            if loan:
                income = loan["minimum_income"]
                # Check if this income is mentioned in the corresponding doc
                doc_map = {
                    "LOAN001": "01_home_loan_policy.md",
                    "LOAN003": "02_personal_loan_policy.md",
                    "LOAN006": "03_education_loan_policy.md",
                }
                doc = doc_map[lid]
                content = documents.get(doc, "")
                income_str = f"{income:,}"
                income_found = (income_str in content or str(income) in content)
                report.check(f"Loan {lid} min income ({income}) mentioned in {doc}",
                             income_found)

    # ── 6. Consistency checks with products.json ───────
    print("Checking consistency with products.json...")
    products = load_json(DATA_DIR, "products.json")
    if products:
        product_lookup = {p["product_id"]: p for p in products}

        # Check savings account rates
        savings_content = documents.get("06_savings_account_policy.md", "")
        if savings_content:
            for pid in ["PROD001", "PROD002", "PROD003"]:
                prod = product_lookup.get(pid)
                if prod:
                    rate_found = str(prod['interest_rate']) in savings_content
                    report.check(f"Savings doc mentions {pid} rate ({prod['interest_rate']}%)",
                                 rate_found)

            # Check minimum balances
            for pid in ["PROD001", "PROD002"]:
                prod = product_lookup.get(pid)
                if prod:
                    bal = prod['minimum_balance']
                    bal_found = (f"{bal:,}" in savings_content or str(bal) in savings_content)
                    report.check(f"Savings doc mentions {pid} min balance (INR {bal})",
                                 bal_found)

        # Check FD rates
        fd_content = documents.get("07_fixed_deposit_policy.md", "")
        if fd_content:
            for pid in ["PROD006", "PROD007", "PROD008", "PROD009"]:
                prod = product_lookup.get(pid)
                if prod:
                    rate_found = str(prod['interest_rate']) in fd_content
                    report.check(f"FD doc mentions {pid} rate ({prod['interest_rate']}%)",
                                 rate_found)

        # Check credit card annual fees
        cc_content = documents.get("05_credit_card_policy.md", "")
        if cc_content:
            for pid in ["PROD010", "PROD011", "PROD012", "PROD013"]:
                prod = product_lookup.get(pid)
                if prod:
                    fee = prod['annual_fee']
                    fee_found = (f"{fee:,}" in cc_content or str(fee) in cc_content)
                    report.check(f"Credit card doc mentions {pid} annual fee (INR {fee})",
                                 fee_found)

        # Check credit card interest rates
        if cc_content:
            for pid in ["PROD010", "PROD011", "PROD012", "PROD013"]:
                prod = product_lookup.get(pid)
                if prod:
                    rate_found = str(prod['interest_rate']) in cc_content
                    report.check(f"Credit card doc mentions {pid} rate ({prod['interest_rate']}%)",
                                 rate_found)

    # ── 7. Check no customer-specific data ─────────────
    print("Checking for customer-specific data leaks...")
    customer_ids = [f"CUST{i:03d}" for i in range(1, 11)]
    account_ids = [f"ACC{i:03d}" for i in range(1, 25)]
    leak_found = False

    for doc in EXPECTED_DOCUMENTS:
        content = documents.get(doc, "")
        for cid in customer_ids:
            if cid in content:
                report.check(f"No customer IDs in {doc}", False, f"Found {cid}")
                leak_found = True
                break
        else:
            continue  # Only reached if inner loop didn't break

    if not leak_found:
        report.check("No customer-specific data in knowledge base documents", True)

    # ── Print report ───────────────────────────────────
    report.print_report()

    # ── Word count summary ─────────────────────────────
    print()
    print("=" * 70)
    print("WORD COUNT SUMMARY")
    print("=" * 70)
    for doc in EXPECTED_DOCUMENTS:
        wc = doc_words.get(doc, 0)
        print(f"  {doc:45s} {wc:>6,} words")
    print(f"  {'':45s} {'------':>6s}")
    print(f"  {'TOTAL':45s} {total_words:>6,} words")
    print("=" * 70)

    # ── Knowledge base summary ─────────────────────────
    print()
    print("=" * 70)
    print("KNOWLEDGE BASE SUMMARY")
    print("=" * 70)
    print(f"  Documents created:       {sum(1 for d in documents.values() if d is not None)}")
    print(f"  Metadata entries:        {len(metadata) if metadata else 'N/A'}")
    print(f"  Total word count:        {total_words:,}")
    print(f"  Average words/document:  {total_words // len(EXPECTED_DOCUMENTS):,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
