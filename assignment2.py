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

# ---- PHASE 3: ANALYZE ----
# PROMPT: Balance test, ignorability t-tests, SUTVA justification, ATE estimation

from scipy import stats
import matplotlib.pyplot as plt
treated = df_clean[df_clean["TREATMENT_BINARY"]==1]
control = df_clean[df_clean["TREATMENT_BINARY"]==0]

# --- A: Balance Test ---
print("="*50)
print("BALANCE TEST")
print("="*50)
for col in ["YEARS_EXP_CLEAN","BASELINE_TASKS_CLEAN","TRAINING_CLEAN"]:
    t, p = stats.ttest_ind(treated[col].dropna(), control[col].dropna())
    print(f"{col}: treated={treated[col].mean():.2f}, control={control[col].mean():.2f}, p={p:.3f}")

# --- B: ATE Estimation ---
print("\n" + "="*50)
print("ATE ESTIMATION")
print("="*50)
ate_tasks = treated["TASKS_CLEAN"].mean() - control["TASKS_CLEAN"].mean()
ate_error = treated["ERROR_RATE_CLEAN"].mean() - control["ERROR_RATE_CLEAN"].mean()
print(f"ATE (Productivity): {ate_tasks:.2f} tasks")
print(f"ATE (Error Rate):   {ate_error:.3f} pct")

t1, p1 = stats.ttest_ind(treated["TASKS_CLEAN"], control["TASKS_CLEAN"])
t2, p2 = stats.ttest_ind(treated["ERROR_RATE_CLEAN"], control["ERROR_RATE_CLEAN"])
print(f"Productivity p-value: {p1:.4f}")
print(f"Error Rate p-value:   {p2:.4f}")

# --- Boxplots ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
df_clean.boxplot(column="TASKS_CLEAN", by="TREATMENT_BINARY", ax=ax1)
ax1.set_title("Productivity by Treatment")
df_clean.boxplot(column="ERROR_RATE_CLEAN", by="TREATMENT_BINARY", ax=ax2)
ax2.set_title("Error Rate by Treatment")
plt.savefig("boxplots.png")
print("\nBoxplots saved!")