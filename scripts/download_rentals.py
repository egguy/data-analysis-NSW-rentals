# The base imports
import os
from glob import glob
from tqdm import tqdm

# http client
import httpx
# for HTML parsing
import bs4
# for dataframes
import pandas as pd

base_url = "https://www.fairtrading.nsw.gov.au/about-fair-trading/rental-bond-data"

print("🕵️ Downloading the webpage")
# Grab the webpage
response = httpx.get(base_url)
# Pass the response to BeautifulSoup
soup = bs4.BeautifulSoup(response.text, "html.parser")

# 2. Parse the HTML table with id #table76559 this table contains all the links to the XLSX files
# this seems to be stable enough
table = soup.find(id="table76559")

# Get all the `a` tags in the first column of the table
# The first column contains the links to the XLSX files
# get all the `tr` tags
hrefs = []
rows = table.find_all("tr")
for row in rows:
    # get the first `td` tag from each `tr` tag with xpath
    first_column = row.find("td")
    if not first_column:
        continue

    # get the first `a` tag from each `td` tag
    first_link = first_column.find("a")
    if not first_link:
        continue

    # get the href attribute from each a tag
    href = first_link.get("href")
    hrefs.append(href)

print(f"Found {len(hrefs)} files to download")

# create the directories
os.makedirs("data/xlsx", exist_ok=True)
os.makedirs("data/csv", exist_ok=True)

# download the files
print("Downloading the raw files files")
for href in tqdm(hrefs):
    # get the filename from the href
    filename = href.split("/")[-1]

    # skip the files already downloaded
    if os.path.exists(f"data/xlsx/{filename}"):
        continue

    # download the file
    response = httpx.get(href)
    # save the file
    with open(f"data/xlsx/{filename}", "wb") as f:
        f.write(response.content)


# convert the files to CSV
print("🧠 Converting the files to CSV")
for filename in tqdm(glob("data/xlsx/*.xlsx")):
    # get the filename without the extension
    filename = filename.split("/")[-1].split(".")[0]
    # skip the files already converted
    if os.path.exists(f"data/csv/{filename}.csv"):
        continue

    # read the file, remove the first 2 rows they are the header from NSW
    df = pd.read_excel(f"data/xlsx/{filename}.xlsx", skiprows=2)
    # save the file
    df.to_csv(f"data/csv/{filename}.csv", index=False)

# check CSV header are all matching
ref_columns = None
print("Checking the CSV headers")
for filename in tqdm(glob("data/csv/*.csv")):
    df = pd.read_csv(filename)
    if ref_columns is None:
        ref_columns = df.columns
        continue
    # Check if the columns match
    if not ref_columns.equals(df.columns):
        print(f"Columns are not matching for {filename}")
        print(ref_columns)

print("✅ All CSV headers are matching")

print("Merge all the CSV files into one")

dfs = []
# process the CSV files
for filename in tqdm(glob("data/csv/*.csv")):
    # get the filename without the extension
    filename = filename.split("/")[-1].split(".")[0]
    # If the filename is not month by month, skip it
    # these files contain the work "-year-"
    if "-year-" in filename.lower():
        continue

    # read the file, treat postcodes as string and parse the dates
    df = pd.read_csv(f"data/csv/{filename}.csv", parse_dates=["Lodgement Date"], dtype={"Postcode": str, })
    dfs.append(df)
print("Processed all the CSV files, concatenating them")

# concatenate the dataframes
df = pd.concat(dfs)
# convert rent to numeric, dropping the rows that are not numeric
df["Weekly Rent"] = pd.to_numeric(df["Weekly Rent"], errors="coerce")
df["Bedrooms"] = pd.to_numeric(df["Bedrooms"], errors="coerce")
df = df.dropna(subset=["Weekly Rent", "Bedrooms"])
# convert the columns to int
df["Weekly Rent"] = df["Weekly Rent"].astype(int)
df["Bedrooms"] = df["Bedrooms"].astype(int)

# Save the raw data
print(df.info())

print("Saving the data")
# save to csv
df.to_csv("data/rentals.csv", index=False)
df.to_parquet("data/rentals.parquet", index=False)
print("Done 🥳 🎉")