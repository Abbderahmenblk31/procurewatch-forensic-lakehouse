"""
ProcureWatch - Federal Procurement Forensics & Cartel Detection Dashboard
=========================================================================
An enterprise forensic accounting and compliance intelligence application
built on DuckDB Lakehouse and real-time US Federal Procurement data.
Detects Benford's Law first-digit anomalies, threshold evasion, and HHI monopolies.
"""

import os
import sys
import duckdb
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="ProcureWatch | Forensic Procurement Lakehouse",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "lakehouse", "procurement_lakehouse.duckdb")

@st.cache_data(ttl=60)
def load_forensic_data():
    # Cloud auto-init fallback if lakehouse db is missing
    if not os.path.exists(DB_PATH):
        import subprocess
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "ingest_engine", "ingest_contracts.py")], check=True)
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "models", "forensic_analysis.py")], check=True)
        
    con = duckdb.connect(DB_PATH, read_only=True)
    
    benford_df = con.execute("SELECT * FROM mart_benford_audit ORDER BY digit;").df()
    hhi_df = con.execute("SELECT * FROM mart_agency_vendor_concentration ORDER BY total_spend_usd DESC;").df()
    splitting_df = con.execute("SELECT * FROM mart_contract_splitting_risk ORDER BY total_split_value_usd DESC;").df()
    
    summary_stats = con.execute("""
        SELECT 
            COUNT(*) as total_contracts,
            COUNT(DISTINCT normalized_vendor) as unique_vendors,
            COUNT(DISTINCT awarding_agency) as unique_agencies,
            ROUND(SUM(award_amount), 2) as total_spend_usd,
            ROUND(AVG(award_amount), 2) as avg_contract_usd
        FROM silver_procurement_contracts;
    """).fetchone()
    
    con.close()
    return benford_df, hhi_df, splitting_df, summary_stats

