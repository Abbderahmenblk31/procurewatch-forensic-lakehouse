"""
ProcureWatch - Master Pipeline Orchestrator
===========================================
Runs full end-to-end forensic procurement pipeline:
1. Ingests genuine federal contracts from USASpending.gov API
2. Executes Benford's Law & HHI Monopoly models in DuckDB
3. Runs automated data quality and statistical tests
4. Launches the interactive Forensic Intelligence Dashboard
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_step(title, command):
    print("\n" + "="*75)
    print(f"  {title}")
    print("="*75)
    result = subprocess.run(command, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"❌ Error encountered in: {title}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    print("""
    ===============================================================
       🕵️‍♂️ PROCUREWATCH: FORENSIC PROCUREMENT FRAUD LAKEHOUSE 🕵️‍♂️
    ===============================================================
    """)
    run_step("STEP 1: INGESTING USASPENDING FEDERAL CONTRACT AWARDS", [sys.executable, "ingest_engine/ingest_contracts.py"])
    run_step("STEP 2: RUNNING BENFORD'S LAW & FORENSIC HHI MODELS", [sys.executable, "models/forensic_analysis.py"])
    run_step("STEP 3: EXECUTING AUTOMATED FORENSIC QUALITY TESTS", [sys.executable, "-m", "pytest", "tests/", "-v"])
    
    print("\n" + "="*75)
    print("  STEP 4: LAUNCHING INTERACTIVE FORENSIC BI DASHBOARD")
    print("="*75)
    print("Opening Streamlit on http://localhost:8501 ...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"], cwd=BASE_DIR)
