import pandas as pd
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# -----------------------------
# UN SANCTIONS XML EXTRACTION
# -----------------------------import streamlit as st

def main():
    st.title("Sanctioned Name Watchlist Checker")
    st.write("Click below to fetch latest data")

    if st.button("Fetch All Names"):
        # This must return a DataFrame or data to display
        df = combine_all_watchlists()  # Your logic
        st.success(f"{len(df)} names extracted.")
        st.dataframe(df)

if __name__ == "__main__":
    main()


def extract_un_sanctions_names():
    url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    response = requests.get(url)
    root = ET.fromstring(response.content)

    namespaces = {'default': 'http://www.un.org/sanctions/1.0'}

    names = []

    for individual in root.findall("default:INDIVIDUAL", namespaces):
        full_name = individual.findtext("default:INDIVIDUAL_NAME", default='', namespaces=namespaces).strip()
        if full_name:
            names.append({'Name': full_name, 'Source': 'UN'})

    for entity in root.findall("default:ENTITY", namespaces):
        entity_name = entity.findtext("default:ENTITY_NAME", default='', namespaces=namespaces).strip()
        if entity_name:
            names.append({'Name': entity_name, 'Source': 'UN'})

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

# Example usage:
# combined_watchlist_df = combine_all_watchlists()
# print(combined_watchlist_df.head())
