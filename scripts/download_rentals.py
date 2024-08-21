# The base imports
import os
from functools import partial
from glob import glob
from tqdm import tqdm

# http client
import httpx

# for HTML parsing
import bs4
from urllib.parse import urljoin

# for dataframes
import pandas as pd
import multiprocessing

base_url = "https://www.nsw.gov.au/housing-and-construction/rental-forms-surveys-and-data/rental-bond-data"

xlsx_base_dir = "data/input/xlsx"
csv_base_dir = "data/output/csv"

hrefs = {
    "refunds": [],
    "lodgements": [],
    "held": [],
}

def is_refund_xlsx(href) -> bool:
    # url looks like /sites/default/files/noindex/2023-11/RentalBond_Refunds_2nd_Quarter_2023.xlsx
    lower_href = href.lower()
    if not lower_href.endswith(".xlsx"):
        return False

    if "refund" not in lower_href:
        return False
    if "rental" not in lower_href:
        return False
    if "bond" not in lower_href:
        return False
    return True

def is_lodgement_xlsx(href) -> bool:
    # url looks like /sites/default/files/noindex/2024-06/rental-bond_lodgements_may_2024.xlsx
    lower_href = href.lower()
    if not lower_href.endswith(".xlsx"):
        return False

    if "lodgement" not in lower_href:
        return False
    if "rental" not in lower_href:
        return False
    if "bond" not in lower_href:
        return False
    return True

def is_rental_bond_holding_xlsx(href) -> bool:
    # url is like: /sites/default/files/noindex/2024-05/RentalBond_Bondsheld_As_At_Jan_2024.xlsx
    lower_href = href.lower()
    if not lower_href.endswith(".xlsx"):
        return False

    if "held" not in lower_href:
        return False
    if "rental" not in lower_href:
        return False
    if "bond" not in lower_href:
        return False
    return True

checker = {
    "refunds": is_refund_xlsx,
    "lodgements": is_lodgement_xlsx,
    "held": is_rental_bond_holding_xlsx,
}

# create the directories' path
for category in hrefs:
    os.makedirs(os.path.join(xlsx_base_dir, category), exist_ok=True)
    os.makedirs(os.path.join(csv_base_dir, category), exist_ok=True)

print("🕵️ Downloading the webpage")
# Grab the webpage
response = httpx.get(base_url)
# Pass the response to BeautifulSoup
soup = bs4.BeautifulSoup(response.text, "html.parser")

# get all the a link
links = [link.get("href") for link in soup.find_all("a")]
# make then absolute
links = [urljoin(base_url, link) for link in links if link]

print(f"Found {len(links)} links")

# categorize the links
for category, check_func in checker.items():
    hrefs[category] = [link for link in links if check_func(link)]

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
