# 🕵️‍♂️ ProcureWatch: Forensic Federal Procurement & Cartel Detection Lakehouse

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit%20Cloud-6366F1.svg?style=for-the-badge&logo=streamlit)](https://abbderahmenblk31-procurewatch-forensic-lake-dashboardapp-v7ykcb.streamlit.app/)
[![Forensic Lakehouse CI](https://github.com/Abbderahmenblk31/procurewatch-forensic-lakehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/Abbderahmenblk31/procurewatch-forensic-lakehouse/actions)
[![Engine: DuckDB](https://img.shields.io/badge/Engine-DuckDB%20Forensic%20SQL-indigo.svg)](https://duckdb.org/)
[![Data: 100% Real USASpending.gov](https://img.shields.io/badge/Data-US%20Treasury%20USASpending%20API-blue.svg)](https://api.usaspending.gov/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🔗 **Interactive Cloud Application:** [Launch ProcureWatch Live Dashboard](https://abbderahmenblk31-procurewatch-forensic-lake-dashboardapp-v7ykcb.streamlit.app/)

An enterprise-grade **Forensic Data Engineering, Quantitative Audit & Prescriptive Enforcement Lakehouse** that ingests **100% genuine federal procurement contracts and awards** from the official **US Department of the Treasury (USASpending.gov API)**.

The platform applies mathematical forensics, antitrust regulatory algorithms, and an **Automated Legal & Audit Enforcement Triage Engine**:
1. **Benford's Law First-Digit Forensic Distribution Test** ($\chi^2 = 86.77$, $p < 0.0001$, $\text{MAD} = 3.51\%$) to detect anomalous transaction clustering.
2. **Contract Splitting & Threshold Smurfing Detection** (identifying clusters in the $200k-$250k band under FAR simplified acquisition rules).
3. **Herfindahl-Hirschman Index (HHI) Monopoly Risk Modeling** (screening federal agencies for uncompetitive vendor monopolies under US Department of Justice standards).
4. **Prescriptive Legal & Audit Enforcement Matrix** that categorizes high-risk contractors into binding audit tiers (`Tier 1: Freeze Disbursements & Subpoena`, `Tier 2: Desk Audit`, `Tier 3: Monitor`).

---

## 📌 Executive Summary & Forensic Problem

Public procurement fraud, single-bidder cartels, and contract threshold circumvention cost taxpayers and governments **hundreds of billions of dollars annually**.

Traditional internal audit departments rely on retrospective sample audits (inspecting 1% to 2% of contracts manually months after disbursements). **ProcureWatch** replaces manual sampling with an automated, 100% population forensic lakehouse:
* **The Forensic Math:** Naturally occurring financial transactions adhere strictly to **Benford's Law** ($P(d) = \log_{10}(1 + 1/d)$). Human conspirators who manipulate invoices or split awards trigger statistically significant deviations.
* **The Regulatory Loophole:** Under the **Federal Acquisition Regulation (FAR)**, simplified acquisition procedures allow awards up to **$250,000** (and **$10,000** for micro-purchases) with minimal competitive oversight. Corrupt contractors systematically split multi-million projects into repeated sub-$250k awards to bypass public competitive tenders.
* **The Antitrust Lens:** Measures market concentration using the **Herfindahl-Hirschman Index (HHI)** to flag agencies exhibiting dangerous vendor lock-in ($\text{HHI} > 2,500$).
* **Prescriptive Action:** Automatically assigns binding audit directives based on an objective **Composite Fraud Risk Score (0-100)**.

---

## 🏛️ Medallion Architecture & System Design

```text
         [Official US Department of the Treasury API (USASpending.gov)]
          (Hundreds of Billions in Prime Contract Awards across 20+ Agencies)
                                         │
                                         ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                        BRONZE LAYER (RAW INGESTION)                    │
  │  • fetch_procurement_awards(): Multi-slice API ingestion               │
  │  • Captures Award ID, Vendor, Obligated Amount, Sub-Agency, Start Date │
  │  • Paging, backoff, and idempotent persistence to DuckDB Lakehouse     │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                 SILVER LAYER (ENTITY RESOLUTION & AUDIT)               │
  │  • Entity Resolution: Strips corporate suffixes (LLC, INC, CORP, GRP) │
  │  • Mathematical First-Digit Extraction: CAST(SUBSTRING(amount, 1, 1))  │
  │  • Regulatory Tier Stratification (Micro, Simplified, Standard, Mega)  │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                   GOLD LAYER (FORENSIC & ANTITRUST MARTS)              │
  │  • mart_benford_audit: Empirical vs. Theoretical Log10 Distribution    │
  │    (Calculates Chi-Square statistic and Mean Absolute Deviation - MAD) │
  │  • mart_contract_splitting_risk: Identifies clusters in 80%-99% bands  │
  │  • mart_agency_vendor_concentration: Computes HHI Monopoly Scores      │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │       PRESCRIPTIVE DECISION INTELLIGENCE (LEGAL AUDIT TRIAGE)          │
  │  • mart_prescriptive_fraud_triage:                                     │
  │    - Composite Fraud Risk Score (0 - 100)                              │
  │    - Threshold Evasion (45%) + Agency Capture (25%) + Scale (30%)      │
  │    - Action: TIER 1 (FREEZE & SUBPOENA) / TIER 2 (DESK AUDIT)          │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼                                               ▼
 ┌────────────────────────────────────────┐    ┌────────────────────────────────────────┐
 │      AUTOMATED REGRESSION TESTS        │    │    INTERACTIVE FORENSIC BI DASHBOARD   │
 │  • First-digit domain validity [1, 9]  │    │ • Streamlit + Plotly Dark              │
 │  • Benford theoretical sum (100.0%)    │    │ • Dual Benford Curve Comparison        │
 │  • HHI mathematical bounds [0, 10,000] │    │ • Smurfing & Split Contract Ledger     │
 │  • Prescriptive Risk Bounds [0, 100]   │    │ • Automated Legal Enforcement Matrix   │
 └────────────────────────────────────────┘    └────────────────────────────────────────┘
```

---

## 🧮 Prescriptive Fraud Risk Scoring Model

The prescriptive engine calculates a multi-dimensional **Composite Fraud Risk Score ($0 \le S_{\text{risk}} \le 100$)** for each contractor entity:

$$S_{\text{risk}} = S_{\text{split}} + S_{\text{hhi}} + S_{\text{exposure}} + S_{\text{freq}}$$

Where:
1. **Threshold Evasion Score ($0 \le S_{\text{split}} \le 45$):**
   $$S_{\text{split}} = \min\left(45.0, \ (N_{\text{split}} \times 25.0) + \left(\frac{V_{\text{split}}}{\$250,000} \times 20.0\right)\right)$$
   Directly measures awards strategically positioned in the $200k-$249.9k statutory avoidance corridor.
2. **Agency Monopoly Capture ($0 \le S_{\text{hhi}} \le 25$):**
   $$S_{\text{hhi}} = \min\left(25.0, \ \text{Share}_{\text{agency}}\% \times 0.5\right)$$
   Measures the vendor's financial dominance over the awarding department's budget.
3. **High-Value Exposure ($0 \le S_{\text{exposure}} \le 15$):**
   $$S_{\text{exposure}} = \min\left(15.0, \ \frac{\text{Total Spend}}{\$10,000,000} \times 15.0\right)$$
4. **Contract Frequency Factor ($0 \le S_{\text{freq}} \le 15$):**
   $$S_{\text{freq}} = \min\left(15.0, \ N_{\text{awards}} \times 1.5\right)$$

### Prescriptive Legal Enforcement Directives:
| Risk Score | Prescriptive Action Directive | Enforcement Protocol |
| :--- | :--- | :--- |
| $\ge 60$ | `🚨 TIER 1: FREEZE DISBURSEMENTS & SUBPOENA` | Immediate payment hold. Issue Inspector General (OIG) subpoena for sub-contractor ledgers and billings. |
| $40 - 59$ | `⚠️ TIER 2: FORENSIC DESK AUDIT & CONTRACT SAMPLING` | Unannounced deliverable verification and independent pricing benchmarking. |
| $20 - 39$ | `🔎 TIER 3: ENHANCED CONTINUOUS MONITORING` | Automated red-flag triggers attached to next 5 purchase orders / modifications. |
| $< 20$ | `✅ TIER 4: ROUTINE RECONCILIATION` | Normal statutory disbursement and standard annual closeout. |

---

## 📊 Live Forensic Findings & Enforcement Scorecards

### 1. Benford's Law First-Digit Distribution Audit
```text
================================================================================
📊 BENFORD'S LAW FIRST-DIGIT DISTRIBUTION AUDIT TABLE
================================================================================
 digit  observed_count  actual_pct  benford_pct  deviation_pct          audit_flag
     1             283       42.75        30.10         +12.65 ANOMALOUS DEVIATION
     2             131       19.79        17.61          +2.18          CONFORMANT
     3              89       13.44        12.49          +0.95          CONFORMANT
     4              55        8.31         9.69          -1.38          CONFORMANT
     5              31        4.68         7.92          -3.24          CONFORMANT
     6              26        3.93         6.69          -2.76          CONFORMANT
     7              23        3.47         5.80          -2.33          CONFORMANT
     8              15        2.27         5.12          -2.85          CONFORMANT
     9               9        1.36         4.58          -3.22          CONFORMANT
================================================================================
Chi-Square Goodness-of-Fit Statistic: 86.77 (p-value: 0.0000)
Mean Absolute Deviation (MAD): 3.51%
```

### 2. Prescriptive Fraud Triage Output (Live Sample)
```text
Contractor Entity     Federal Agency             Awards   Total Spend ($)   Split Awards   Risk Score  Prescriptive Enforcement Directive
---------------------------------------------------------------------------------------------------------------------------------------------------
MORE PREPARED         Peace Corps                     1         $241,500               1        71.2   🚨 TIER 1: FREEZE DISBURSEMENTS & SUBPOENA
ARMEDIA               Intl Trade Commission           1         $225,978               1        69.9   🚨 TIER 1: FREEZE DISBURSEMENTS & SUBPOENA
COMBRIDGE SRL         Department of Defense           4       $1,272,594               1        52.7   ⚠️ TIER 2: FORENSIC DESK AUDIT & SAMPLING
SOFIE                 Department of Defense           2         $446,424               1        48.6   ⚠️ TIER 2: FORENSIC DESK AUDIT & SAMPLING
L3HARRIS NEXGEN       Department of Defense           1         $245,241               1        46.5   ⚠️ TIER 2: FORENSIC DESK AUDIT & SAMPLING
OPSOLUTIONS           Department of Defense           1         $240,000               1        46.1   ⚠️ TIER 2: FORENSIC DESK AUDIT & SAMPLING
LOCKHEED MARTIN       Department of Defense          90     $451,450,400,000           0        43.6   ⚠️ TIER 2: FORENSIC DESK AUDIT & SAMPLING
CHEMONICS INTL        USAID                           2       $9,714,132,000           0        43.0   ⚠️ TIER 2: FORENSIC DESK AUDIT & SAMPLING
---------------------------------------------------------------------------------------------------------------------------------------------------
```

---

## 🛠️ Tech Stack & Engineering Decisions

| Component | Technology | Engineering Justification |
| :--- | :--- | :--- |
| **Engine / OLAP** | **DuckDB 1.0+ Columnar** | Ultra-fast local analytical SQL engine. Eliminates heavy Spark or Snowflake costs while executing complex string parsing, regex entity resolution, and window functions in sub-seconds. |
| **Data Ingestion** | **Python 3 / Requests / PyArrow** | Multi-slice REST consumer with pagination, retry backoff, and idempotent ingestion from USASpending.gov. |
| **Statistical Forensics** | **SciPy + DuckDB SQL** | Native implementations of Benford Log10 distributions, Chi-Square Goodness-of-Fit, and HHI market concentration formulas. |
| **Serving & UI** | **Streamlit + Plotly Dark** | Interactive dual Benford curve comparisons, agency HHI bar charts, and an automated audit decision triage ledger. |
| **Testing** | **Pytest** | Automated unit tests verifying Benford mathematical sums, HHI range constraints, and fraud risk score bounds. |
| **CI/CD** | **GitHub Actions** | Automated integration tests executing on every commit. |

---

## 🧪 Automated Regression & Data Quality Test Suite

Run the test suite with:
```bash
pytest tests/ -v
```

Execution output:
```text
tests/test_forensic_pipeline.py::test_bronze_contracts_contain_real_data PASSED [ 16%]
tests/test_forensic_pipeline.py::test_silver_first_digit_integrity PASSED [ 33%]
tests/test_forensic_pipeline.py::test_benford_theoretical_distribution PASSED [ 50%]
tests/test_forensic_pipeline.py::test_hhi_monopoly_mathematical_bounds PASSED [ 66%]
tests/test_forensic_pipeline.py::test_contract_splitting_threshold_bounds PASSED [ 83%]
tests/test_forensic_pipeline.py::test_prescriptive_fraud_triage PASSED   [100%]
============================== 6 passed in 1.14s ==============================
```

---

## 🚀 Quickstart: Run Locally in 60 Seconds

### 1. Clone the repository
```bash
git clone https://github.com/Abbderahmenblk31/procurewatch-forensic-lakehouse.git
cd procurewatch-forensic-lakehouse
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the complete pipeline & launch dashboard
```bash
python run_pipeline.py
```
*This command executes live procurement ingestion from USASpending.gov, runs forensic transforms in DuckDB, passes all quality tests, and launches the dashboard at `http://localhost:8501`.*

---

## 📂 Repository Structure

```text
procurewatch-forensic-lakehouse/
├── .github/
│   └── workflows/
│       └── ci.yml                    # Automated GitHub Actions CI workflow
├── data/
│   └── lakehouse/
│       └── procurement_lakehouse.duckdb # Embedded DuckDB database with forensic marts
├── ingest_engine/
│   └── ingest_contracts.py           # Real-time USASpending.gov API ingestion
├── models/
│   └── forensic_analysis.py          # Benford's Law, Contract Splitting, HHI & prescriptive triage
├── dashboard/
│   └── app.py                        # Streamlit + Plotly dark interactive intelligence dashboard
├── tests/
│   └── test_forensic_pipeline.py     # Automated data quality & mathematical consistency tests
├── requirements.txt                  # Python dependencies
├── run_pipeline.py                   # Master single-command pipeline orchestrator
└── README.md                         # Project documentation and forensic audit case study
```

---

## 📜 License
MIT License. Open source research and engineering.
