import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

# ----------- Web Scraping Functions -----------

def get_mha_banned_organisations():
    url = "https://www.mha.gov.in/en/banned-organisations"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    return [li.get_text(strip=True) for li in soup.select("ul li") if li.get_text(strip=True)]

def get_mha_individual_terrorists():
    url = "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    return [td.get_text(strip=True) for td in soup.select("table td") if any(char.isalpha() for char in td.get_text())]

def get_un_sanctioned_names():
    url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "xml")
    names = [name.get_text(strip=True) for name in soup.find_all("FIRST_NAME")]
    names += [name.get_text(strip=True) for name in soup.find_all("SECOND_NAME")]
    names += [name.get_text(strip=True) for name in soup.find_all("THIRD_NAME")]
    return list(set([n for n in names if n]))  # remove empty and duplicates

# ----------- Name Matching Function -----------

def fuzzy_match(name1, name2):
    return fuzz.token_sort_ratio(name1.lower(), name2.lower()) > 85

def find_non_matched_names(sanctioned_list, customer_list):
    return [s for s in sanctioned_list if not any(fuzzy_match(s, c) for c in customer_list)]

# ----------- Streamlit App -----------

st.title("🛡️ Sanctioned Name Checker")

uploaded_file = st.file_uploader("Upload your customer Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        all_customer_names = df[df.columns[0]].astype(str).tolist()

        st.success("✅ Excel file loaded successfully.")
        
        with st.spinner("Fetching names from websites..."):
            un_names = get_un_sanctioned_names()
            mha_orgs = get_mha_banned_organisations()
            mha_inds = get_mha_individual_terrorists()

        all_sanctioned = list(set(un_names + mha_orgs + mha_inds))
        
        not_in_excel = find_non_matched_names(all_sanctioned, all_customer_names)

        st.subheader("🔍 Sanctioned Names NOT Found in Excel")
        st.write(not_in_excel)

        st.download_button("Download Missing Sanctioned Names", 
                           pd.DataFrame(not_in_excel, columns=["Sanctioned Name"]).to_csv(index=False), 
                           "sanctioned_names_not_in_excel.csv")

    except Exception as e:
        st.error(f"❌ Failed to process file: {e}")
