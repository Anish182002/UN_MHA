import requests
import xml.etree.ElementTree as ET
import pandas as pd
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

# === UN Sanctions ===
def fetch_un_names():
    url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    ns = {'sanctions': 'http://www.un.org/sanctions/1.0'}
    names = []

    for individual in root.findall(".//INDIVIDUAL"):
        full_name = individual.findtext("FIRST_NAME", "") + " " + individual.findtext("SECOND_NAME", "") + " " + individual.findtext("THIRD_NAME", "") + " " + individual.findtext("FOURTH_NAME", "")
        full_name = ' '.join(full_name.split())  # Clean extra spaces
        if full_name:
            names.append(("UN Consolidated List", full_name.strip()))

    for entity in root.findall(".//ENTITY"):
        name = entity.findtext("FIRST_NAME", "")
        if name:
            names.append(("UN Consolidated List", name.strip()))

    return names

# === MHA Banned Organizations ===
def fetch_mha_org_names():
    url = "https://www.mha.gov.in/en/banned-organisations"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.content, "lxml")
    content = soup.find("div", class_="field--name-body")
    names = []

    if content:
        items = content.find_all(["p", "li"])
        for item in items:
            text = item.get_text(strip=True)
            if text and len(text.split()) > 1:
                names.append(("MHA - Banned Organizations", text))
    return names

# === MHA Individual Terrorists ===
def fetch_mha_individual_names():
    url = "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.content, "lxml")
    table = soup.find("table")
    names = []

    if table:
        rows = table.find_all("tr")[1:]  # Skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                name = cols[1].get_text(strip=True)
                if name:
                    names.append(("MHA - Individual Terrorist", name))
    return names

# === MHA Unlawful Associations ===
def fetch_mha_unlawful_associations():
    url = "https://www.mha.gov.in/en/commoncontent/unlawful-associations-under-section-3-of-unlawful-activities-prevention-act-1967"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.content, "lxml")
    content = soup.find("div", class_="field--name-body")
    names = []

    if content:
        blocks = content.find_all(["p", "li"])
        for block in blocks:
            text = block.get_text(strip=True)
            if text and len(text.split()) > 1 and not text.isdigit():
                names.append(("MHA - Unlawful Associations", text))
    return names

# === Load customer Excel names ===
def load_customer_names():
    df = pd.read_excel("customers.xlsx", engine="openpyxl")
    name_columns = ["Customer Name", "Owner Name", "Beneficiary Name", "Insured Name"]
    customers = []

    for col in name_columns:
        if col in df.columns:
            customers += df[col].dropna().astype(str).tolist()

    return list(set(customers))  # remove duplicates

# === Compare and Find Sanctioned Names Not in Excel ===
def find_unmatched_sanctioned_names(sanctioned_names, customer_names):
    not_in_excel = []
    for source, sanctioned in sanctioned_names:
        if all(fuzz.partial_ratio(sanctioned.lower(), customer.lower()) < 85 for customer in customer_names):
            not_in_excel.append((source, sanctioned))
    return not_in_excel

# === Main ===
def main():
    sanctioned_names = (
        fetch_un_names() +
        fetch_mha_org_names() +
        fetch_mha_individual_names() +
        fetch_mha_unlawful_associations()
    )
    customer_names = load_customer_names()
    unmatched = find_unmatched_sanctioned_names(sanctioned_names, customer_names)

    df = pd.DataFrame(unmatched, columns=["Source", "Sanctioned Name"])
    df.to_csv("sanctioned_names_not_in_excel.csv", index=False)
    print(f"✅ Done! {len(unmatched)} names not found in Excel saved to 'sanctioned_names_not_in_excel.csv'")

if __name__ == "__main__":
    main()