# Title & Executive Header
st.markdown("""
<div style='background-color: #0b132b; padding: 22px; border-radius: 12px; margin-bottom: 25px; border-left: 6px solid #6366f1;'>
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <div>
            <h1 style='color: #ffffff; margin: 0; font-size: 26px;'>🕵️‍♂️ ProcureWatch: Forensic Procurement & Cartel Detection Lakehouse</h1>
            <p style='color: #94a3b8; margin: 6px 0 0 0; font-size: 14px;'>
                Auditing <b>Trillions in Federal Contracts</b> via Benford's Law, HHI Monopoly Indices, and Contract Splitting Detection
            </p>
        </div>
        <div style='background-color: #1c2541; padding: 10px 18px; border-radius: 8px; border: 1px solid #3a506b; text-align: right;'>
            <span style='color: #94a3b8; font-size: 12px;'>Data Source:</span> <b style='color: #38bdf8;'>USASpending.gov API</b> | 
            <span style='color: #94a3b8; font-size: 12px;'>Engine:</span> <b style='color: #818cf8;'>DuckDB Forensic SQL</b>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

try:
    benford_df, hhi_df, splitting_df, summary = load_forensic_data()
except Exception as e:
    st.error(f"Failed to connect to Forensic Lakehouse: {e}")
    st.stop()

# Top KPI Metric Cards
total_spend = float(summary[3])
total_contracts = int(summary[0])
unique_vendors = int(summary[1])
monopoly_agencies = len(hhi_df[hhi_df["market_competitiveness_tier"].str.contains("HIGHLY CONCENTRATED")])

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        "🏛️ Total Audited Federal Spend",
        f"${total_spend / 1e12:.2f} Trillion" if total_spend >= 1e12 else f"${total_spend / 1e9:.2f} Billion",
        delta="Official US Treasury Data"
    )
with col2:
    st.metric(
        "📋 Contracts Audited",
        f"{total_contracts:,} Awards",
        delta=f"{unique_vendors:,} Contractors Screened"
    )
with col3:
    st.metric(
        "🚨 Monopoly Risk Agencies",
        f"{monopoly_agencies} Agencies",
        delta="HHI Index > 2,500 (DOJ Standard)",
        delta_color="inverse"
    )
with col4:
    split_suspects = int(splitting_df["split_contract_count"].sum())
    st.metric(
        "⚠️ Threshold Smurfing Alerts",
        f"{split_suspects} Awards",
        delta="Clustered Below Statutory Limits",
        delta_color="inverse"
    )

st.markdown("---")

# Main Investigative Tabs
tab1, tab2, tab3 = st.tabs([
    "📐 Benford's Law First-Digit Audit",
    "✂️ Contract Splitting & Threshold Smurfing",
    "🏢 Agency Vendor Concentration (HHI Index)"
])

with tab1:
    st.subheader("Benford's Law First-Digit Distribution Forensic Test")
    st.markdown("""
    Under **Benford's Law**, naturally occurring transaction sums exhibit a specific logarithmic distribution where 
    digit `1` appears as the leading digit ~30.1% of the time, and digit `9` appears ~4.6% of the time. 
    **Significant deviations often signal artificial price inflation, bid manipulation, or threshold evasion.**
    """)
    
    # Benford Comparison Chart
    fig_benford = go.Figure()
    
    fig_benford.add_trace(go.Bar(
        x=benford_df["digit"],
        y=benford_df["actual_pct"],
        name="Empirical Observed %",
        marker_color="#6366f1",
        opacity=0.85
    ))
    
    fig_benford.add_trace(go.Scatter(
        x=benford_df["digit"],
        y=benford_df["benford_pct"],
        name="Benford's Theoretical %",
        line=dict(color="#f43f5e", width=3, dash="dot"),
        mode="lines+markers"
    ))
    
    fig_benford.update_layout(
        template="plotly_dark",
        height=420,
        title="First-Digit Frequency: Empirical Federal Contracts vs. Benford Law",
        xaxis=dict(title="First Significant Digit (1 to 9)", tickmode="linear"),
        yaxis=dict(title="Occurrence Percentage (%)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_benford, use_container_width=True)
    
    st.subheader("Statistical Deviation Scorecard")
    st.dataframe(
        benford_df[[
            "digit", "observed_count", "actual_pct", "benford_pct", "deviation_pct", "audit_flag"
        ]].rename(columns={
            "digit": "First Digit",
            "observed_count": "Observed Count",
            "actual_pct": "Empirical %",
            "benford_pct": "Benford Theoretical %",
            "deviation_pct": "Deviation Δ (%)",
            "audit_flag": "Forensic Audit Status"
        }),
        use_container_width=True
    )

with tab2:
    st.subheader("Contract Splitting & Statutory Threshold Circumvention (Smurfing)")
    st.markdown("""
    Under the **Federal Acquisition Regulation (FAR)**, simplified acquisition procedures allow agencies to award 
    contracts up to **$250,000** (and **$10,000** for micro-purchases) with minimal competitive oversight.
    Corrupt contractors and procurement officers frequently **split large contracts into multiple awards positioned 
    just below these thresholds** (e.g. $220,000 to $249,999) to bypass open tender requirements.
    """)
    
    st.dataframe(
        splitting_df[[
            "awarding_agency", "awarding_sub_agency", "normalized_vendor", "threshold_risk_category",
            "split_contract_count", "total_split_value_usd", "avg_award_value_usd"
        ]].rename(columns={
            "awarding_agency": "Cabinet Agency",
            "awarding_sub_agency": "Sub-Agency Bureau",
            "normalized_vendor": "Contractor Entity",
            "threshold_risk_category": "Threshold Risk Band",
            "split_contract_count": "Awards in Danger Zone",
            "total_split_value_usd": "Total Cumulative Spend ($)",
            "avg_award_value_usd": "Avg Award Size ($)"
        }),
        use_container_width=True
    )

with tab3:
    st.subheader("Agency Supplier Concentration & Market Monopoly (HHI Index)")
    st.markdown("""
    The **Herfindahl-Hirschman Index (HHI)** is the standard metric used by the **US Department of Justice (DOJ)** 
    and **Federal Trade Commission (FTC)** to detect monopolistic market concentration:
    - **HHI < 1,500:** Competitive Market (Green)
    - **1,500 ≤ HHI ≤ 2,500:** Moderately Concentrated (Orange)
    - **HHI > 2,500:** **Highly Concentrated / Severe Vendor Monopoly Risk (Red)**
    """)
    
    fig_hhi = px.bar(
        hhi_df.head(10),
        x="awarding_agency",
        y="hhi_index",
        color="market_competitiveness_tier",
        color_discrete_map={
            "COMPETITIVE": "#10b981",
            "MODERATELY CONCENTRATED": "#f59e0b",
            "HIGHLY CONCENTRATED (MONOPOLY RISK)": "#ef4444"
        },
        title="Top Federal Agencies by Vendor Concentration (HHI Score)",
        labels={"awarding_agency": "Federal Agency", "hhi_index": "HHI Monopoly Index"}
    )
    fig_hhi.update_layout(template="plotly_dark", height=430)
    st.plotly_chart(fig_hhi, use_container_width=True)
    
    st.dataframe(
        hhi_df[[
            "awarding_agency", "total_agency_contracts", "unique_vendors", "total_spend_usd",
            "hhi_index", "top_contractor", "top_contractor_share_pct", "market_competitiveness_tier"
        ]].rename(columns={
            "awarding_agency": "Federal Agency",
            "total_agency_contracts": "Total Contracts",
            "unique_vendors": "Distinct Vendors",
            "total_spend_usd": "Total Spend ($ USD)",
            "hhi_index": "HHI Index",
            "top_contractor": "Dominant Contractor",
            "top_contractor_share_pct": "Dominant Share %",
            "market_competitiveness_tier": "DOJ Competitiveness Status"
        }),
        use_container_width=True
    )

st.sidebar.title("🕵️‍♂️ Forensic Controls")
st.sidebar.info(f"""
- **Lakehouse:** DuckDB Forensic SQL
- **Audited Spend:** `${total_spend/1e9:,.1f} Billion`
- **Vendors Screened:** `{unique_vendors:,}` Entities
- **Compliance Standard:** DOJ / FAR / Benford
""")

if st.sidebar.button("🔄 Rerun USASpending Live Forensic Ingestion"):
    with st.spinner("Streaming real-time procurement awards & executing forensic audits..."):
        import subprocess
        subprocess.run(["python", os.path.join(BASE_DIR, "ingest_engine", "ingest_contracts.py")], check=True)
        subprocess.run(["python", os.path.join(BASE_DIR, "models", "forensic_analysis.py")], check=True)
        st.cache_data.clear()
        st.success("Forensic Lakehouse refreshed with latest federal awards!")
        st.rerun()
