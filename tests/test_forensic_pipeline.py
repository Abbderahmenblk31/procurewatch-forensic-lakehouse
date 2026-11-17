"""
ProcureWatch - Forensic Pipeline & Data Quality Tests
=====================================================
Automated regression tests to verify Benford first-digit integrity,
entity resolution, and HHI monopoly index mathematical formulas.
"""

import os
import math
import duckdb
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "lakehouse", "procurement_lakehouse.duckdb")

@pytest.fixture
def db_conn():
    con = duckdb.connect(DB_PATH, read_only=True)
    yield con
    con.close()

def test_bronze_contracts_contain_real_data(db_conn):
    """Verifies that raw contracts table exists and contains real awards."""
    count = db_conn.execute("SELECT COUNT(*) FROM raw_procurement_contracts").fetchone()[0]
    assert count > 100, f"Insufficient contracts in bronze layer: {count}"

def test_silver_first_digit_integrity(db_conn):
    """Ensures first significant digits are strictly within domain [1, 9]."""
    invalid_digits = db_conn.execute("""
        SELECT COUNT(*) 
        FROM silver_procurement_contracts 
        WHERE first_digit NOT BETWEEN 1 AND 9 OR first_digit IS NULL;
    """).fetchone()[0]
    assert invalid_digits == 0, f"Found {invalid_digits} invalid first digits in silver layer!"

def test_benford_theoretical_distribution(db_conn):
    """Verifies that Benford theoretical distribution sums to 100% and adheres to log10(1 + 1/d)."""
    rows = db_conn.execute("SELECT digit, benford_pct FROM mart_benford_audit ORDER BY digit;").fetchall()
    total_pct = sum(r[1] for r in rows)
    assert 99.8 <= total_pct <= 100.2, f"Benford theoretical sum deviated: {total_pct}"
    
    # Test specific mathematical value for digit 1 (~30.1%)
    digit_1_pct = [r[1] for r in rows if r[0] == 1][0]
    expected_d1 = round(math.log10(1.0 + 1.0 / 1.0) * 100.0, 2)
    assert abs(digit_1_pct - expected_d1) < 0.1

def test_hhi_monopoly_mathematical_bounds(db_conn):
    """Ensures Herfindahl-Hirschman Index (HHI) is mathematically between 0 and 10,000."""
    invalid_hhi = db_conn.execute("""
        SELECT COUNT(*) 
        FROM mart_agency_vendor_concentration 
        WHERE hhi_index < 0 OR hhi_index > 10000;
    """).fetchone()[0]
    assert invalid_hhi == 0, f"Found {invalid_hhi} agencies with mathematically impossible HHI scores!"

def test_contract_splitting_threshold_bounds(db_conn):
    """Ensures split contracts in Simplified Acquisition Band do not exceed statutory $250k limit."""
    exceeded = db_conn.execute("""
        SELECT COUNT(*) 
        FROM mart_contract_splitting_risk 
        WHERE threshold_risk_category = 'Simplified Acquisition Limit ($250k)'
          AND avg_award_value_usd > 250000;
    """).fetchone()[0]
    assert exceeded == 0, f"Found {exceeded} split contracts exceeding statutory limit!"

def test_prescriptive_fraud_triage(db_conn):
    """Verifies that composite fraud risk scores are between 0 and 100 and mapped to valid triage actions."""
    df = db_conn.execute("SELECT * FROM mart_prescriptive_fraud_triage").df()
    assert len(df) > 0, "Prescriptive fraud triage mart is empty!"
    assert (df["composite_fraud_risk_score"] >= 0.0).all(), "Negative fraud risk score found!"
    assert (df["composite_fraud_risk_score"] <= 100.0).all(), "Fraud risk score exceeded 100!"
    valid_actions = {
        "🚨 TIER 1: FREEZE DISBURSEMENTS & SUBPOENA",
        "⚠️ TIER 2: FORENSIC DESK AUDIT & CONTRACT SAMPLING",
        "🔎 TIER 3: ENHANCED CONTINUOUS MONITORING",
        "✅ TIER 4: ROUTINE RECONCILIATION"
    }
    actual_actions = set(df["prescriptive_audit_action"].unique())
    assert actual_actions.issubset(valid_actions), f"Invalid actions: {actual_actions - valid_actions}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
