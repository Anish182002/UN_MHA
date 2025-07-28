import streamlit as st
import pandas as pd 
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# --------- UN Sanctions List XML Parser ---------
def fetch_un_sanctions_list():
    url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    response = requests.get(url)
    response.raise_for_status()
    root = ET.fromstring(response.content)

    names = []
    for individual in root.findall(".//INDIVIDUAL"):
        for name in individual.findall("INDIVIDUAL_ALIAS/ALIAS_NAME"):
            names.append({"Name": name.text.strip(), "Source": "UN Sanctions List"})
        for name in individual.findall("INDIVIDUAL_NAME1/\*[@NAME]"):
            names.append({"Name": name.attrib['NAME'].strip(), "Source": "UN Sanctions List"})

    for entity in root.findall(".//ENTITY"):
        for name in entity.findall("ENTITY_ALIAS/ALIAS_NAME"):
            names.append({"Name": name.text.strip(), "Source": "UN Sanctions List"})
        for name in entity.findall("ENTITY_NAME"):
            names.append({"Name": name.text.strip(), "Source": "UN Sanctions List"})

    df = pd.DataFrame(names)
    return df.dropna(subset=["Name"])

# --------- MHA: Banned Organisations ---------
def fetch_mha_banned_organisations():
    url = "https://www.mha.gov.in/en/banned-organisations"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    banned = []

    for li in soup.select(".content-area ul li"):
        name = li.text.strip()
        if name:
            banned.append({"Name": name, "Source": "MHA Banned Organisations"})

    return pd.DataFrame(banned)

# --------- MHA: Individual Terrorists ---------
def fetch_mha_individual_terrorists():
    url = "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    individuals = []

    for li in soup.select(".content-area ul li"):
        name = li.text.strip()
        if name:
            individuals.append({"Name": name, "Source": "MHA Individual Terrorists"})

    return pd.DataFrame(individuals)

# --------- MHA: Unlawful Associations ---------
def fetch_mha_unlawful_associations():
    url = "https://www.mha.gov.in/en/commoncontent/unlawful-associations-under-section-3-of-unlawful-activities-prevention-act-1967"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    associations = []

    for li in soup.select(".content-area ul li"):
        name = li.text.strip()
        if name:
            associations.append({"Name": name, "Source": "MHA Unlawful Associations"})

    return pd.DataFrame(associations)

# --------- Combine Watchlists ---------
def combine_all_watchlists():
    try:
        un_df = fetch_un_sanctions_list()
    except Exception as e:
        print(f"UN list error: {e}")
        un_df = pd.DataFrame(columns=["Name", "Source"])

    try:
        mha_banned_df = fetch_mha_banned_organisations()
    except Exception as e:
        print(f"MHA banned org error: {e}")
        mha_banned_df = pd.DataFrame(columns=["Name", "Source"])

    try:
        mha_individual_df = fetch_mha_individual_terrorists()
    except Exception as e:
        print(f"MHA individuals error: {e}")
        mha_individual_df = pd.DataFrame(columns=["Name", "Source"])

    try:
        mha_unlawful_df = fetch_mha_unlawful_associations()
    except Exception as e:
        print(f"MHA unlawful assoc error: {e}")
        mha_unlawful_df = pd.DataFrame(columns=["Name", "Source"])

    dfs = [un_df, mha_banned_df, mha_individual_df, mha_unlawful_df]
    valid_dfs = [df for df in dfs if not df.empty and "Name" in df.columns]

    if not valid_dfs:
        raise ValueError("No valid dataframes found with 'Name' column.")

    combined = pd.concat(valid_dfs, ignore_index=True)
    combined["Name"] = combined["Name"].astype(str).str.strip()
    return combined

# --------- Streamlit UI ---------
st.set_page_config(page_title="Sanctions Screening", layout="wide")
st.title("🚨 Name Screening Against Sanctions Lists")

uploaded_file = st.file_uploader("Upload Excel file with names to screen", type=["xlsx"])

if uploaded_file:
    try:
        customer_df = pd.read_excel(uploaded_file)
        st.write("### Uploaded Customer Data", customer_df)

        if "Name" not in customer_df.columns:
            st.error("Uploaded file must contain a 'Name' column")
        else:
            watchlist_df = combine_all_watchlists()
            watchlist_names = set(watchlist_df["Name"].str.lower())

            def check_name(name):
                return any(name.lower() in wl_name for wl_name in watchlist_names)

            customer_df["Potential Match"] = customer_df["Name"].astype(str).apply(check_name)
            matches = customer_df[customer_df["Potential Match"] == True]

            st.success(f"✅ {len(matches)} potential match(es) found.")
            st.write("### Matches", matches)
    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("Please upload an Excel file to begin screening.")
