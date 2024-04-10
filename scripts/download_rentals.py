# The base imports
import os
from functools import partial
from glob import glob
from tqdm import tqdm

# http client
import httpx

# for HTML parsing
import bs4

# for dataframes
import pandas as pd
import multiprocessing

base_url = "https://www.fairtrading.nsw.gov.au/about-fair-trading/rental-bond-data"

xlsx_base_dir = "data/xlsx"
csv_base_dir = "data/csv"

hrefs = {
    "refunds": [],
    "lodgements": [],
    "held": [],
}

tables = {
    "refunds": "panel2",
    "lodgements": "panel1",
    "held": "panel3",
}

# create the directories path
for category in hrefs:
    os.makedirs(os.path.join(xlsx_base_dir, category), exist_ok=True)
    os.makedirs(os.path.join(csv_base_dir, category), exist_ok=True)

print("🕵️ Downloading the webpage")
# Grab the webpage
response = httpx.get(base_url)
# Pass the response to BeautifulSoup
soup = bs4.BeautifulSoup(response.text, "html.parser")

# 2. Parse the HTML table with id #table76559 this table contains all the links to the XLSX files
# this seems to be stable enough
for category, table_id in tables.items():
    table = soup.find(id=table_id)

    # Get all the `a` tags in the first column of the table
    # The first column contains the links to the XLSX files
    # get all the `tr` tags
    # rows = table.find_all("tr")
    for link in table.find_all("a"):
        # # get the first `td` tag from each `tr` tag with xpath
        # first_column = row.find("td")
        # if not first_column:
        #     continue

        # # get the first `a` tag from each `td` tag
        # first_link = first_column.find("a")
        # if not first_link:
        #     continue

        # get the href attribute from each a tag
        href = link.get("href")
        hrefs[category].append(href)

    print(f"Found {len(hrefs[category])} files to download for {category}")


def download_file(category, href):
    # get the filename from the href
    filename = href.split("/")[-1]

    destination = os.path.join(xlsx_base_dir, category, filename)

    # skip the files already downloaded
    if os.path.exists(destination):
        return

    # download the file
    response = httpx.get(href)
    # save the file
    with open(destination, "wb") as f:
        f.write(response.content)


for category, urls in hrefs.items():
    print(f"Downloading {category} files")

    category_downloader = partial(download_file, category)
    with multiprocessing.Pool(4) as http_pool:
        list(tqdm(http_pool.imap(category_downloader, urls), total=len(urls)))


def convert_xlsx_to_csv(category, filename):
    # get the filename without the extension
    base_name = filename.split("/")[-1].split(".")[0]

    destination = os.path.join(csv_base_dir, category, f"{base_name}.csv")

    # skip the files already converted
    if os.path.exists(destination):
        return

    # read the file, remove the first 2 rows they are the header from NSW
    df = pd.read_excel(filename, skiprows=2)
    # save the file
    df.to_csv(destination, index=False)


for category in hrefs:
    # convert the files to CSV
    print(f"🧠 Converting {category} files to CSV")

    file_list = glob(f"data/xlsx/{category}/*.xlsx")

    convert_category = partial(convert_xlsx_to_csv, category)
    # use all the processors for the conversion
    with multiprocessing.Pool() as pool:
        list(tqdm(pool.imap(convert_category, file_list), total=len(file_list)))

for category in hrefs:
    print(f"Checking {category} CSV headers")

    header_ok = True

    # check CSV header are all matching
    ref_columns = None
    for filename in tqdm(glob(f"data/csv/{category}/*.csv")):
        df = pd.read_csv(filename, nrows=1)
        if ref_columns is None:
            ref_columns = df.columns
            continue
        # Check if the columns match
        if not ref_columns.equals(df.columns):
            print(f"Columns are not matching for {filename}")
            print(ref_columns, df.columns)
            header_ok = False

    if not header_ok:
        print("❌ CSV headers are not matching")
    else:
        print("✅ All CSV headers are matching")


print("Merge all the CSV files into one")

dfs = []
# process the CSV files
for filename in tqdm(glob("data/csv/lodgements/*.csv")):
    # get the filename without the extension
    filename = filename.split("/")[-1].split(".")[0]
    # If the filename is not month by month, skip it
    # these files contain the work "-year-"
    # if "-year-" in filename.lower():
    #     continue

    # read the file, treat postcodes as string and parse the dates
    df = pd.read_csv(
        f"data/csv/lodgements/{filename}.csv",
        parse_dates=["Lodgement Date"],
        dtype={
            "Postcode": str,
        },
    )
    dfs.append(df)

print("Processed all the CSV files, concatenating them")

# concatenate the dataframes
df = pd.concat(dfs)
# unique the rows
df = df.drop_duplicates()
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
print("Converting to CSV")
# save to csv
df.to_csv("data/rentals.csv", index=False)
print("Done. Converting to parquet")
df.to_parquet("data/rentals.parquet", index=False)
print("Done 🥳 🎉")
