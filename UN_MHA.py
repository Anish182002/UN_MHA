import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# --- Fetch UN sanctioned names ---
def fetch_un_names():
    url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    response = requests.get(url)
    names = []
    if response.status_code == 200:
        from xml.etree import ElementTree as ET
        root = ET.fromstring(response.content)
        for individual in root.findall(".//INDIVIDUAL"):
            full_name = individual.findtext("FIRST_NAME", "") + " " + individual.findtext("SECOND_NAME", "") + " " + individual.findtext("THIRD_NAME", "") + " " + individual.findtext("FOURTH_NAME", "")
            full_name = ' '.join(full_name.split())
            if full_name:
                names.append(full_name.strip().upper())
    return names

# --- Fetch MHA banned organizations ---
def fetch_mha_org_names():
    url = "https://www.mha.gov.in/en/banned-organisations"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    names = []

    for li in soup.select("div.field--item ul li"):
        name = li.get_text(strip=True)
        if name:
            names.append(name.strip().upper())
    return names

# --- Fetch MHA individual terrorists ---
def fetch_mha_individual_names():
    url = "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    names = []
    
    table = soup.find("table")
    if table:
        rows = table.find_all("tr")[1:]  # Skip header row
        for row in rows:
            cols = row.find_all("td")
            if len(cols) > 1:
                name = cols[1].get_text(strip=True)
                if name:
                    names.append(name.strip().upper())
    return names

# --- Upload and read Excel file ---
def load_customer_names_from_upload():
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            if "Name" in df.columns:
                names = df["Name"].dropna().str.upper().str.strip().tolist()
                return names
            else:
                st.error("Excel file must contain a column named 'Name'.")
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")
    return []

# --- Main App ---
def main():
    st.title("Sanctioned Name Checker")
    st.write("This tool checks which sanctioned names are **not** present in your Excel list.")

    customer_names = load_customer_names_from_upload()
    if not customer_names:
        st.info("Please upload an Excel file to proceed.")
        st.stop()

    st.success(f"{len(customer_names)} customer names loaded.")

    with st.spinner("Fetching sanctioned names..."):
        un_names = fetch_un_names()
        mha_org_names = fetch_mha_org_names()
        mha_ind_names = fetch_mha_individual_names()

        sanctioned_names = set(un_names + mha_org_names + mha_ind_names)

    missing_names = [name for name in sanctioned_names if name not in customer_names]

    st.header("🚨 Sanctioned names NOT in your list:")
    if missing_names:
        st.write(f"Found {len(missing_names)} names not present in your file:")
        st.write(missing_names)
        df_missing = pd.DataFrame(missing_names, columns=["Sanctioned Name Not Found in File"])
        st.download_button("Download Missing Names", df_missing.to_csv(index=False), "missing_names.csv", "text/csv")
    else:
        st.success("✅ All sanctioned names are present in your Excel file.")

if __name__ == "__main__":
    main()
