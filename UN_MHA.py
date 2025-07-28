import streamlit as st
import pandas as pd

def load_customer_names_from_upload():
    uploaded_file = st.file_uploader("Upload customer Excel file", type=["xlsx"])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            if 'Name' in df.columns:
                names = df['Name'].dropna().tolist()
                return names
            else:
                st.error("The uploaded file must have a 'Name' column.")
                return []
        except Exception as e:
            st.error(f"Error reading the Excel file: {e}")
            return []
    else:
        return None  # No file uploaded yet

def main():
    st.title("UN & MHA Name Screening System")
    
    st.write("Please upload an Excel file with a column named **'Name'**.")

    customer_names = load_customer_names_from_upload()
    if customer_names is None:
        st.stop()  # Wait until file is uploaded

    st.success(f"{len(customer_names)} customer names loaded.")
    
    # TODO: Continue with your name screening logic here using `customer_names`
    # Example:
    for name in customer_names:
        st.write(f"Processing: {name}")
        # perform screening and show results

if __name__ == "__main__":
    main()
