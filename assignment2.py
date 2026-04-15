# BANA 290 - Assignment 2: RCT Analysis
# PROMPT: Scrape and clean clerk shift records from BANA290 dashboard

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# ---- PHASE 1: SCRAPE ----
url = "https://bana290-assignment2.netlify.app"
soup = BeautifulSoup(requests.get(url).text, "html.parser")
rows = soup.select("tr")

data = []
for row in rows:
    cells = row.find_all("td")
    if len(cells) >= 14:
        data.append([c.get_text(strip=True) for c in cells])

cols = ["CLERK","CLERK_ID","QUEUE","SITE","SHIFT","YEARS_EXPERIENCE",
        "BASELINE_TASKS_PER_HOUR","BASELINE_ERROR_RATE","TRAINING_SCORE",
        "TREATMENT","SHIFT_START","SHIFT_END","TASKS_COMPLETED","ERROR_RATE"]
df = pd.DataFrame(data, columns=cols)
print("Shape:", df.shape)
print("Sample TREATMENT:", df["TREATMENT"].unique()[:6])

# ---- PHASE 2: CLEAN ----
# PROMPT: Map treatment labels to binary, extract numbers, fix timestamps

def map_treatment(val):
    val = str(val).lower()
    for t in ["ai extract","assist-on","treatment","prefill enabled","group a"]:
        if t in val: return 1
    for c in ["control","none","manual entry","typing only","group b"]:
        if c in val: return 0
    return None

def extract_num(val):
    m = re.search(r"[\d.]+", str(val))
    return float(m.group()) if m else None

df["TREATMENT_BINARY"]     = df["TREATMENT"].apply(map_treatment)
df["TASKS_CLEAN"]          = df["TASKS_COMPLETED"].apply(extract_num)
df["ERROR_RATE_CLEAN"]     = df["ERROR_RATE"].apply(extract_num)
df["YEARS_EXP_CLEAN"]      = df["YEARS_EXPERIENCE"].apply(extract_num)
df["BASELINE_TASKS_CLEAN"] = df["BASELINE_TASKS_PER_HOUR"].apply(extract_num)
df["TRAINING_CLEAN"]       = df["TRAINING_SCORE"].apply(extract_num)
df["SHIFT_START_CLEAN"]    = pd.to_datetime(df["SHIFT_START"], errors="coerce")
df["SHIFT_END_CLEAN"]      = pd.to_datetime(df["SHIFT_END"], errors="coerce")
df["SHIFT_DURATION"]       = (df["SHIFT_END_CLEAN"]-df["SHIFT_START_CLEAN"]).dt.total_seconds()/3600

df_clean = df.dropna(subset=["TREATMENT_BINARY","TASKS_CLEAN","ERROR_RATE_CLEAN"]).copy()
print("\nClean shape:", df_clean.shape)
print("\nTreatment counts:\n", df_clean["TREATMENT_BINARY"].value_counts())
print("\nSample:\n", df_clean[["TREATMENT_BINARY","TASKS_CLEAN","ERROR_RATE_CLEAN"]].head())