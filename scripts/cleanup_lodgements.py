from glob import glob

import pandas as pd
from tqdm import tqdm
import pathlib

dfs = []
# process the CSV files
for filename in tqdm(glob("data/output/csv/lodgements/*.csv")):
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

# creating dir
pathlib.Path("data/output/csv").mkdir(parents=True, exist_ok=True)
pathlib.Path("data/output/parquet").mkdir(parents=True, exist_ok=True)

# save to csv
df.to_csv("data/output/csv/lodgements_combined.csv", index=False)
print("Done. Converting to parquet")
df.to_parquet("data/output/parquet/lodgements_combined.parquet", index=False)
print("Done 🥳 🎉")
