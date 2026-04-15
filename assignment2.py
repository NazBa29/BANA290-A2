# ============================================================
# BANA 290 - Assignment 2: RCT Analysis
# Loan Operations Throughput Tracker
# ============================================================

# PROMPT: Scrape the clerk shift records table from the BANA290 
# assignment dashboard using BeautifulSoup

import requests
from bs4 import BeautifulSoup
import pandas as pd

# ---- PHASE 1: SCRAPE ----
url = "https://bana290-assignment2.netlify.app"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

table = soup.find("table")
df = pd.read_html(str(table))[0]

print("Shape:", df.shape)
print("\nColumns:", df.columns.tolist())
print("\nFirst 3 rows:")
print(df.head(3))