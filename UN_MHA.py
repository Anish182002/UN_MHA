import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

# ----------- Function to extract names from UN website -----------
def extract_names_un():
    url = "https://scsanctions.un.org/kho39en-all.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    names = []

    # Extract paragraphs and try to get names
    for para in soup.find_all("p"):
        text = para.get_text(strip=True)
        if any(x in text for x in ["Name:", "A.k.a."]):
            parts = text.split("Name:")
            for part in parts[1:]:
                name = part.split("\n")[0].strip().split("A.k.a.")[0].strip()
                if name:
                    names.append(name)
    return list(set(names))

# ----------- Function to extract names from MHA websites -----------

def extract_names_mha_banned_orgs():
    url = "https://www.mha.gov.in/en/banned-organisations"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    names = []
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if text:
            names.append(text)
    return list(set(names))

def extract_names_mha_individual_terrorists():
    url = "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    names = []
    for div in soup.find_all("div", class_="views-field-title"):
        text = div.get_text(strip=True)
        if text:
            names.append(text)
    return list(set(names))

def extract_names_mha_unlawful_associations():
    url = "https://www.mha.gov.in/en/commoncontent/unlawful-associations-under-section-3-of-unlawful-activities-prevention-act-1967"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    names = []
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if text:
            names.append(text)
    return list(set(names))

# ----------- Fuzzy Matching Function -----------
def is_match(name, list_of_names, threshold=90):
    for sanctioned_name in list_of_names:
        score = fuzz.token_set_ratio(name.lower(), sanctioned_name.lower())
        if score >= threshold:
            return True
    return False

# ----------- Streamlit Web App UI -----------
st.title("🔍 Name Screening System - Missing Names Finder")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if "Name" not in df.columns:
        st.error("Excel file must contain a 'Name' column.")
    else:
        customer_names = df["Name"].dropna().astype(str).tolist()

        st.info("Extracting names from sanction websites...")

        un_names = extract_names_un()
        mha_banned_orgs = extract_names_mha_banned_orgs()
        mha_individuals = extract_names_mha_individual_terrorists()
        mha_unlawful = extract_names_mha_unlawful_associations()

        sanctioned_names = list(set(un_names + mha_banned_orgs + mha_individuals + mha_unlawful))

        # Compare: Show names in sanctioned list that are NOT found in Excel
        not_found = [name for name in sanctioned_names if not is_match(name, customer_names)]

        st.success(f"✅ Total sanctioned names collected: {len(sanctioned_names)}")
        st.warning(f"⚠️ Sanctioned names NOT found in your Excel file: {len(not_found)}")

        if not_found:
            st.dataframe(pd.DataFrame(not_found, columns=["Sanctioned Name Not in Excel"]))
            st.download_button("📥 Download Missing Names", pd.DataFrame(not_found, columns=["Sanctioned Name Not in Excel"]).to_csv(index=False), file_name="missing_names.csv")

