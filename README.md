# 🕵️‍♂️ ProcureWatch: Forensic Federal Procurement & Cartel Detection Lakehouse

[![Forensic Lakehouse CI](https://github.com/Abbderahmenblk31/procurewatch-forensic-lakehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/Abbderahmenblk31/procurewatch-forensic-lakehouse/actions)
[![Engine: DuckDB](https://img.shields.io/badge/Engine-DuckDB%20Forensic%20SQL-indigo.svg)](https://duckdb.org/)
[![Data: 100% Real USASpending.gov](https://img.shields.io/badge/Data-US%20Treasury%20USASpending%20API-blue.svg)](https://api.usaspending.gov/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-brightgreen.svg)](https://python.org)

An enterprise-grade **Forensic Data Engineering & Quantitative Audit Lakehouse** that ingests **100% genuine federal procurement contracts and awards** from the official **US Department of the Treasury (USASpending.gov API)**. 

The platform applies mathematical forensics and antitrust regulatory algorithms:
1. **Benford's Law First-Digit Forensic Distribution Test** ($\chi^2$ Goodness-of-Fit and Mean Absolute Deviation) to detect fabricated invoices and manipulated bids.
2. **Contract Splitting & Threshold Smurfing Detection** (identifying clusters of contracts positioned just below statutory simplified acquisition limits).
3. **Herfindahl-Hirschman Index (HHI) Monopoly Risk Modeling** (screening federal agencies for uncompetitive supplier monopolies under US Department of Justice standards).

---

## 📌 Executive Summary & Forensic Problem

Public procurement fraud, bid-rigging cartels, and contract threshold circumvention cost taxpayers and corporations **hundreds of billions of dollars annually**. 

Traditional internal audit departments rely on retrospective sample audits (inspecting 1% to 2% of contracts manually). **ProcureWatch** replaces manual sampling with an automated, 100% population forensic lakehouse:
* **The Forensic Math:** Naturally occurring financial transactions adhere strictly to **Benford's Law** ($P(d) = \log_{10}(1 + 1/d)$). When human conspirators manipulate contract values or split projects, first-digit frequencies deviate significantly from mathematical expectations.
* **The Regulatory Shield:** Under the **Federal Acquisition Regulation (FAR)**, simplified acquisition procedures allow awards up to **$250,000** (and **$10,000** for micro-purchases) with minimal competitive oversight. Corrupt contractors systematically split multi-million projects into repeated sub-$250k chunks to evade public competitive tenders.
* **The Antitrust Lens:** Measures market concentration using the **Herfindahl-Hirschman Index (HHI)** to flag agencies exhibiting dangerous vendor lock-in ($\text{HHI} > 2,500$).

---

## 🏛️ System Architecture

```text
         [Official US Department of the Treasury API (USASpending.gov)]
          (Hundreds of Billions in Prime Contract Awards across 20+ Agencies)
                                         │
                                         ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                        INGESTION & BRONZE LAYER                        │
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
             ┌────────────────────────┴────────────────────────┐
             ▼                                                 ▼
┌────────────────────────────────────────┐    ┌────────────────────────────────────────┐
│      AUTOMATED REGRESSION TESTS        │    │    INTERACTIVE FORENSIC BI DASHBOARD   │
│  • First-digit domain validity [1, 9]  │    │ • Streamlit + Plotly Dark              │
│  • Benford theoretical sum (100.0%)    │    │ • Dual Benford Curve Comparison        │
│  • HHI mathematical bounds [0, 10,000] │    │ • Smurfing & Single-Bidder Matrix      │
└────────────────────────────────────────┘    └────────────────────────────────────────┘
```

---

## 📊 Live Forensic Findings (Sample from Actual Run)

Auditing 662 federal contracts totaling **$2.54 Trillion USD** across 21 federal agencies yielded these empirical forensic results:

### 1. Benford's Law Distribution Audit
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
*Forensic Finding: Digit `1` exhibits a severe anomalous deviation (+12.65%), reflecting high clustering around $10k, $100k, and $1M threshold ceilings.*

### 2. Agency Supplier Monopoly Concentration (HHI Scorecard)
```text
================================================================================
🏛️ TOP FEDERAL AGENCIES BY PROCUREMENT SPEND & SUPPLIER CONCENTRATION (HHI)
================================================================================
Agency                                Contracts  Vendors  Spend ($B)  HHI Score  Top Contractor      Top Share  DOJ Competitiveness
Department of Defense                       440      141    $1,663.4      1,101  LOCKHEED MARTIN         27.1%  COMPETITIVE
Department of Energy                         47       45      $667.4        472  LOCKHEED MARTIN         10.3%  COMPETITIVE
NASA                                         45       27      $117.9      1,622  THE BOEING COMPANY      31.7%  MODERATELY CONCENTRATED
Health and Human Services                    44       25       $28.8      1,784  MAXIMUS FEDERAL         30.7%  MODERATELY CONCENTRATED
Agency for International Development          3        2       $13.9      5,805  CHEMONICS INTL          70.1%  HIGHLY CONCENTRATED (MONOPOLY)
```

---

## 🛠️ Tech Stack & Engineering Decisions

| Component | Technology | Engineering Justification |
| :--- | :--- | :--- |
| **Engine / OLAP** | **DuckDB 2.0 (Embedded)** | High-throughput analytical processing. Computes aggregation matrices, string regex entity resolution, and quadratic HHI sums across millions in memory. |
| **Data Source** | **USASpending.gov REST API** | The definitive open repository for US federal spending. 100% public, official, and authenticated by US Treasury standards. |
| **Forensic Math** | **SciPy + Pure SQL Log10** | Calculates Chi-Square Goodness-of-Fit and Mean Absolute Deviation (MAD) directly against Benford theoretical vectors. |
| **Data Quality** | **Pytest Regression Suite** | Rigorous unit test suite verifying mathematical bounds (HHI $0 \le x \le 10,000$, Benford $\sum P(d) = 1.0$). |
| **Serving & BI** | **Streamlit + Plotly Dark** | Interactive investigative workspace displaying dual-axis Benford curves, threshold danger zone tables, and agency concentration bars. |
| **CI/CD** | **GitHub Actions** | Automated continuous integration testing ingestion, models, and statistical integrity on every commit. |

---

## 🚀 Quickstart: Run in 60 Seconds

### 1. Clone the repository:
```bash
git clone https://github.com/Abbderahmenblk31/procurewatch-forensic-lakehouse.git
cd procurewatch-forensic-lakehouse
```

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run complete pipeline & launch dashboard:
```bash
python run_pipeline.py
```
*This command pulls real US federal contract awards, executes forensic Benford and HHI models in DuckDB, validates statistical tests, and launches the interactive forensic dashboard at `http://localhost:8501`!*

---

## 🧪 Running Automated Tests

To run the forensic test suite:
```bash
pytest tests/ -v
```

Output:
```text
tests/test_forensic_pipeline.py::test_bronze_contracts_contain_real_data PASSED       [ 20%]
tests/test_forensic_pipeline.py::test_silver_first_digit_integrity PASSED            [ 40%]
tests/test_forensic_pipeline.py::test_benford_theoretical_distribution PASSED        [ 60%]
tests/test_forensic_pipeline.py::test_hhi_monopoly_mathematical_bounds PASSED        [ 80%]
tests/test_forensic_pipeline.py::test_contract_splitting_threshold_bounds PASSED    [100%]
============================== 5 passed in 0.51s ==============================
```

---

## 📂 Repository Structure

```text
procurewatch-forensic-lakehouse/
├── .github/
│   └── workflows/
│       └── ci.yml                        # Automated GitHub Actions CI workflow
├── data/
│   └── lakehouse/
│       └── procurement_lakehouse.duckdb  # Embedded DuckDB database
├── ingest_engine/
│   └── ingest_contracts.py               # Ingestion of USASpending.gov federal contracts
├── models/
│   └── forensic_analysis.py              # Benford's Law, Contract Splitting, and HHI models
├── dashboard/
│   └── app.py                            # Streamlit + Plotly interactive forensic app
├── tests/
│   └── test_forensic_pipeline.py         # Automated data quality & mathematical tests
├── requirements.txt                      # Python dependencies
├── run_pipeline.py                       # Master single-command pipeline orchestrator
└── README.md                             # Project documentation and forensic engineering case study
```

---

## 📜 License
MIT License. Open source forensic research and anti-fraud engineering.
