import pandas as pd
import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

# --- Function to fetch names from UN consolidated list ---
def get_un_sanctioned_names():
    url = "https://scsanctions.un.org/kho39en-all.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")
    names = []

    for p in soup.find_all("p"):
        text = p.get_text(separator=" ").strip()
        if text and any(char.isalpha() for char in text):
            if any(x in text.lower() for x in ['name:', 'a.k.a', 'aka', 'born', 'nationality']):
                lines = text.split("\n")
                for line in lines:
                    if "Name:" in line or line.strip().isupper():
                        name = line.split("Name:")[-1].strip()
                        if name and len(name.split()) <= 6:  # avoid long junk
                            names.append(name)
    return list(set(names))

# --- Function to fetch names from MHA banned organisations ---
def get_mha_banned_orgs():
    url = "https://www.mha.gov.in/en/banned-organisations"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")
    names = []
    for li in soup.find_all("li"):
        text = li.get_text().strip()
        if len(text.split()) > 1 and len(text) < 100:
            names.append(text)
    return list(set(names))

# --- Function to fetch names from MHA individual terrorists ---
def get_mha_individual_terrorists():
    url = "https://www.mha.gov.in/en/page/individual-terrorists-under-uapa"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")
    names = []
    for td in soup.find_all("td"):
        text = td.get_text().strip()
        if len(text.split()) >= 2 and all(x.isalpha() or x.isspace() for x in text):
            names.append(text)
    return list(set(names))

# --- Function to fetch names from MHA unlawful associations ---
def get_mha_unlawful_associations():
    url = "https://www.mha.gov.in/en/commoncontent/unlawful-associations-under-section-3-of-unlawful-activities-prevention-act-1967"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")
    names = []
    for li in soup.find_all("li"):
        text = li.get_text().strip()
        if len(text.split()) > 1:
            names.append(text)
    return list(set(names))

# --- Load customer names from Excel ---
def load_customer_names(excel_file):
    df = pd.read_excel(excel_file)
    names = []
    for col in df.columns:
        names.extend(df[col].dropna().astype(str).tolist())
    return list(set(names))

# --- Compare sanctioned vs customer names using fuzzy matching ---
def get_unmatched_sanctioned_names(sanctioned_names, customer_names, threshold=90):
    unmatched = []
    for sname in sanctioned_names:
        matched = False
        for cname in customer_names:
            score = fuzz.token_sort_ratio(sname.lower(), cname.lower())
            if score >= threshold:
                matched = True
                break
        if not matched:
            unmatched.append(sname)
    return unmatched

# === MAIN EXECUTION ===

# 1. Fetch sanctioned names from all 4 websites
un_names = get_un_sanctioned_names()
org_names = get_mha_banned_orgs()
terrorist_names = get_mha_individual_terrorists()
unlawful_assoc_names = get_mha_unlawful_associations()

sanctioned_names = list(set(un_names + org_names + terrorist_names + unlawful_assoc_names))

# 2. Load customer names from your Excel
excel_file = "customers.xlsx"  # Place your file in same folder
customer_names = load_customer_names(excel_file)

# 3. Find sanctioned names not present in customer Excel
missing_sanctioned = get_unmatched_sanctioned_names(sanctioned_names, customer_names)

# 4. Save and show
df_missing = pd.DataFrame(missing_sanctioned, columns=["Sanctioned Name Not in Excel"])
df_missing.to_excel("sanctioned_not_in_excel.xlsx", index=False)
print("✅ Comparison complete. Missing names saved in 'sanctioned_not_in_excel.xlsx'")
