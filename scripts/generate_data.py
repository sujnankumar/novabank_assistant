"""
NovaBank Synthetic Data Generator
=================================
Generates all synthetic banking datasets for the AI-Powered Banking Customer Query Assistant.

Datasets generated:
  - customers.json         (10 customers)
  - accounts.json          (15-20 accounts)
  - transactions.json      (~1500 transactions)
  - loans.json             (10+ loan products)
  - products.json          (banking products)
  - customer_profiles.json (customer profiles)
  - customer_query_logs.txt (150-200 customer queries in text format)
  - query_labels.json      (intent labels for each query)

Usage:
  python scripts/generate_data.py
"""

import json
import random
import os
from datetime import datetime, timedelta

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
SEED = 42
NUM_CUSTOMERS = 10
NUM_ACCOUNTS_MIN = 15
NUM_ACCOUNTS_MAX = 20
NUM_TRANSACTIONS = 1500
NUM_LOAN_PRODUCTS = 12
NUM_QUERIES_MIN = 200

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

random.seed(SEED)


def ensure_data_dir():
    """Create the data directory if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


# ──────────────────────────────────────────────
# 1. CUSTOMERS
# ──────────────────────────────────────────────
def generate_customers():
    """Generate 10 synthetic Indian customers for NovaBank."""
    customers_data = [
        {"name": "Arjun Nair", "age": 28, "gender": "Male", "city": "Mangalore",
         "occupation": "Software Engineer", "monthly_income": 75000, "credit_score": 765},
        {"name": "Priya Sharma", "age": 34, "gender": "Female", "city": "Pune",
         "occupation": "Data Analyst", "monthly_income": 62000, "credit_score": 720},
        {"name": "Rohit Verma", "age": 45, "gender": "Male", "city": "Delhi",
         "occupation": "Business Owner", "monthly_income": 150000, "credit_score": 810},
        {"name": "Sneha Kulkarni", "age": 26, "gender": "Female", "city": "Bengaluru",
         "occupation": "UX Designer", "monthly_income": 55000, "credit_score": 690},
        {"name": "Vikram Patil", "age": 52, "gender": "Male", "city": "Mumbai",
         "occupation": "Senior Manager", "monthly_income": 120000, "credit_score": 780},
        {"name": "Ananya Reddy", "age": 30, "gender": "Female", "city": "Hyderabad",
         "occupation": "Doctor", "monthly_income": 95000, "credit_score": 750},
        {"name": "Karthik Iyer", "age": 38, "gender": "Male", "city": "Chennai",
         "occupation": "Chartered Accountant", "monthly_income": 85000, "credit_score": 800},
        {"name": "Meera Joshi", "age": 24, "gender": "Female", "city": "Jaipur",
         "occupation": "Graduate Student", "monthly_income": 18000, "credit_score": 640},
        {"name": "Suresh Menon", "age": 60, "gender": "Male", "city": "Kochi",
         "occupation": "Retired Teacher", "monthly_income": 35000, "credit_score": 730},
        {"name": "Divya Gupta", "age": 32, "gender": "Female", "city": "Lucknow",
         "occupation": "Marketing Manager", "monthly_income": 70000, "credit_score": 745},
    ]

    customers = []
    for i, c in enumerate(customers_data, start=1):
        customers.append({
            "customer_id": f"CUST{i:03d}",
            "name": c["name"],
            "age": c["age"],
            "gender": c["gender"],
            "city": c["city"],
            "occupation": c["occupation"],
            "monthly_income": c["monthly_income"],
            "credit_score": c["credit_score"],
            "consent": True if i <= 9 else random.choice([True, False])
        })

    return customers


# ──────────────────────────────────────────────
# 2. ACCOUNTS
# ──────────────────────────────────────────────
def generate_accounts(customers):
    """Generate 15-20 accounts ensuring every customer has at least one."""
    account_types = ["Savings", "Current", "Salary"]
    accounts = []
    account_counter = 0

    # First pass: give every customer at least one account
    for cust in customers:
        account_counter += 1
        primary_type = random.choice(account_types)
        opened_date = _random_date_past(days_back=365 * 5)
        balance = _generate_balance(primary_type, cust["monthly_income"])
        accounts.append({
            "account_id": f"ACC{account_counter:03d}",
            "customer_id": cust["customer_id"],
            "account_type": primary_type,
            "balance": balance,
            "currency": "INR",
            "status": "Active",
            "opened_date": opened_date.strftime("%Y-%m-%d")
        })

    # Second pass: add extra accounts to reach 15-20 total
    target = random.randint(NUM_ACCOUNTS_MIN, NUM_ACCOUNTS_MAX)
    extra_needed = target - len(accounts)
    for _ in range(extra_needed):
        account_counter += 1
        cust = random.choice(customers)
        existing_types = [a["account_type"] for a in accounts if a["customer_id"] == cust["customer_id"]]
        available_types = [t for t in account_types if t not in existing_types]
        if not available_types:
            available_types = account_types
        acct_type = random.choice(available_types)
        opened_date = _random_date_past(days_back=365 * 3)
        balance = _generate_balance(acct_type, cust["monthly_income"])
        status = random.choices(["Active", "Dormant"], weights=[95, 5])[0]
        accounts.append({
            "account_id": f"ACC{account_counter:03d}",
            "customer_id": cust["customer_id"],
            "account_type": acct_type,
            "balance": balance,
            "currency": "INR",
            "status": status,
            "opened_date": opened_date.strftime("%Y-%m-%d")
        })

    return accounts


def _generate_balance(account_type, monthly_income):
    """Generate a realistic balance based on account type and income."""
    if account_type == "Savings":
        return round(random.uniform(monthly_income * 0.5, monthly_income * 8), 2)
    elif account_type == "Current":
        return round(random.uniform(monthly_income * 1, monthly_income * 15), 2)
    else:  # Salary
        return round(random.uniform(monthly_income * 0.3, monthly_income * 2), 2)


def _random_date_past(days_back=365):
    """Generate a random date in the past within days_back days."""
    today = datetime(2026, 9, 24)
    delta = timedelta(days=random.randint(1, days_back))
    return today - delta


# ──────────────────────────────────────────────
# 3. TRANSACTIONS
# ──────────────────────────────────────────────
def generate_transactions(accounts, customers):
    """Generate ~1500 synthetic transactions with realistic distributions."""
    categories_debit = [
        "Food", "Shopping", "Travel", "Utilities", "Entertainment",
        "Healthcare", "Transfer", "ATM", "Bills", "Education", "Insurance", "Other"
    ]
    categories_credit = ["Salary", "Transfer", "Other"]

    merchants = {
        "Food": ["Swiggy", "Zomato", "BigBasket", "Dominos", "FreshMenu", "Blinkit"],
        "Shopping": ["Amazon", "Flipkart", "Myntra", "Ajio", "Meesho", "Nykaa"],
        "Travel": ["Uber", "Ola", "IRCTC", "MakeMyTrip", "RedBus", "IndiGo Airlines"],
        "Utilities": ["BESCOM", "Jio Recharge", "Airtel Recharge", "Tata Power", "BWSSB"],
        "Entertainment": ["Netflix", "BookMyShow", "Spotify", "Hotstar", "Amazon Prime"],
        "Healthcare": ["Apollo Pharmacy", "1mg", "PharmEasy", "Practo", "MedPlus"],
        "Transfer": ["NovaBank Transfer", "UPI Transfer", "NEFT Transfer", "IMPS Transfer"],
        "ATM": ["NovaBank ATM", "SBI ATM", "HDFC ATM", "ICICI ATM"],
        "Bills": ["Electricity Bill", "Water Bill", "Gas Bill", "Internet Bill", "Phone Bill"],
        "Education": ["Coursera", "Udemy", "Byju's", "Unacademy", "College Fees"],
        "Insurance": ["LIC Premium", "HDFC Life", "Star Health", "ICICI Lombard"],
        "Salary": ["NovaBank Salary Credit", "Employer Salary Credit"],
        "Other": ["Miscellaneous", "Cash Deposit", "Refund", "Cashback"]
    }

    descriptions = {
        "Food": ["Food delivery order", "Online food order", "Grocery purchase", "Restaurant payment"],
        "Shopping": ["Online shopping purchase", "E-commerce order", "Fashion purchase", "Electronics purchase"],
        "Travel": ["Cab ride payment", "Train ticket booking", "Flight ticket booking", "Bus ticket booking"],
        "Utilities": ["Monthly recharge", "Utility payment", "Service renewal", "Prepaid recharge"],
        "Entertainment": ["Subscription payment", "Movie ticket booking", "Streaming subscription", "Event booking"],
        "Healthcare": ["Medicine purchase", "Online pharmacy order", "Doctor consultation", "Lab test payment"],
        "Transfer": ["Fund transfer", "Money transfer to account", "Payment transfer", "Account-to-account transfer"],
        "ATM": ["ATM cash withdrawal", "Cash withdrawal from ATM"],
        "Bills": ["Monthly bill payment", "Utility bill payment", "Service bill payment"],
        "Education": ["Course purchase", "Education fee payment", "Online course subscription"],
        "Insurance": ["Insurance premium payment", "Policy renewal payment"],
        "Salary": ["Monthly salary credit", "Salary deposit"],
        "Other": ["Miscellaneous transaction", "Cash deposit at branch", "Refund credited", "Cashback received"]
    }

    # Build a customer-to-accounts mapping
    cust_accounts = {}
    for acc in accounts:
        cid = acc["customer_id"]
        if cid not in cust_accounts:
            cust_accounts[cid] = []
        cust_accounts[cid].append(acc)

    customer_ids = [c["customer_id"] for c in customers]
    # Weight distribution: some customers are more active
    customer_weights = [random.uniform(0.5, 2.0) for _ in customer_ids]

    transactions = []
    base_date = datetime(2025, 9, 25)  # ~12 months back from 2026-09-24

    for i in range(1, NUM_TRANSACTIONS + 1):
        # Pick a customer weighted
        cust_id = random.choices(customer_ids, weights=customer_weights, k=1)[0]
        accs = cust_accounts[cust_id]
        acc = random.choice(accs)

        # Random date in the last 12 months
        days_offset = random.randint(0, 364)
        txn_date = base_date + timedelta(days=days_offset)

        # Decide credit or debit (roughly 20% credit, 80% debit)
        txn_type = random.choices(["CREDIT", "DEBIT"], weights=[20, 80], k=1)[0]

        if txn_type == "DEBIT":
            category = random.choices(
                categories_debit,
                weights=[18, 15, 8, 10, 8, 5, 10, 8, 10, 3, 3, 2],
                k=1
            )[0]
        else:
            category = random.choices(
                categories_credit,
                weights=[60, 30, 10],
                k=1
            )[0]

        merchant = random.choice(merchants.get(category, ["NovaBank"]))
        description = random.choice(descriptions.get(category, ["Transaction"]))

        # Realistic amounts by category
        amount = _generate_amount(category, txn_type)

        status = random.choices(
            ["SUCCESS", "PENDING", "FAILED"],
            weights=[92, 5, 3],
            k=1
        )[0]

        transactions.append({
            "transaction_id": f"TXN{i:05d}",
            "customer_id": cust_id,
            "account_id": acc["account_id"],
            "date": txn_date.strftime("%Y-%m-%d"),
            "type": txn_type,
            "amount": amount,
            "merchant": merchant,
            "category": category,
            "description": description,
            "status": status
        })

    # Sort by date
    transactions.sort(key=lambda t: t["date"])
    # Re-assign IDs after sorting
    for i, txn in enumerate(transactions, start=1):
        txn["transaction_id"] = f"TXN{i:05d}"

    return transactions


def _generate_amount(category, txn_type):
    """Generate a realistic transaction amount based on category."""
    ranges = {
        "Food": (100, 2500),
        "Shopping": (200, 15000),
        "Travel": (50, 8000),
        "Utilities": (100, 3000),
        "Entertainment": (99, 2000),
        "Healthcare": (50, 5000),
        "Transfer": (500, 50000),
        "ATM": (500, 20000),
        "Bills": (200, 5000),
        "Education": (500, 25000),
        "Insurance": (1000, 15000),
        "Salary": (15000, 200000),
        "Other": (50, 5000),
    }
    lo, hi = ranges.get(category, (100, 5000))
    return round(random.uniform(lo, hi), 2)


# ──────────────────────────────────────────────
# 4. LOAN PRODUCTS
# ──────────────────────────────────────────────
def generate_loans():
    """Generate 12 NovaBank loan products."""
    loans = [
        {
            "loan_id": "LOAN001",
            "loan_name": "NovaBank Home Loan Standard",
            "loan_type": "Home Loan",
            "minimum_amount": 500000,
            "maximum_amount": 10000000,
            "interest_rate": 8.50,
            "minimum_income": 30000,
            "minimum_credit_score": 700,
            "minimum_age": 21,
            "maximum_age": 60,
            "maximum_tenure_years": 30,
            "processing_fee_percent": 0.50,
            "required_documents": [
                "PAN Card", "Aadhaar Card", "Salary Slips (last 3 months)",
                "Bank Statements (last 6 months)", "Property Documents",
                "IT Returns (last 2 years)"
            ]
        },
        {
            "loan_id": "LOAN002",
            "loan_name": "NovaBank Home Loan Premium",
            "loan_type": "Home Loan",
            "minimum_amount": 2500000,
            "maximum_amount": 50000000,
            "interest_rate": 8.25,
            "minimum_income": 75000,
            "minimum_credit_score": 750,
            "minimum_age": 25,
            "maximum_age": 58,
            "maximum_tenure_years": 30,
            "processing_fee_percent": 0.35,
            "required_documents": [
                "PAN Card", "Aadhaar Card", "Salary Slips (last 6 months)",
                "Bank Statements (last 12 months)", "Property Documents",
                "IT Returns (last 3 years)", "Form 16"
            ]
        },
        {
            "loan_id": "LOAN003",
            "loan_name": "NovaBank Personal Loan Lite",
            "loan_type": "Personal Loan",
            "minimum_amount": 25000,
            "maximum_amount": 500000,
            "interest_rate": 12.50,
            "minimum_income": 20000,
            "minimum_credit_score": 650,
            "minimum_age": 21,
            "maximum_age": 60,
            "maximum_tenure_years": 5,
            "processing_fee_percent": 2.00,
            "required_documents": [
                "PAN Card", "Aadhaar Card", "Salary Slips (last 3 months)",
                "Bank Statements (last 3 months)"
            ]
        },
        {
            "loan_id": "LOAN004",
            "loan_name": "NovaBank Personal Loan Plus",
            "loan_type": "Personal Loan",
            "minimum_amount": 100000,
            "maximum_amount": 2500000,
            "interest_rate": 11.00,
            "minimum_income": 40000,
            "minimum_credit_score": 720,
            "minimum_age": 23,
            "maximum_age": 58,
            "maximum_tenure_years": 7,
            "processing_fee_percent": 1.50,
            "required_documents": [
                "PAN Card", "Aadhaar Card", "Salary Slips (last 6 months)",
                "Bank Statements (last 6 months)", "IT Returns (last 2 years)"
            ]
        },
        {
            "loan_id": "LOAN005",
            "loan_name": "NovaBank Personal Loan Premium",
            "loan_type": "Personal Loan",
            "minimum_amount": 500000,
            "maximum_amount": 5000000,
            "interest_rate": 10.25,
            "minimum_income": 75000,
            "minimum_credit_score": 760,
            "minimum_age": 25,
            "maximum_age": 55,
            "maximum_tenure_years": 7,
            "processing_fee_percent": 1.00,
            "required_documents": [
                "PAN Card", "Aadhaar Card", "Salary Slips (last 6 months)",
                "Bank Statements (last 12 months)", "IT Returns (last 3 years)", "Form 16"
            ]
        },
        {
            "loan_id": "LOAN006",
            "loan_name": "NovaBank Education Loan Domestic",
            "loan_type": "Education Loan",
            "minimum_amount": 100000,
            "maximum_amount": 2000000,
            "interest_rate": 9.50,
            "minimum_income": 15000,
            "minimum_credit_score": 600,
            "minimum_age": 18,
            "maximum_age": 35,
            "maximum_tenure_years": 10,
            "processing_fee_percent": 1.00,
            "required_documents": [
                "PAN Card", "Aadhaar Card", "Admission Letter",
                "Fee Structure", "Academic Records",
                "Co-applicant Income Proof", "Bank Statements (last 6 months)"
            ]
        },
        {
            "loan_id": "LOAN007",
            "loan_name": "NovaBank Education Loan International",
            "loan_type": "Education Loan",
            "minimum_amount": 500000,
            "maximum_amount": 7500000,
            "interest_rate": 10.00,
            "minimum_income": 25000,
            "minimum_credit_score": 650,
            "minimum_age": 18,
            "maximum_age": 35,
            "maximum_tenure_years": 15,
            "processing_fee_percent": 0.75,
            "required_documents": [
                "PAN Card", "Aadhaar Card", "Passport", "Visa",
                "Admission Letter (Foreign University)", "Fee Structure",
                "Academic Records", "GRE/GMAT/IELTS Score",
                "Co-applicant Income Proof", "Collateral Documents (if above 7.5L)"
            ]
        },
        {
            "loan_id": "LOAN008",
            "loan_name": "NovaBank Two-Wheeler Loan",
            "loan_type": "Vehicle Loan",
            "minimum_amount": 25000,
            "maximum_amount": 300000,
            "interest_rate": 11.50,
            "minimum_income": 15000,
            "minimum_credit_score": 650,
            "minimum_age": 21,
            "maximum_age": 60,
            "maximum_tenure_years": 5,
            "processing_fee_percent": 2.00,
            "required_documents": [
                "PAN Card", "Aadhaar Card", "Salary Slips (last 3 months)",
                "Bank Statements (last 3 months)", "Vehicle Quotation"
            ]
        },
        {
            "loan_id": "LOAN009",
            "loan_name": "NovaBank Car Loan Standard",
            "loan_type": "Vehicle Loan",
            "minimum_amount": 200000,
            "maximum_amount": 5000000,
            "interest_rate": 9.25,
            "minimum_income": 30000,
            "minimum_credit_score": 700,
            "minimum_age": 21,
            "maximum_age": 60,
            "maximum_tenure_years": 7,
            "processing_fee_percent": 1.50,
            "required_documents": [
                "PAN Card", "Aadhaar Card", "Salary Slips (last 3 months)",
                "Bank Statements (last 6 months)", "Vehicle Proforma Invoice",
                "Driving License"
            ]
        },
        {
            "loan_id": "LOAN010",
            "loan_name": "NovaBank Car Loan Premium",
            "loan_type": "Vehicle Loan",
            "minimum_amount": 1000000,
            "maximum_amount": 15000000,
            "interest_rate": 8.75,
            "minimum_income": 75000,
            "minimum_credit_score": 750,
            "minimum_age": 25,
            "maximum_age": 58,
            "maximum_tenure_years": 7,
            "processing_fee_percent": 1.00,
            "required_documents": [
                "PAN Card", "Aadhaar Card", "Salary Slips (last 6 months)",
                "Bank Statements (last 12 months)", "Vehicle Proforma Invoice",
                "IT Returns (last 2 years)", "Driving License"
            ]
        },
        {
            "loan_id": "LOAN011",
            "loan_name": "NovaBank Home Improvement Loan",
            "loan_type": "Home Loan",
            "minimum_amount": 100000,
            "maximum_amount": 5000000,
            "interest_rate": 9.75,
            "minimum_income": 25000,
            "minimum_credit_score": 680,
            "minimum_age": 23,
            "maximum_age": 60,
            "maximum_tenure_years": 15,
            "processing_fee_percent": 0.75,
            "required_documents": [
                "PAN Card", "Aadhaar Card", "Salary Slips (last 3 months)",
                "Bank Statements (last 6 months)", "Property Ownership Proof",
                "Renovation Estimate"
            ]
        },
        {
            "loan_id": "LOAN012",
            "loan_name": "NovaBank Instant Personal Loan",
            "loan_type": "Personal Loan",
            "minimum_amount": 10000,
            "maximum_amount": 200000,
            "interest_rate": 14.00,
            "minimum_income": 15000,
            "minimum_credit_score": 630,
            "minimum_age": 21,
            "maximum_age": 55,
            "maximum_tenure_years": 3,
            "processing_fee_percent": 2.50,
            "required_documents": [
                "PAN Card", "Aadhaar Card", "Bank Statements (last 3 months)"
            ]
        },
    ]
    return loans


# ──────────────────────────────────────────────
# 5. BANKING PRODUCTS
# ──────────────────────────────────────────────
def generate_products():
    """Generate NovaBank banking products catalog."""
    products = [
        # Savings Accounts
        {
            "product_id": "PROD001",
            "product_name": "NovaBank Basic Savings Account",
            "product_type": "Savings Account",
            "interest_rate": 3.00,
            "minimum_balance": 1000,
            "annual_fee": 0,
            "transaction_limit": 50,
            "eligibility": "Indian resident, age 18+, valid KYC",
            "tenure": "No fixed tenure"
        },
        {
            "product_id": "PROD002",
            "product_name": "NovaBank Premium Savings Account",
            "product_type": "Savings Account",
            "interest_rate": 4.00,
            "minimum_balance": 25000,
            "annual_fee": 0,
            "transaction_limit": 100,
            "eligibility": "Indian resident, age 18+, valid KYC, minimum monthly income INR 30000",
            "tenure": "No fixed tenure"
        },
        {
            "product_id": "PROD003",
            "product_name": "NovaBank Zero Balance Savings Account",
            "product_type": "Savings Account",
            "interest_rate": 2.50,
            "minimum_balance": 0,
            "annual_fee": 0,
            "transaction_limit": 30,
            "eligibility": "Indian resident, age 18+, valid KYC",
            "tenure": "No fixed tenure"
        },
        # Current Accounts
        {
            "product_id": "PROD004",
            "product_name": "NovaBank Business Current Account",
            "product_type": "Current Account",
            "interest_rate": 0.00,
            "minimum_balance": 10000,
            "annual_fee": 500,
            "transaction_limit": 500,
            "eligibility": "Business registration, GST certificate, valid KYC",
            "tenure": "No fixed tenure"
        },
        {
            "product_id": "PROD005",
            "product_name": "NovaBank Premium Current Account",
            "product_type": "Current Account",
            "interest_rate": 0.00,
            "minimum_balance": 50000,
            "annual_fee": 0,
            "transaction_limit": 1000,
            "eligibility": "Business registration, GST certificate, minimum turnover INR 50 lakhs",
            "tenure": "No fixed tenure"
        },
        # Fixed Deposits
        {
            "product_id": "PROD006",
            "product_name": "NovaBank Regular Fixed Deposit",
            "product_type": "Fixed Deposit",
            "interest_rate": 6.50,
            "minimum_balance": 10000,
            "annual_fee": 0,
            "transaction_limit": None,
            "eligibility": "Indian resident, age 18+, valid KYC",
            "tenure": "6 months to 10 years"
        },
        {
            "product_id": "PROD007",
            "product_name": "NovaBank Tax Saver Fixed Deposit",
            "product_type": "Fixed Deposit",
            "interest_rate": 6.80,
            "minimum_balance": 10000,
            "annual_fee": 0,
            "transaction_limit": None,
            "eligibility": "Indian resident, age 18+, valid KYC, max INR 1.5 lakh per year under 80C",
            "tenure": "5 years (lock-in)"
        },
        {
            "product_id": "PROD008",
            "product_name": "NovaBank Senior Citizen Fixed Deposit",
            "product_type": "Fixed Deposit",
            "interest_rate": 7.25,
            "minimum_balance": 10000,
            "annual_fee": 0,
            "transaction_limit": None,
            "eligibility": "Indian resident, age 60+, valid KYC",
            "tenure": "6 months to 10 years"
        },
        {
            "product_id": "PROD009",
            "product_name": "NovaBank Flexi Fixed Deposit",
            "product_type": "Fixed Deposit",
            "interest_rate": 6.25,
            "minimum_balance": 25000,
            "annual_fee": 0,
            "transaction_limit": None,
            "eligibility": "Indian resident, age 18+, valid KYC, linked savings account required",
            "tenure": "1 year to 5 years"
        },
        # Credit Cards
        {
            "product_id": "PROD010",
            "product_name": "NovaBank Classic Credit Card",
            "product_type": "Credit Card",
            "interest_rate": 42.00,
            "minimum_balance": None,
            "annual_fee": 500,
            "transaction_limit": 200000,
            "eligibility": "Age 21+, minimum annual income INR 3 lakhs, credit score 650+",
            "tenure": "Lifetime (subject to renewal)"
        },
        {
            "product_id": "PROD011",
            "product_name": "NovaBank Gold Credit Card",
            "product_type": "Credit Card",
            "interest_rate": 39.60,
            "minimum_balance": None,
            "annual_fee": 1500,
            "transaction_limit": 500000,
            "eligibility": "Age 21+, minimum annual income INR 6 lakhs, credit score 700+",
            "tenure": "Lifetime (subject to renewal)"
        },
        {
            "product_id": "PROD012",
            "product_name": "NovaBank Platinum Credit Card",
            "product_type": "Credit Card",
            "interest_rate": 36.00,
            "minimum_balance": None,
            "annual_fee": 5000,
            "transaction_limit": 1500000,
            "eligibility": "Age 21+, minimum annual income INR 12 lakhs, credit score 750+",
            "tenure": "Lifetime (subject to renewal)"
        },
        {
            "product_id": "PROD013",
            "product_name": "NovaBank Cashback Credit Card",
            "product_type": "Credit Card",
            "interest_rate": 40.80,
            "minimum_balance": None,
            "annual_fee": 999,
            "transaction_limit": 300000,
            "eligibility": "Age 21+, minimum annual income INR 4 lakhs, credit score 680+",
            "tenure": "Lifetime (subject to renewal)"
        },
        # Loan summaries (pointing to detailed loans.json)
        {
            "product_id": "PROD014",
            "product_name": "NovaBank Home Loans",
            "product_type": "Loan",
            "interest_rate": 8.25,
            "minimum_balance": None,
            "annual_fee": None,
            "transaction_limit": None,
            "eligibility": "Age 21-60, minimum income INR 30000, credit score 700+",
            "tenure": "Up to 30 years"
        },
        {
            "product_id": "PROD015",
            "product_name": "NovaBank Personal Loans",
            "product_type": "Loan",
            "interest_rate": 10.25,
            "minimum_balance": None,
            "annual_fee": None,
            "transaction_limit": None,
            "eligibility": "Age 21-60, minimum income INR 15000, credit score 630+",
            "tenure": "Up to 7 years"
        },
        {
            "product_id": "PROD016",
            "product_name": "NovaBank Education Loans",
            "product_type": "Loan",
            "interest_rate": 9.50,
            "minimum_balance": None,
            "annual_fee": None,
            "transaction_limit": None,
            "eligibility": "Age 18-35, co-applicant required, valid admission letter",
            "tenure": "Up to 15 years"
        },
        {
            "product_id": "PROD017",
            "product_name": "NovaBank Vehicle Loans",
            "product_type": "Loan",
            "interest_rate": 8.75,
            "minimum_balance": None,
            "annual_fee": None,
            "transaction_limit": None,
            "eligibility": "Age 21-60, minimum income INR 15000, credit score 650+",
            "tenure": "Up to 7 years"
        },
    ]
    return products


# ──────────────────────────────────────────────
# 6. CUSTOMER PROFILES
# ──────────────────────────────────────────────
def generate_customer_profiles(customers):
    """Generate enriched customer profiles with preferences."""
    languages = ["English", "Hindi", "Kannada", "Tamil", "Telugu", "Malayalam", "Marathi"]
    comm_prefs = ["Email", "SMS", "WhatsApp", "Phone Call"]
    segments = ["Standard", "Premium", "Gold", "Platinum"]
    employment_types = ["Salaried", "Self-Employed", "Student", "Retired"]

    profiles = []
    for cust in customers:
        # Map occupation to employment type
        occ = cust["occupation"].lower()
        if "student" in occ:
            emp_type = "Student"
        elif "retired" in occ:
            emp_type = "Retired"
        elif "business" in occ or "owner" in occ:
            emp_type = "Self-Employed"
        else:
            emp_type = "Salaried"

        # Segment based on income
        income = cust["monthly_income"]
        if income >= 100000:
            segment = "Platinum"
        elif income >= 70000:
            segment = "Gold"
        elif income >= 40000:
            segment = "Premium"
        else:
            segment = "Standard"

        # Language by city
        city_lang = {
            "Mangalore": "Kannada", "Pune": "Marathi", "Delhi": "Hindi",
            "Bengaluru": "English", "Mumbai": "Hindi", "Hyderabad": "Telugu",
            "Chennai": "Tamil", "Jaipur": "Hindi", "Kochi": "Malayalam",
            "Lucknow": "Hindi"
        }

        profiles.append({
            "customer_id": cust["customer_id"],
            "preferred_language": city_lang.get(cust["city"], "English"),
            "communication_preference": random.choice(comm_prefs),
            "customer_segment": segment,
            "employment_type": emp_type,
            "relationship_years": random.randint(1, 15),
            "consent_for_personalization": cust["consent"]
        })

    return profiles


# ──────────────────────────────────────────────
# 7. CUSTOMER QUERY LOGS (.txt) + INTENT LABELS
# ──────────────────────────────────────────────
def generate_query_logs_and_labels(customers):
    """Generate 200+ customer query logs in text format and corresponding intent labels."""

    customer_ids = [c["customer_id"] for c in customers]

    # Define query templates grouped by intent
    query_templates = {
        "CHECK_BALANCE": [
            "What is my current account balance?",
            "How much money is in my account?",
            "Can you check my current balance?",
            "How much do I have in my savings account?",
            "Tell me my available balance.",
            "Show me my account balance.",
            "What's my balance right now?",
            "I want to know my account balance.",
            "Please check how much balance I have.",
            "What is the balance in my savings account?",
            "How much money do I currently have?",
            "Could you tell me my balance?",
        ],
        "ACCOUNT_DETAILS": [
            "Show me my account details.",
            "What accounts do I have with NovaBank?",
            "Can you show me my account information?",
            "I need my account details.",
            "What type of accounts do I have?",
            "Tell me about my NovaBank accounts.",
            "Give me all my account information.",
            "What is my account number and type?",
        ],
        "TRANSACTION_HISTORY": [
            "Show my recent transactions.",
            "Can I see my last five transactions?",
            "What transactions happened recently?",
            "Show me my transaction history.",
            "I want to see my recent bank transactions.",
            "List my last 10 transactions.",
            "What were my recent debit transactions?",
            "Show all my transactions from this month.",
            "Can I get a statement of my recent transactions?",
            "What's my transaction history for this month?",
        ],
        "TRANSACTION_SEARCH": [
            "Did I make any payment to Amazon?",
            "Search for a transaction of 5000 rupees.",
            "Find my last payment to Flipkart.",
            "Was there a failed transaction on my account?",
            "Show me all UPI transactions.",
            "Did I receive my salary this month?",
            "Find any transactions above 10000 rupees.",
        ],
        "SPENDING_ANALYSIS": [
            "How much did I spend this month?",
            "Where am I spending most of my money?",
            "Give me a summary of my spending.",
            "How much have I spent in the last 30 days?",
            "What is my total expenditure this month?",
            "Can you analyze my spending patterns?",
            "Show me a breakdown of my expenses.",
            "What are my top spending categories?",
        ],
        "MONTHLY_SPENDING": [
            "What was my total spending in August?",
            "How much did I spend last month?",
            "Give me my monthly spending summary.",
            "What were my expenses in July 2026?",
            "Compare my spending this month versus last month.",
            "Show me month-wise spending for the last 3 months.",
        ],
        "CATEGORY_SPENDING": [
            "How much did I spend on food?",
            "What did I spend on shopping this month?",
            "How much have I spent on travel?",
            "How much did I spend on entertainment?",
            "Show me my healthcare expenses.",
            "What are my utility bill payments this month?",
            "How much went to bills this month?",
            "Show me my education-related spending.",
            "What is my total food delivery expenditure?",
        ],
        "MERCHANT_SPENDING": [
            "How much did I spend on Amazon?",
            "What did I spend at Swiggy last month?",
            "How much have I paid to Uber?",
            "Show me all my Flipkart purchases.",
            "How much did I pay to Netflix?",
            "What is my total spending at Zomato?",
            "Show me my transactions with Myntra.",
            "How much have I spent at Apollo Pharmacy?",
            "What did I spend on BookMyShow?",
            "Show me my IRCTC transactions.",
        ],
        "LOAN_INFORMATION": [
            "What home loans do you offer?",
            "Tell me about your personal loans.",
            "What loan options are available?",
            "I want to know about your loan products.",
            "What types of loans does NovaBank offer?",
            "Can you tell me about education loans?",
            "What vehicle loan schemes do you have?",
            "Give me details of all your loan products.",
            "I am interested in a home loan. What are the options?",
        ],
        "LOAN_ELIGIBILITY": [
            "Am I eligible for a personal loan?",
            "Can I get a home loan?",
            "Would I qualify for an education loan?",
            "Check my eligibility for a vehicle loan.",
            "Am I eligible for the NovaBank Home Loan Premium?",
            "Can I apply for a car loan with my current salary?",
            "What is the maximum loan amount I can get?",
            "Do I qualify for the instant personal loan?",
            "Check if I can get a two-wheeler loan.",
        ],
        "LOAN_INTEREST_RATE": [
            "What is the home loan interest rate?",
            "What rate do you offer for personal loans?",
            "What is the current interest rate for education loans?",
            "Tell me the vehicle loan interest rate.",
            "What is the EMI for a 10 lakh home loan?",
            "How much interest will I pay on a personal loan of 5 lakhs?",
            "What is the cheapest loan rate you offer?",
        ],
        "LOAN_DOCUMENTS": [
            "What documents do I need for a home loan?",
            "What documents are required for a personal loan?",
            "List the documents needed for an education loan.",
            "What paperwork is required for a car loan?",
            "What all do I need to submit for a vehicle loan?",
            "Tell me the document requirements for the instant personal loan.",
        ],
        "CREDIT_CARD_INFORMATION": [
            "What credit cards do you offer?",
            "What are the benefits of your credit cards?",
            "Tell me about the NovaBank Platinum Credit Card.",
            "What is the annual fee for the Gold Credit Card?",
            "Which credit card is best for cashback?",
            "What are the eligibility criteria for your credit cards?",
            "I want to apply for a credit card. What options do I have?",
            "Compare your Classic and Gold credit cards.",
        ],
        "SAVINGS_INFORMATION": [
            "What savings account options do you have?",
            "Tell me about your premium savings account.",
            "What is the interest rate on your savings accounts?",
            "Do you have a zero balance savings account?",
            "What is the minimum balance for a savings account?",
            "What are the features of your savings accounts?",
        ],
        "FD_INFORMATION": [
            "What FD options are available?",
            "What is the interest rate on fixed deposits?",
            "Tell me about the tax saver FD.",
            "What is the minimum amount for a fixed deposit?",
            "Do you have a senior citizen FD scheme?",
            "What are your current FD interest rates?",
            "How does the flexi fixed deposit work?",
        ],
        "BANKING_POLICY": [
            "What is the minimum balance requirement?",
            "What is the policy for closing an account?",
            "What are the rules for fixed deposits?",
            "What are the charges for not maintaining minimum balance?",
            "How can I update my KYC details?",
            "What is the NEFT transfer limit?",
            "What are the timings for RTGS transfers?",
            "How do I report a lost debit card?",
            "What is the process for linking Aadhaar with my account?",
            "What are the ATM withdrawal limits?",
        ],
        "CUSTOMER_PROFILE": [
            "Update my communication preference to WhatsApp.",
            "What is my customer segment?",
            "Change my preferred language to Hindi.",
            "What details do you have about me?",
            "Am I a premium customer?",
            "How long have I been with NovaBank?",
        ],
        "GENERAL_BANKING_QUERY": [
            "Can you help me?",
            "Tell me something about banking.",
            "I have a question.",
            "What services does NovaBank provide?",
            "I need assistance with my account.",
            "Hello, I need some help.",
            "Good morning, can I speak to someone?",
            "Is there a branch near my location?",
            "What are your customer care timings?",
        ],
        "UNKNOWN_QUERY": [
            "What's the weather today?",
            "I want to change my password.",
            "Can you book a flight for me?",
            "Tell me a joke.",
            "What is the stock price of Reliance?",
            "Play some music.",
            "Who won the cricket match?",
            "Order food for me from Swiggy.",
            "What time is it?",
            "Can you recommend a good restaurant?",
        ],
    }

    # Map intents to expected agents and data sources
    intent_metadata = {
        "CHECK_BALANCE": ("BANKING_AGENT", "ACCOUNTS"),
        "ACCOUNT_DETAILS": ("BANKING_AGENT", "ACCOUNTS"),
        "TRANSACTION_HISTORY": ("BANKING_AGENT", "TRANSACTIONS"),
        "TRANSACTION_SEARCH": ("BANKING_AGENT", "TRANSACTIONS"),
        "SPENDING_ANALYSIS": ("BANKING_AGENT", "TRANSACTIONS"),
        "MONTHLY_SPENDING": ("BANKING_AGENT", "TRANSACTIONS"),
        "CATEGORY_SPENDING": ("BANKING_AGENT", "TRANSACTIONS"),
        "MERCHANT_SPENDING": ("BANKING_AGENT", "TRANSACTIONS"),
        "LOAN_INFORMATION": ("LOAN_AGENT", "LOANS"),
        "LOAN_ELIGIBILITY": ("LOAN_AGENT", "LOANS"),
        "LOAN_INTEREST_RATE": ("LOAN_AGENT", "LOANS"),
        "LOAN_DOCUMENTS": ("LOAN_AGENT", "LOANS"),
        "CREDIT_CARD_INFORMATION": ("PRODUCT_AGENT", "PRODUCTS"),
        "SAVINGS_INFORMATION": ("PRODUCT_AGENT", "PRODUCTS"),
        "FD_INFORMATION": ("PRODUCT_AGENT", "PRODUCTS"),
        "BANKING_POLICY": ("PRODUCT_AGENT", "PRODUCTS"),
        "CUSTOMER_PROFILE": ("BANKING_AGENT", "CUSTOMER_PROFILES"),
        "GENERAL_BANKING_QUERY": ("GENERAL_AGENT", "KNOWLEDGE_BASE"),
        "UNKNOWN_QUERY": ("GENERAL_AGENT", "NONE"),
    }

    queries = []
    labels = []
    query_counter = 0

    # Use all templates, plus repeat some for volume
    base_date = datetime(2026, 9, 1, 9, 0, 0)

    # First pass: use every template at least once
    for intent, templates in query_templates.items():
        for template in templates:
            query_counter += 1
            cust_id = random.choice(customer_ids)
            timestamp = base_date + timedelta(
                minutes=random.randint(0, 60 * 24 * 23),
                seconds=random.randint(0, 59)
            )
            queries.append({
                "query_id": f"Q{query_counter:03d}",
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "customer_id": cust_id,
                "query": template
            })
            agent, source = intent_metadata[intent]
            labels.append({
                "query_id": f"Q{query_counter:03d}",
                "intent": intent,
                "expected_agent": agent,
                "expected_data_source": source
            })

    # If we need more queries to reach 200, add duplicates with variations
    while query_counter < NUM_QUERIES_MIN:
        intent = random.choice(list(query_templates.keys()))
        template = random.choice(query_templates[intent])
        query_counter += 1
        cust_id = random.choice(customer_ids)
        timestamp = base_date + timedelta(
            minutes=random.randint(0, 60 * 24 * 23),
            seconds=random.randint(0, 59)
        )
        queries.append({
            "query_id": f"Q{query_counter:03d}",
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "customer_id": cust_id,
            "query": template
        })
        agent, source = intent_metadata[intent]
        labels.append({
            "query_id": f"Q{query_counter:03d}",
            "intent": intent,
            "expected_agent": agent,
            "expected_data_source": source
        })

    # Sort queries by timestamp
    combined = list(zip(queries, labels))
    combined.sort(key=lambda x: x[0]["timestamp"])

    # Re-assign query IDs after sorting
    sorted_queries = []
    sorted_labels = []
    for i, (q, l) in enumerate(combined, start=1):
        qid = f"Q{i:03d}"
        q["query_id"] = qid
        l["query_id"] = qid
        sorted_queries.append(q)
        sorted_labels.append(l)

    return sorted_queries, sorted_labels


def write_query_logs_txt(queries, filepath):
    """Write query logs as a plain text file."""
    with open(filepath, "w", encoding="utf-8") as f:
        for q in queries:
            line = f'{q["timestamp"]} | customer={q["customer_id"]} | {q["query"]}\n'
            f.write(line)


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def save_json(data, filename):
    """Save data as formatted JSON."""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  [OK] {filename}: {len(data)} records")
    return filepath


def main():
    print("=" * 60)
    print("NovaBank Synthetic Data Generator")
    print("=" * 60)
    print()

    ensure_data_dir()

    # Generate all datasets
    print("Generating datasets...")

    customers = generate_customers()
    save_json(customers, "customers.json")

    accounts = generate_accounts(customers)
    save_json(accounts, "accounts.json")

    transactions = generate_transactions(accounts, customers)
    save_json(transactions, "transactions.json")

    loans = generate_loans()
    save_json(loans, "loans.json")

    products = generate_products()
    save_json(products, "products.json")

    profiles = generate_customer_profiles(customers)
    save_json(profiles, "customer_profiles.json")

    queries, labels = generate_query_logs_and_labels(customers)

    # Write query logs as .txt
    txt_path = os.path.join(DATA_DIR, "customer_query_logs.txt")
    write_query_logs_txt(queries, txt_path)
    print(f"  [OK] customer_query_logs.txt: {len(queries)} queries")

    # Write intent labels as JSON
    save_json(labels, "query_labels.json")

    print()
    print("=" * 60)
    print("Generation Summary")
    print("=" * 60)
    print(f"  Customers:           {len(customers)}")
    print(f"  Accounts:            {len(accounts)}")
    print(f"  Transactions:        {len(transactions)}")
    print(f"  Loan Products:       {len(loans)}")
    print(f"  Banking Products:    {len(products)}")
    print(f"  Customer Profiles:   {len(profiles)}")
    print(f"  Customer Query Logs: {len(queries)}")
    print(f"  Intent Labels:       {len(labels)}")
    print()
    print("All datasets saved to:", DATA_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
