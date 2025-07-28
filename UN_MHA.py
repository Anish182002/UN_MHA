import streamlit as st
import pandas as pd
from io import BytesIO
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
import re

# Title
st.title("Sanctioned Name Screening System")

# Upload Excel File
uploaded_file = st.file_uploader("Upload Customer Excel File", type=["xlsx"])
if uploaded_file:
    customer_df = pd.read_excel(uploaded_file)
    customer_names = customer_df['Name'].astype(str).tolist()

    # Preprocess function
    def preprocess(name):
        return re.sub(r'[^a-zA-Z ]', '', name.lower()).strip()

    preprocessed_customer_names = [preprocess(name) for name in customer_names]

    # Fetch UN Sanctions List (XML)
    def fetch_un_names():
        url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
        resp = requests.get(url)
        root = ET.fromstring(resp.content)
        names = []
        for name_elem in root.findall(".//INDIVIDUALS/INDIVIDUAL/INDIVIDUAL_NAME"):
            full_name = " ".join([child.text for child in name_elem if child.text])
            names.append(full_name.strip())
        return names

    # Fetch MHA India banned organizations
    def fetch_mha_org_names():
        url = "https://www.mha.gov.in/en/banned-organisations"
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'lxml')
        items = soup.select(".view-content div")
        return [item.get_text(strip=True) for item in items if item.get_text(strip=True)]

    # Fetch MHA India individual terrorists
    def fetch_mha_individual_names():
        url = "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa"
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'lxml')
        table = soup.find("table")
        rows = table.find_all("tr")[1:]  # Skip header
        return [row.find_all("td")[1].get_text(strip=True) for row in rows if row.find_all("td")]

    # Aggregate sanctioned names
    sanctioned_names = fetch_un_names() + fetch_mha_org_names() + fetch_mha_individual_names()
    sanctioned_names = list(set(preprocess(name) for name in sanctioned_names))

    # Match and find missing names
    missing_sanctioned = []
    for s_name in sanctioned_names:
        match_found = any(fuzz.token_set_ratio(s_name, c_name) > 90 for c_name in preprocessed_customer_names)
        if not match_found:
            missing_sanctioned.append(s_name)

    # Display missing sanctioned names in chunks
    st.subheader(f"Sanctioned Names NOT Found in Uploaded Excel ({len(missing_sanctioned)})")

    if missing_sanctioned:
        chunk_size = 100
        for i in range(0, len(missing_sanctioned), chunk_size):
            with st.expander(f"Show names {i} to {i + chunk_size}"):
                st.write(missing_sanctioned[i:i + chunk_size])

        # Download button
        df_missing = pd.DataFrame(missing_sanctioned, columns=["Sanctioned Name"])
        csv = df_missing.to_csv(index=False).encode('utf-8')
        st.download_button("Download Missing Sanctioned Names", csv, file_name="missing_sanctioned_names.csv")
    else:
        st.success("All sanctioned names are matched in the uploaded Excel!")
else:
    st.info("Please upload an Excel file with a column named 'Name'.")
