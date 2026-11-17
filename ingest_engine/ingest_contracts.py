"""
ProcureWatch - Federal Procurement Contracts Ingestion Engine
=============================================================
Ingests 100% genuine federal procurement contracts and awards from the
official USASpending.gov API (US Department of the Treasury).
Captures contract awards across the Department of Defense, Health & Human
Services, Energy, Homeland Security, NASA, and General Services.
Persists raw awards into an embedded DuckDB Forensic Lakehouse.
"""

import os
import sys
import time
import requests
import duckdb
import pandas as pd
from datetime import datetime, timezone

# Ensure stdout handles UTF-8 on Windows consoles
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAKEHOUSE_DIR = os.path.join(BASE_DIR, "data", "lakehouse")
os.makedirs(LAKEHOUSE_DIR, exist_ok=True)
DB_PATH = os.path.join(LAKEHOUSE_DIR, "procurement_lakehouse.duckdb")

API_ENDPOINT = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
HEADERS = {
    "User-Agent": "ProcureWatch-Forensic-Lakehouse/1.0 (Public-Accountability-Research)",
    "Content-Type": "application/json"
}

def fetch_procurement_awards(target_records=800, batch_size=100):
    """
    Fetches real federal procurement contracts across multiple agencies and time periods.
    Collects a diverse distribution of contract values for Benford's Law and splitting analysis.
    """
    print(f"[1/3] Querying USASpending.gov API for federal contract awards...")
    
    fields = [
        "Award ID", 
        "Recipient Name", 
        "Award Amount", 
        "Awarding Agency", 
        "Awarding Sub Agency", 
        "Contract Award Type", 
        "Start Date", 
        "Description"
    ]
    
    # We query multiple fiscal windows and award types to capture diverse procurement patterns
    queries = [
        # Large and Mid-tier prime contracts (Fiscal Year 2024)
        {
            "award_type_codes": ["A", "B", "C", "D"], # Definitive contracts, purchase orders, delivery orders
            "time_period": [{"start_date": "2023-10-01", "end_date": "2024-09-30"}],
            "sort": "Award Amount",
            "order": "desc"
        },
        # Operational and standard simplified acquisitions
        {
            "award_type_codes": ["A", "B"], # BPA calls and purchase orders
            "time_period": [{"start_date": "2024-01-01", "end_date": "2024-06-30"}],
            "sort": "Start Date",
            "order": "desc"
        }
    ]
    
    all_contracts = []
    seen_ids = set()
    
    for q_idx, q_filter in enumerate(queries, 1):
        page = 1
        max_pages = (target_records // len(queries)) // batch_size + 2
        print(f"   -> Executing procurement slice #{q_idx} (Types: {q_filter['award_type_codes']})...")
        
        while page <= max_pages and len(all_contracts) < target_records:
            payload = {
                "filters": {
                    "award_type_codes": q_filter["award_type_codes"],
                    "time_period": q_filter["time_period"]
                },
                "fields": fields,
                "page": page,
                "limit": batch_size,
                "sort": q_filter["sort"],
                "order": q_filter["order"]
            }
            
            try:
                resp = requests.post(API_ENDPOINT, json=payload, headers=HEADERS, timeout=20)
                if resp.status_code != 200:
                    print(f"      [!] API returned status {resp.status_code} on page {page}, moving to next slice.")
                    break
                    
                results = resp.json().get("results", [])
                if not results:
                    break
                    
                added_count = 0
                for item in results:
                    award_id = str(item.get("Award ID") or item.get("generated_internal_id") or "").strip()
                    amount = item.get("Award Amount")
                    recipient = item.get("Recipient Name")
                    
                    if not award_id or amount is None or amount <= 0 or not recipient:
                        continue
                        
                    if award_id in seen_ids:
                        continue
                        
                    seen_ids.add(award_id)
                    all_contracts.append({
                        "award_id": award_id,
                        "recipient_name": str(recipient).strip().upper(),
                        "award_amount": float(amount),
                        "awarding_agency": str(item.get("Awarding Agency") or "UNSPECIFIED").strip(),
                        "awarding_sub_agency": str(item.get("Awarding Sub Agency") or "UNSPECIFIED").strip(),
                        "contract_type": str(item.get("Contract Award Type") or "CONTRACT").strip(),
                        "start_date": str(item.get("Start Date") or "").strip()[:10],
                        "description": str(item.get("Description") or "").strip()[:200],
                        "ingested_at_utc": datetime.now(timezone.utc)
                    })
                    added_count += 1
                    
                print(f"      • Page {page}: Ingested {added_count} unique contracts (Total: {len(all_contracts)}/{target_records})")
                page += 1
                time.sleep(0.3) # Respectful API rate limiting
                
            except Exception as e:
                print(f"      [!] Network error on page {page}: {e}")
                break
                
    df = pd.DataFrame(all_contracts)
    print(f"\n[2/3] Completed API collection: {len(df):,} validated federal contract awards.")
    return df

def persist_to_lakehouse(df_contracts):
    """Saves raw procurement records into DuckDB Lakehouse Bronze layer."""
    print("[3/3] Ingesting contract records into DuckDB Forensic Lakehouse...")
    con = duckdb.connect(DB_PATH)
    
    con.register("df_incoming_contracts", df_contracts)
    
    con.execute("""
        CREATE OR REPLACE TABLE raw_procurement_contracts AS
        SELECT * FROM df_incoming_contracts;
    """)
    
    stats = con.execute("""
        SELECT 
            COUNT(*) as total_contracts,
            COUNT(DISTINCT recipient_name) as unique_vendors,
            COUNT(DISTINCT awarding_agency) as unique_agencies,
            ROUND(SUM(award_amount), 2) as total_obligated_amount_usd,
            ROUND(MIN(award_amount), 2) as min_award_usd,
            ROUND(MAX(award_amount), 2) as max_award_usd
        FROM raw_procurement_contracts;
    """).fetchone()
    
    print("\n" + "="*70)
    print("SUCCESS: PROCUREWATCH LAKEHOUSE INGESTION COMPLETE!")
    print(f"   * Lakehouse Database: {DB_PATH}")
    print(f"   * Total Contracts Ingested: {stats[0]:,}")
    print(f"   * Unique Commercial Vendors: {stats[1]:,}")
    print(f"   * Federal Agencies Tracked: {stats[2]:,}")
    print(f"   * Total Obligated Capital:  ${stats[3]:,.2f} USD")
    print(f"   * Award Value Range:        ${stats[4]:,.2f} to ${stats[5]:,.2f} USD")
    print("="*70 + "\n")
    
    con.close()

if __name__ == "__main__":
    print("="*70)
    print("  PROCUREWATCH: FEDERAL PROCUREMENT CONTRACTS INGESTION")
    print("="*70)
    contracts_df = fetch_procurement_awards(target_records=600, batch_size=100)
    persist_to_lakehouse(contracts_df)
