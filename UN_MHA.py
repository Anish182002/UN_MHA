import streamlit as st
import pandas as pd
import requests
import unicodedata
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from io import BytesIO

st.set_page_config(page_title="Sanction Name Checker", layout="wide")

# ---------------------- Normalization -------------------------

def normalize_name(name):
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    name = re.sub(r'\s+', ' ', name).strip().lower()
    return name

# ---------------------- Load Excel -------------------------

def load_excel_names(uploaded_file):
    df = pd.read_excel(uploaded_file)
    names = df.iloc[:, 0].dropna().tolist()
    return set(normalize_name(name) for name in names)

# ---------------------- UN Sanctions List -------------------------

def extract_un_names():
    url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    ns = {'ns': 'http://www.un.org/sanctions/1.0'}
    names = set()
    for entry in root.findall('.//INDIVIDUAL', ns) + root.findall('.//ENTITY', ns):
        for name in entry.findall('.//FIRST_NAME', ns) + entry.findall('.//SECOND_NAME', ns) + \
                    entry.findall('.//THIRD_NAME', ns) + entry.findall('.//FOURTH_NAME', ns) + \
                    entry.findall('.//NAME', ns):
            if name.text:
                names.add(normalize_name(name.text))
    return names

# ---------------------- MHA Banned Organisations -------------------------

def extract_mha_banned_orgs():
    url = "https://www.mha.gov.in/en/banned-organisations"
    soup = BeautifulSoup(requests.get(url).content, 'lxml')
    names = set()
    for tag in soup.find_all(['h3', 'p', 'li']):
        text = tag.get_text(strip=True)
        if text and len(text.split()) >= 2:
            names.add(normalize_name(text))
    return names

# ---------------------- MHA Individual Terrorists -------------------------

def extract_mha_individuals():
    url = "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa"
    soup = BeautifulSoup(requests.get(url).content, 'lxml')
    names = set()
    for tag in soup.find_all(['h3', 'p', 'li', 'td']):
        text = tag.get_text(strip=True)
        if text and len(text.split()) >= 2:
            names.add(normalize_name(text))
    return names

# ---------------------- MHA Section 35 Terrorist Organisations -------------------------

def extract_mha_section35_terror_orgs():
    url = "https://www.mha.gov.in/en/commoncontent/list-of-organisations-designated-%E2%80%98terrorist-organizations%E2%80%99-under-section-35-of"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")
    names = set()
    for tag in soup.find_all(['p', 'li', 'td']):
        text = tag.get_text(strip=True)
        if text and len(text.split()) >= 2:
            names.add(normalize_name(text))
    return names

# ---------------------- Compare Sanction Names with Excel -------------------------

def compare_names(excel_names):
    un_names = extract_un_names()
    mha_orgs = extract_mha_banned_orgs()
    mha_inds = extract_mha_individuals()
    mha_terror_orgs = extract_mha_section35_terror_orgs()

    sanction_names = un_names.union(mha_orgs, mha_inds, mha_terror_orgs)
    missing_names = sanction_names - excel_names

    return sorted(missing_names)

# ---------------------- Excel Download -------------------------

def to_excel_download(data):
    output = BytesIO()
    pd.DataFrame(data, columns=["Sanctioned Name Not in Excel"]).to_excel(output, index=False)
    output.seek(0)
    return output

# ---------------------- Streamlit UI -------------------------

st.title("🔍 Sanction List Name Checker")
st.markdown("Upload your Excel file with customer names to check against the UN and MHA sanctions lists.")

uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        with st.spinner("Reading Excel file..."):
            excel_names = load_excel_names(uploaded_file)

        if st.button("🚨 Scan Against Sanction Lists"):
            with st.spinner("Checking against UN & MHA sanction sources..."):
                missing_names = compare_names(excel_names)

            if missing_names:
                st.success(f"✅ Found {len(missing_names)} sanctioned names not in your Excel.")
                st.dataframe(missing_names, use_container_width=True)

                download = to_excel_download(missing_names)
                st.download_button(
                    label="⬇️ Download Missing Names as Excel",
                    data=download,
                    file_name="missing_sanctioned_names.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("✅ No sanctioned names found missing in your Excel.")
    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.warning("Please upload an Excel file to proceed.")
