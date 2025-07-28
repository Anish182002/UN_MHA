import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from openpyxl import load_workbook

# Function to extract UN sanctioned names from XML
import xml.etree.ElementTree as ET

def fetch_un_names():
    url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    names = []
    for individual in root.findall(".//INDIVIDUAL"):
        first_name = individual.findtext("FIRST_NAME")
        second_name = individual.findtext("SECOND_NAME")
        third_name = individual.findtext("THIRD_NAME")
        full_name = " ".join(filter(None, [first_name, second_name, third_name]))
        if full_name:
            names.append(full_name.strip())
    for entity in root.findall(".//ENTITY"):
        name = entity.findtext("FIRST_NAME")
        if name:
            names.append(name.strip())
    return names

# Function to extract banned organisations from MHA

def fetch_mha_org_names():
    url = "https://www.mha.gov.in/en/banned-organisations"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")
    names = []
    for li in soup.select(".content ul li"):
        name = li.get_text(strip=True)
        if name:
            names.append(name)
    return names

# Function to extract individual terrorists under UAPA

def fetch_mha_individual_names():
    url = "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")
    table = soup.find("table")
    names = []
    if table:
        rows = table.find_all("tr")[1:]  # Skip header
        for row in rows:
            cols = row.find_all("td")
            if cols:
                name = cols[0].get_text(strip=True)
                if name:
                    names.append(name)
    return names

# Name matching logic

def is_name_match(name1, name2, threshold=85):
    return fuzz.token_sort_ratio(name1.lower(), name2.lower()) >= threshold

def screen_names(customer_names, sanctioned_names):
    matches = []
    for cust in customer_names:
        for sanc in sanctioned_names:
            score = fuzz.token_sort_ratio(cust.lower(), sanc.lower())
            if score >= 85:
                matches.append((cust, sanc, score))
    return matches

# Load customer names from Excel

def load_customer_names(uploaded_file):
    df = pd.read_excel(uploaded_file)
    if 'Name' not in df.columns:
        raise ValueError("Excel file must contain a column named 'Name'")
    return df['Name'].dropna().astype(str).tolist()

# Streamlit App

def main():
    st.title("🛡️ Name Screening System (UN & MHA India)")
    st.write("Screen customer names against UN and MHA sanctions lists.")

    uploaded_file = st.file_uploader("Upload customer Excel file (.xlsx)", type=["xlsx"])

    if uploaded_file:
        try:
            customer_names = load_customer_names(uploaded_file)
            st.success(f"Loaded {len(customer_names)} customer names.")
        except Exception as e:
            st.error(f"Error: {e}")
            return

        with st.spinner("Fetching sanctioned names from UN and MHA websites..."):
            sanctioned_names = fetch_un_names() + fetch_mha_org_names() + fetch_mha_individual_names()

        screening_mode = st.selectbox(
            "Choose screening mode",
            ["Find Matches in Customer File", "Find Sanctioned Names NOT in Customer File"]
        )

        if screening_mode == "Find Matches in Customer File":
            st.subheader("Screening for matches...")
            matching_names = screen_names(customer_names, sanctioned_names)

            if matching_names:
                st.success(f"Found {len(matching_names)} matches.")
                df_match = pd.DataFrame(matching_names, columns=["Customer Name", "Matched Sanctioned Name", "Match Score"])
                st.dataframe(df_match)
                st.download_button("Download Matches", df_match.to_csv(index=False), "matches.csv", "text/csv")
            else:
                st.info("No matches found.")

        elif screening_mode == "Find Sanctioned Names NOT in Customer File":
            st.subheader("Finding sanctioned names not in your customer file...")
            not_in_excel = []
            for sanc_name in sanctioned_names:
                if not any(is_name_match(sanc_name, cust_name) for cust_name in customer_names):
                    not_in_excel.append(sanc_name)

            if not_in_excel:
                st.warning(f"Found {len(not_in_excel)} sanctioned names NOT in your customer file.")
                df_missing = pd.DataFrame(not_in_excel, columns=["Sanctioned Name"])
                st.dataframe(df_missing)
                st.download_button("Download Missing Names", df_missing.to_csv(index=False), "sanctioned_names_not_in_excel.csv", "text/csv")
            else:
                st.success("All sanctioned names are accounted for in your customer file.")

if __name__ == "__main__":
    main()
