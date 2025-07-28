import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from rapidfuzz import fuzz
import re

# Function to load Excel file
def load_customer_data(file):
    return pd.read_excel(file)

# Function to extract names from UN XML sanctions list
def extract_un_sanctions_xml():
    url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    namespaces = {'ns': 'http://www.un.org/sanctions/1.0'}
    names = set()

    for individual in root.findall(".//INDIVIDUAL"):
        full_name = " ".join([
            individual.findtext("FIRST_NAME") or '',
            individual.findtext("SECOND_NAME") or '',
            individual.findtext("THIRD_NAME") or '',
            individual.findtext("FOURTH_NAME") or ''
        ]).strip()
        if full_name:
            names.add(full_name.upper())

    for entity in root.findall(".//ENTITY"):
        entity_name = entity.findtext("NAME")
        if entity_name:
            names.add(entity_name.upper())

    return names

# Function to extract names from UN HTML site (unstructured)
def extract_un_html_names():
    url = "https://scsanctions.un.org/kho39en-all.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text()
    lines = text.splitlines()

    names = set()
    for line in lines:
        if re.match(r"^[A-Z][A-Z\s,.'\-]+$", line.strip()):  # crude filter for names
            name = line.strip()
            if len(name.split()) >= 2:
                names.add(name.upper())
    return names

# Function to extract names from MHA India sites
def extract_mha_website_names(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    names = set()

    for tag in soup.find_all(['li', 'p', 'td']):
        text = tag.get_text().strip()
        if 4 <= len(text.split()) <= 8:
            names.add(text.upper())

    return names

# Fuzzy matching function
def fuzzy_match(name, sanctioned_names, threshold=85):
    matched = []
    for sanctioned in sanctioned_names:
        score = fuzz.token_sort_ratio(name.upper(), sanctioned.upper())
        if score >= threshold:
            matched.append((sanctioned, score))
    return matched

# Streamlit UI
st.title("🛡️ Name Screening Against Sanction Lists")

uploaded_file = st.file_uploader("Upload Excel File (with Name column):", type=["xlsx"])

if uploaded_file:
    df = load_customer_data(uploaded_file)
    if 'Name' not in df.columns:
        st.error("Excel must have a column named 'Name'")
    else:
        st.success("Excel file uploaded successfully.")

        st.info("Extracting sanctioned names from sources...")
        sanctioned_names = set()
        sanctioned_names.update(extract_un_sanctions_xml())
        sanctioned_names.update(extract_un_html_names())

        # MHA sites
        mha_urls = [
            "https://www.mha.gov.in/en/banned-organisations",
            "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa",
            "https://www.mha.gov.in/en/commoncontent/unlawful-associations-under-section-3-of-unlawful-activities-prevention-act-1967",
            "https://www.mha.gov.in/en/commoncontent/list-of-organisations-designated-%E2%80%98terrorist-organizations%E2%80%99-under-section-35-of"
        ]
        for url in mha_urls:
            sanctioned_names.update(extract_mha_website_names(url))

        st.success(f"Total unique sanctioned names extracted: {len(sanctioned_names)}")

        st.info("Performing name screening using fuzzy matching...")
        matches = []
        for idx, row in df.iterrows():
            name = str(row['Name'])
            matched = fuzzy_match(name, sanctioned_names)
            if matched:
                for sanctioned_name, score in matched:
                    matches.append({
                        'Customer Name': name,
                        'Matched Sanctioned Name': sanctioned_name,
                        'Score': score
                    })

        if matches:
            results_df = pd.DataFrame(matches)
            st.subheader("🚨 Matches Found")
            st.dataframe(results_df)

            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Results as CSV", data=csv, file_name="matches.csv", mime="text/csv")
        else:
            st.success("✅ No matches found against the sanction lists.")
