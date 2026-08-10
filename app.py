import streamlit as st
import pandas as pd
import io

# Web App Title and Description
st.set_page_config(page_title="AI Sheets: UTR Tracer", layout="centered")
st.title("📊 UTR Transaction Tracer")
st.write("Upload a raw transaction spreadsheet to automatically trace layers and generate a formatted report.")

# 1. File Upload Interface
uploaded_file = st.file_uploader("Upload your raw dataset (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # 2. Read the uploaded file directly from memory
        df_raw = pd.read_excel(uploaded_file)
        st.success("File uploaded successfully!")
        st.write("Preview of Raw Data:")
        st.dataframe(df_raw.head(3))
        
        if st.button("Generate Traced Trail"):
            with st.spinner("Tracing transactions..."):
                
                # Setup columns based on your dataset
                sender_col = 'Account No./ (Wallet /PG/PA) Id'
                beneficiary_col = 'Account No' 
                utr_col = 'Transaction Id / UTR Number'
                date_col = 'Transaction Date'
                amount_col = 'Transaction Amount'
                layer_col = 'Layer'

                final_report = []
                serial_no = 1

                # 3. The recursive DFS (Depth-First Search) algorithm
                def find_linked_transactions(current_utr, current_beneficiary, current_layer_num):
                    next_layer_str = str(current_layer_num + 1)
                    
                    linked_txns = df_raw[
                        (df_raw[sender_col] == current_beneficiary) & 
                        (df_raw[layer_col].astype(str).str.contains(next_layer_str, na=False))
                    ]

                    for _, txn in linked_txns.iterrows():
                        final_report.append({
                            "S. No.": "", # Blank for inner layers
                            "Layer": f"Layer {current_layer_num + 1}",
                            "Amount debited from ICICI A/c No.": txn[sender_col],
                            "UTR No. And Date": f"{txn[utr_col]} | {txn[date_col]}",
                            "Amount Rs.": txn[amount_col],
                            "Amount credited into A/c No.": txn[beneficiary_col],
                            "Name and address of account holder": "N/A" 
                        })
                        
                        find_linked_transactions(txn[utr_col], txn[beneficiary_col], current_layer_num + 1)

                # 4. Start the traversal with Layer 1
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

                # 5. Prepare Output DataFrame
                df_final = pd.DataFrame(final_report)
                
                st.success("Tracing Complete!")
                st.write("Preview of Formatted Report:")
                st.dataframe(df_final)

                # 6. Create Download Button
                # We save to a virtual memory buffer so the user can download it directly from the web browser
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, sheet_name='Traced_Trail')
                
                st.download_button(
                    label="⬇️ Download Formatted Spreadsheet",
                    data=output.getvalue(),
                    file_name="Traced_Output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"An error occurred: {e}. Please ensure the uploaded file has the correct columns.")