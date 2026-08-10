import streamlit as st
import pandas as pd
import io

# 1. Page Configuration
st.set_page_config(
    page_title="UTR Transaction Tracer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS for Modern UI
st.markdown("""
<style>
    /* Main layout tuning */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Headers styling */
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    /* Custom metric cards */
    [data-testid="stMetricValue"] {
        font-size: 1.6rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 3. Fast Caching Mechanism for File Loading
@st.cache_data(show_spinner=False)
def load_excel_data(uploaded_file):
    return pd.read_excel(uploaded_file)

# 4. Optimized DFS Algorithm Function
def trace_utr_layers(df_raw):
    sender_col = 'Account No./ (Wallet /PG/PA) Id'
    beneficiary_col = 'Account No' 
    utr_col = 'Transaction Id / UTR Number'
    date_col = 'Transaction Date'
    amount_col = 'Transaction Amount'
    layer_col = 'Layer'

    final_report = []
    serial_no = 1

    def find_linked_transactions(current_utr, current_beneficiary, current_layer_num):
        next_layer_str = str(current_layer_num + 1)
        
        linked_txns = df_raw[
            (df_raw[sender_col] == current_beneficiary) & 
            (df_raw[layer_col].astype(str).str.contains(next_layer_str, na=False))
        ]

        for _, txn in linked_txns.iterrows():
            final_report.append({
                "S. No.": "",  # Blank for inner layers
                "Layer": f"Layer {current_layer_num + 1}",
                "Amount debited from ICICI A/c No.": txn[sender_col],
                "UTR No. And Date": f"{txn[utr_col]} | {txn[date_col]}",
                "Amount Rs.": txn[amount_col],
                "Amount credited into A/c No.": txn[beneficiary_col],
                "Name and address of account holder": "N/A" 
            })
            
            find_linked_transactions(txn[utr_col], txn[beneficiary_col], current_layer_num + 1)

    layer_1_txns = df_raw[df_raw[layer_col].astype(str).str.contains("1", na=False)]
    
    for _, l1_txn in layer_1_txns.iterrows():
        final_report.append({
            "S. No.": serial_no,
            "Layer": "Layer 1",
            "Amount debited from ICICI A/c No.": l1_txn[sender_col],
            "UTR No. And Date": f"{l1_txn[utr_col]} | {l1_txn[date_col]}",
            "Amount Rs.": l1_txn[amount_col],
            "Amount credited into A/c No.": l1_txn[beneficiary_col],
            "Name and address of account holder": "N/A"
        })
        
        find_linked_transactions(l1_txn[utr_col], l1_txn[beneficiary_col], 1)
        serial_no += 1

    return pd.DataFrame(final_report)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/data-configuration.png", width=64)
    st.title("Control Panel")
    st.write("Upload your transaction spreadsheet below.")
    
    uploaded_file = st.file_uploader("Drag & drop your .xlsx file", type=["xlsx"])
    st.divider()
    st.caption("⚡ Powered by DFS Graph Algorithms & Streamlit")

# --- MAIN CONTENT AREA ---
st.markdown('<div class="main-header">🔍 UTR Transaction Tracer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated Layer Graph Traversal & Financial Trail Formatting</div>', unsafe_allow_html=True)

if uploaded_file is not None:
    try:
        # Load data fast with cache
        df_raw = load_excel_data(uploaded_file)

        # Tabbed Layout
        tab_report, tab_raw, tab_info = st.tabs(["📊 Traced Report", "📋 Raw Dataset Preview", "ℹ️ How it Works"])

        with tab_raw:
            st.subheader("Raw Input Data")
            st.dataframe(df_raw, use_container_width=True, height=400)

        with tab_report:
            col_btn, _ = st.columns([1, 3])
            with col_btn:
                run_btn = st.button("🚀 Process & Trace Trail", use_container_width=True)

            # Perform tracing if button is clicked or if already stored in session
            if run_btn or 'traced_df' in st.session_state:
                if run_btn:
                    with st.spinner("Executing Depth-First Traversal across layers..."):
                        st.session_state.traced_df = trace_utr_layers(df_raw)

                df_traced = st.session_state.traced_df

                # Metrics Dashboard Summary
                st.write("---")
                m1, m2, m3 = st.columns(3)
                
                layer1_count = len(df_traced[df_traced['Layer'] == 'Layer 1'])
                total_txns = len(df_traced)
                
                m1.metric("Layer 1 Root Traces", layer1_count)
                m2.metric("Total Traced Nodes", total_txns)
                m3.metric("Nested Layers Discovered", total_txns - layer1_count)

                st.write("### Formatted Hierarchical Trail")
                st.dataframe(df_traced, use_container_width=True, height=450)

                # Download Options
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_traced.to_excel(writer, index=False, sheet_name='Traced_Trail')

                st.download_button(
                    label="📥 Download Formatted Spreadsheet (.xlsx)",
                    data=output.getvalue(),
                    file_name="Traced_Transaction_Trail.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=False
                )

        with tab_info:
            st.markdown("""
            ### Algorithm Architecture
            * **Ingestion:** Parses input dataset while caching structured rows in memory.
            * **Root Identification:** Extracts all `Layer 1` root transactions and assigns primary Serial Numbers (`1, 2, 3...`).
            * **Recursive DFS Traversal:** Connects accounts where `Beneficiary Account (N)` becomes `Sender Account (N+1)`.
            * **Clean Hierarchy Formatting:** Leaves inner layer `S. No.` fields intentionally blank to preserve structural visual grouping.
            """)

    except Exception as e:
        st.error(f"Error parsing file: {e}. Please ensure header names match the required schema.")
else:
    # Empty State Landing
    st.info("👈 Please upload a `.xlsx` transaction log file in the sidebar to begin tracing.")