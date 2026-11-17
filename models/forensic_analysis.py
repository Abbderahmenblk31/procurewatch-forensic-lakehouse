"""
ProcureWatch - Forensic Procurement & Fraud Analytics Engine
============================================================
Executes forensic accounting and statistical algorithms inside DuckDB:
1. Benford's Law First-Digit Distribution Audit (Chi-Square & MAD).
2. Contract Splitting & Statutory Threshold Smurfing Detection.
3. Herfindahl-Hirschman Index (HHI) Vendor Monopoly Concentration.
"""

import os
import sys
import math
import duckdb
import pandas as pd
from scipy.stats import chisquare

if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "lakehouse", "procurement_lakehouse.duckdb")

# Benford's Law Theoretical Probabilities for Digits 1 to 9
BENFORD_THEORETICAL = {
    d: round(math.log10(1.0 + 1.0 / d), 4) for d in range(1, 10)
}

def run_forensic_pipeline():
    print("="*75)
    print("  PROCUREWATCH: FORENSIC PROCUREMENT & FRAUD DETECTION ENGINE")
    print("="*75)
    
    con = duckdb.connect(DB_PATH)
    
    # 1. Silver Layer: Cleaned Contracts with First-Digit & Entity Normalization
    print("[1/4] Engineering Silver Layer: Entity resolution & first-digit extraction...")
    con.execute("""
        CREATE OR REPLACE TABLE silver_procurement_contracts AS
        WITH cleaned AS (
            SELECT 
                award_id,
                recipient_name,
                -- Entity Resolution: Normalize corporate suffixes for vendor clustering
                TRIM(REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(recipient_name, 
                            '\\b(INC|INCORPORATED|LLC|L\\.L\\.C\\.|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|SYSTEMS|SERVICES|SOLUTIONS|HOLDINGS|GROUP)\\b', '', 'g'
                        ),
                        '[,\\.\\-\\/]', ' ', 'g'
                    ),
                    '\\s+', ' ', 'g'
                )) AS normalized_vendor,
                award_amount,
                awarding_agency,
                awarding_sub_agency,
                contract_type,
                start_date,
                description,
                ingested_at_utc,
                -- Extract first significant digit of contract amount
                CAST(SUBSTRING(CAST(CAST(award_amount AS BIGINT) AS VARCHAR), 1, 1) AS INTEGER) AS first_digit,
                -- Threshold brackets
                CASE 
                    WHEN award_amount < 10000 THEN 'Micro (<$10k)'
                    WHEN award_amount BETWEEN 10000 AND 250000 THEN 'Simplified ($10k-$250k)'
                    WHEN award_amount BETWEEN 250000 AND 10000000 THEN 'Standard ($250k-$10M)'
                    ELSE 'Mega Prime (>$10M)'
                END AS procurement_tier
            FROM raw_procurement_contracts
            WHERE award_amount >= 1.0
        )
        SELECT * FROM cleaned
        WHERE first_digit BETWEEN 1 AND 9;
    """)
    print("   -> Cleaned contract entities and extracted first-digit frequency vectors.")
    
    # 2. Gold Mart 1: Benford's Law Forensic Audit
    print("[2/4] Executing Benford's Law Audit (First-Digit Forensic Test)...")
    
    # Create theoretical reference table
    ref_records = [{"digit": d, "benford_prob": p, "benford_pct": round(p * 100.0, 2)} for d, p in BENFORD_THEORETICAL.items()]
    df_ref = pd.DataFrame(ref_records)
    con.register("df_benford_ref", df_ref)
    
    con.execute("""
        CREATE OR REPLACE TABLE mart_benford_audit AS
        WITH empirical_counts AS (
            SELECT 
                first_digit as digit,
                COUNT(*) as observed_count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM silver_procurement_contracts), 2) as actual_pct
            FROM silver_procurement_contracts
            GROUP BY first_digit
        )
        SELECT 
            r.digit,
            COALESCE(e.observed_count, 0) as observed_count,
            COALESCE(e.actual_pct, 0.0) as actual_pct,
            r.benford_pct,
            ROUND(COALESCE(e.actual_pct, 0.0) - r.benford_pct, 2) as deviation_pct,
            ROUND(ABS(COALESCE(e.actual_pct, 0.0) - r.benford_pct), 2) as abs_deviation_pct,
            -- Audit flag: deviation > 3.5% indicates potential manual manipulation or threshold clustering
            CASE 
                WHEN ABS(COALESCE(e.actual_pct, 0.0) - r.benford_pct) > 3.5 THEN 'ANOMALOUS DEVIATION'
                ELSE 'CONFORMANT'
            END as audit_flag
        FROM df_benford_ref r
        LEFT JOIN empirical_counts e ON r.digit = e.digit
        ORDER BY r.digit;
    """)
    
    # Calculate Chi-Square Goodness-of-Fit and Mean Absolute Deviation (MAD)
    benford_df = con.execute("SELECT observed_count, benford_pct FROM mart_benford_audit ORDER BY digit;").df()
    total_obs = benford_df["observed_count"].sum()
    expected_counts = (benford_df["benford_pct"] / 100.0) * total_obs
    chi2_stat, p_val = chisquare(f_obs=benford_df["observed_count"], f_exp=expected_counts)
    mad_score = con.execute("SELECT ROUND(AVG(abs_deviation_pct), 2) FROM mart_benford_audit;").fetchone()[0]
    
    print(f"   -> Benford Chi2 Statistic: {chi2_stat:.2f} (p-value: {p_val:.4f})")
    print(f"   -> Mean Absolute Deviation (MAD): {mad_score:.2f}%")
    
    # 3. Gold Mart 2: Contract Splitting & Threshold Smurfing Detection
    print("[3/4] Detecting Contract Splitting & Threshold Evasion Risk...")
    con.execute("""
        CREATE OR REPLACE TABLE mart_contract_splitting_risk AS
        WITH suspicious_brackets AS (
            SELECT 
                awarding_agency,
                awarding_sub_agency,
                normalized_vendor,
                award_id,
                award_amount,
                start_date,
                contract_type,
                -- Flag awards positioned in the upper 80%-99% band of statutory thresholds
                CASE 
                    WHEN award_amount BETWEEN 200000 AND 249999.99 THEN 'Simplified Acquisition Limit ($250k)'
                    WHEN award_amount BETWEEN 8000 AND 9999.99 THEN 'Micro-Purchase Limit ($10k)'
                    ELSE 'Standard'
                END as threshold_risk_category
            FROM silver_procurement_contracts
        )
        SELECT 
            awarding_agency,
            awarding_sub_agency,
            normalized_vendor,
            threshold_risk_category,
            COUNT(*) as split_contract_count,
            ROUND(SUM(award_amount), 2) as total_split_value_usd,
            ROUND(AVG(award_amount), 2) as avg_award_value_usd
        FROM suspicious_brackets
        WHERE threshold_risk_category != 'Standard'
        GROUP BY awarding_agency, awarding_sub_agency, normalized_vendor, threshold_risk_category
        HAVING COUNT(*) >= 1
        ORDER BY total_split_value_usd DESC;
    """)
    
    # 4. Gold Mart 3: Agency Vendor Monopoly Concentration (HHI Index)
    print("[4/4] Calculating Herfindahl-Hirschman Monopoly Index (HHI) by Agency...")
    con.execute("""
        CREATE OR REPLACE TABLE mart_agency_vendor_concentration AS
        WITH agency_totals AS (
            SELECT 
                awarding_agency,
                SUM(award_amount) as total_agency_spend_usd,
                COUNT(*) as total_agency_contracts,
                COUNT(DISTINCT normalized_vendor) as unique_vendors
            FROM silver_procurement_contracts
            GROUP BY awarding_agency
        ),
        vendor_shares AS (
            SELECT 
                c.awarding_agency,
                c.normalized_vendor,
                SUM(c.award_amount) as vendor_spend_usd,
                ROUND(SUM(c.award_amount) * 100.0 / a.total_agency_spend_usd, 2) as market_share_pct
            FROM silver_procurement_contracts c
            JOIN agency_totals a ON c.awarding_agency = a.awarding_agency
            GROUP BY c.awarding_agency, c.normalized_vendor, a.total_agency_spend_usd
        ),
        agency_hhi AS (
            SELECT 
                awarding_agency,
                ROUND(SUM(POWER(market_share_pct, 2)), 0) as hhi_index,
                MAX_BY(normalized_vendor, market_share_pct) as top_contractor,
                MAX(market_share_pct) as top_contractor_share_pct
            FROM vendor_shares
            GROUP BY awarding_agency
        )
        SELECT 
            a.awarding_agency,
            a.total_agency_contracts,
            a.unique_vendors,
            ROUND(a.total_agency_spend_usd, 2) as total_spend_usd,
            h.hhi_index,
            h.top_contractor,
            h.top_contractor_share_pct,
            -- Regulatory HHI Classifications (US Dept of Justice standard)
            CASE 
                WHEN h.hhi_index > 2500 THEN 'HIGHLY CONCENTRATED (MONOPOLY RISK)'
                WHEN h.hhi_index BETWEEN 1500 AND 2500 THEN 'MODERATELY CONCENTRATED'
                ELSE 'COMPETITIVE'
            END as market_competitiveness_tier
        FROM agency_totals a
        JOIN agency_hhi h ON a.awarding_agency = h.awarding_agency
        ORDER BY a.total_agency_spend_usd DESC;
    """)
    
    # 5. Gold Mart 4: Prescriptive Forensic Audit & Triage Action Engine
    print("[5/5] Generating Prescriptive Forensic Audit & Triage Action Engine...")
    con.execute("""
        CREATE OR REPLACE TABLE mart_prescriptive_fraud_triage AS
        WITH agency_totals AS (
            SELECT 
                awarding_agency,
                SUM(award_amount) as agency_total_spend
            FROM silver_procurement_contracts
            GROUP BY awarding_agency
        ),
        vendor_metrics AS (
            SELECT 
                c.normalized_vendor,
                c.awarding_agency,
                COUNT(*) as total_awards,
                ROUND(SUM(c.award_amount), 2) as total_awarded_usd,
                ROUND(AVG(c.award_amount), 2) as avg_award_usd,
                COUNT(CASE WHEN c.award_amount BETWEEN 200000 AND 249999.99 OR c.award_amount BETWEEN 8000 AND 9999.99 THEN 1 END) as threshold_cluster_count,
                ROUND(SUM(CASE WHEN c.award_amount BETWEEN 200000 AND 249999.99 OR c.award_amount BETWEEN 8000 AND 9999.99 THEN c.award_amount ELSE 0 END), 2) as threshold_cluster_value_usd,
                ROUND(SUM(c.award_amount) * 100.0 / a.agency_total_spend, 2) as agency_share_pct
            FROM silver_procurement_contracts c
            JOIN agency_totals a ON c.awarding_agency = a.awarding_agency
            GROUP BY c.normalized_vendor, c.awarding_agency, a.agency_total_spend
        ),
        scored AS (
            SELECT 
                v.*,
                ROUND(
                    LEAST(45.0, (v.threshold_cluster_count * 25.0) + (v.threshold_cluster_value_usd / 250000.0 * 20.0)) +
                    LEAST(25.0, (v.agency_share_pct * 0.5)) +
                    LEAST(15.0, (v.total_awarded_usd / 10000000.0 * 15.0)) +
                    LEAST(15.0, (v.total_awards * 1.5)),
                    1
                ) as composite_fraud_risk_score
            FROM vendor_metrics v
        )
        SELECT 
            normalized_vendor,
            awarding_agency,
            total_awards,
            total_awarded_usd,
            avg_award_usd,
            threshold_cluster_count,
            threshold_cluster_value_usd,
            agency_share_pct,
            composite_fraud_risk_score,
            CASE 
                WHEN composite_fraud_risk_score >= 60 THEN '🚨 TIER 1: FREEZE DISBURSEMENTS & SUBPOENA'
                WHEN composite_fraud_risk_score >= 40 THEN '⚠️ TIER 2: FORENSIC DESK AUDIT & CONTRACT SAMPLING'
                WHEN composite_fraud_risk_score >= 20 THEN '🔎 TIER 3: ENHANCED CONTINUOUS MONITORING'
                ELSE '✅ TIER 4: ROUTINE RECONCILIATION'
            END as prescriptive_audit_action,
            CASE 
                WHEN composite_fraud_risk_score >= 60 THEN 
                    CONCAT('Critical threshold evasion detected (', CAST(threshold_cluster_count AS VARCHAR), ' awards clustered in $200k-$250k band) with high agency capture (', CAST(agency_share_pct AS VARCHAR), '%). Immediate disbursement hold and OIG subpoena mandated.')
                WHEN composite_fraud_risk_score >= 40 THEN 
                    CONCAT('Elevated forensic risk. High exposure ($', CAST(total_awarded_usd AS VARCHAR), ' USD) or threshold boundary award. Initiate unannounced contract sampling.')
                WHEN composite_fraud_risk_score >= 20 THEN 
                    'Moderate profile. Flag next 5 purchase orders for automated competitive bid verification.'
                ELSE 
                    'Within normal statutory disbursement distribution. Maintain standard quarterly audit.'
            END as prescriptive_decision_rationale
        FROM scored
        ORDER BY composite_fraud_risk_score DESC, total_awarded_usd DESC;
    """)
    print("   -> Prescriptive fraud triage engine built.")
    
    print("\n" + "="*80)
    print("📊 BENFORD'S LAW FIRST-DIGIT DISTRIBUTION AUDIT TABLE")
    print("="*80)
    audit_table = con.execute("SELECT digit, observed_count, actual_pct, benford_pct, deviation_pct, audit_flag FROM mart_benford_audit;").df()
    print(audit_table.to_string(index=False))
    print("="*80)
    
    print("\n" + "="*80)
    print("🏛️ TOP FEDERAL AGENCIES BY PROCUREMENT SPEND & SUPPLIER CONCENTRATION (HHI)")
    print("="*80)
    top_agencies = con.execute("""
        SELECT 
            awarding_agency,
            total_agency_contracts as contracts,
            unique_vendors as vendors,
            ROUND(total_spend_usd / 1e9, 2) as spend_billions_usd,
            hhi_index,
            top_contractor,
            top_contractor_share_pct as top_share_pct,
            market_competitiveness_tier
        FROM mart_agency_vendor_concentration
        LIMIT 5;
    """).df()
    print(top_agencies.to_string(index=False))
    print("="*80 + "\n")
    
    con.close()

if __name__ == "__main__":
    run_forensic_pipeline()
