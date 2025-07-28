import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import openpyxl

# --------- FUNCTIONS TO FETCH NAMES WITH SOURCE TAG ---------

def fetch_un_names():
    url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "xml")
    names = []
    for individual in soup.find_all("INDIVIDUAL"):
        full_name = individual.find("FIRST_NAME")
        second_name = individual.find("SECOND_NAME")
        third_name = individual.find("THIRD_NAME")
        last_name = individual.find("FOURTH_NAME")
        name_parts = [n.text for n in [full_name, second_name, third_name, last_name] if n]
        if name_parts:
            names.append((" ".join(name_parts), "UN List"))
    return names

def fetch_mha_org_names():
    url = "https://www.mha.gov.in/en/banned-organisations"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")
    orgs = []
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if cols:
                org_name = cols[1].get_text(strip=True)
                orgs.append((org_name, "MHA Banned Organizations"))
    return orgs

def fetch_mha_individual_names():
    url = "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")
    individuals = []
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if cols:
                name = cols[1].get_text(strip=True)
                individuals.append((name, "MHA Individual Terrorists"))
    return individuals

# --------- LOAD CUSTOMER EXCEL FILE ---------

def load_customer_names(uploaded_file):
    df = pd.read_excel(uploaded_file)
    names = df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
    return names

# --------- MAIN STREAMLIT APP ---------

st.title("Sanctioned Name Comparison System")

uploaded_file = st.file_uploader("Upload your Excel file (first column should contain names):", type=["xlsx"])

if uploaded_file:
    try:
        customer_names = load_customer_names(uploaded_file)
        st.success(f"Loaded {len(customer_names)} names from Excel.")

        with st.spinner("Fetching sanctioned names..."):
            sanctioned_names = (
                fetch_un_names()
                + fetch_mha_org_names()
                + fetch_mha_individual_names()
            )

        sanctioned_only_names = [name for name, _ in sanctioned_names]
        missing = [(name, source) for name, source in sanctioned_names if name not in customer_names]

        st.subheader("Sanctioned names NOT found in your Excel:")
        st.write(f"Total missing: {len(missing)}")

        if missing:
            df_missing = pd.DataFrame(missing, columns=["Sanctioned Name", "Source"])
            st.dataframe(df_missing)

            csv = df_missing.to_csv(index=False).encode("utf-8")
            st.download_button("Download Missing Names with Source", csv, "missing_names.csv", "text/csv")

    except Exception as e:
        st.error(f"Error processing the file: {e}")
else:
    st.info("Please upload an Excel file to begin.")
