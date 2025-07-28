import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from io import BytesIO

def fetch_un_names():
    url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    names = set()
    for individual in root.findall(".//INDIVIDUAL"):
        full_name = " ".join([
            individual.findtext("FIRST_NAME", default=""),
            individual.findtext("SECOND_NAME", default=""),
            individual.findtext("THIRD_NAME", default=""),
            individual.findtext("FOURTH_NAME", default="")
        ]).strip()
        if full_name:
            names.add(full_name.upper())
    return names

def fetch_mha_banned_orgs():
    url = "https://www.mha.gov.in/en/banned-organisations"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    names = set()
    for li in soup.select(".content li"):
        name = li.get_text(strip=True)
        if name:
            names.add(name.upper())
    return names

def fetch_mha_individuals():
    url = "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    names = set()
    for td in soup.select("table td"):
        text = td.get_text(strip=True)
        if text.isupper() and len(text.split()) >= 2:
            names.add(text.upper())
    return names

def main():
    st.title("Sanction List New Name Checker")
    st.write("Upload your existing Excel file to check if any **new sanctioned names** are added on official websites.")

    uploaded_file = st.file_uploader("Upload your Excel file (with a column of names)", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        excel_names = set(df.iloc[:, 0].dropna().astype(str).str.upper())

        with st.spinner("Fetching live sanctioned names..."):
            un_names = fetch_un_names()
            mha_org_names = fetch_mha_banned_orgs()
            mha_indiv_names = fetch_mha_individuals()

        all_live_names = un_names.union(mha_org_names).union(mha_indiv_names)

        new_names = all_live_names - excel_names

        if new_names:
            st.success(f"Found {len(new_names)} new names that are not in your Excel file!")
            new_data = pd.DataFrame(sorted(new_names), columns=["New Name"])
            st.dataframe(new_data)

            download = st.download_button("Download New Names", new_data.to_csv(index=False), "new_names.csv")
        else:
            st.info("No new names found. Your list is up-to-date!")

        if st.checkbox("Show all live names from websites"):
            all_data = pd.DataFrame(sorted(all_live_names), columns=["Live Name"])
            st.dataframe(all_data)

if __name__ == "__main__":
    main()
