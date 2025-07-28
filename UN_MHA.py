import pandas as pd
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import streamlit as st

# -----------------------------
# UN SANCTIONS XML EXTRACTION
# -----------------------------

def extract_un_sanctions_names():
    url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    response = requests.get(url)
    root = ET.fromstring(response.content)

    namespaces = {'default': 'http://www.un.org/sanctions/1.0'}
    names = []

    for individual in root.findall("default:INDIVIDUAL", namespaces):
        for name_el in individual.findall("default:INDIVIDUAL_NAME", namespaces):
            full_name = name_el.text.strip() if name_el.text else ''
            if full_name:
                names.append({'Name': full_name, 'Source': 'UN - Individual'})

    for entity in root.findall("default:ENTITY", namespaces):
        for entity_name_el in entity.findall("default:ENTITY_NAME", namespaces):
            entity_name = entity_name_el.text.strip() if entity_name_el.text else ''
            if entity_name:
                names.append({'Name': entity_name, 'Source': 'UN - Entity'})

    return pd.DataFrame(names)

# -----------------------------
# MHA LISTS EXTRACTION
# -----------------------------

def extract_mha_banned_orgs():
    url = "https://www.mha.gov.in/en/banned-organisations"
    soup = BeautifulSoup(requests.get(url).content, "lxml")
    items = soup.select(".field-item.even li")
    return pd.DataFrame([{'Name': i.get_text(strip=True), 'Source': 'MHA - Banned Organisations'} for i in items])

def extract_mha_individual_terrorists():
    url = "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa"
    soup = BeautifulSoup(requests.get(url).content, "lxml")
    items = soup.select(".field-item.even li")
    return pd.DataFrame([{'Name': i.get_text(strip=True), 'Source': 'MHA - Individual Terrorists'} for i in items])

def extract_mha_unlawful_associations():
    url = "https://www.mha.gov.in/en/commoncontent/unlawful-associations-under-section-3-of-unlawful-activities-prevention-act-1967"
    soup = BeautifulSoup(requests.get(url).content, "lxml")
    items = soup.select(".field-item.even li")
    return pd.DataFrame([{'Name': i.get_text(strip=True), 'Source': 'MHA - Unlawful Associations'} for i in items])

# -----------------------------
# COMBINE ALL SOURCES
# -----------------------------

def combine_all_watchlists():
    df_un = extract_un_sanctions_names()
    df_orgs = extract_mha_banned_orgs()
    df_terrorists = extract_mha_individual_terrorists()
    df_associations = extract_mha_unlawful_associations()
    combined = pd.concat([df_un, df_orgs, df_terrorists, df_associations], ignore_index=True)
    combined["Name"] = combined["Name"].str.strip()
    return combined.drop_duplicates()

# -----------------------------
# STREAMLIT APP
# -----------------------------

def main():
    st.title("Sanctioned Name Watchlist Checker")
    st.write("Click below to fetch and display the latest names from UN and MHA sites.")

    if st.button("Fetch All Names"):
        with st.spinner("Fetching data from all sources..."):
            df = combine_all_watchlists()
        st.success(f"{len(df)} names extracted.")
        st.dataframe(df)

if __name__ == "__main__":
    main()
