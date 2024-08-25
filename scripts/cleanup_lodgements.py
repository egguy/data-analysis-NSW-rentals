from glob import glob

import polars as pl
from tqdm import tqdm
import pathlib

dfs = []
# process the CSV files
for filename in tqdm(glob("data/output/csv/lodgements/*.csv")):
    # get the filename without the extension
    filename = filename.split("/")[-1].split(".")[0]


    # read the file, treat postcodes as string and parse the dates
    df = pl.read_csv(
        f"data/csv/lodgements/{filename}.csv",
        # parse_dates=["Lodgement Date"],
        try_parse_dates=True,
        schema_overrides={
            "Postcode": str,
            # "Bedrooms": pl.Int8,
            # "Weekly Rent": pl.Int32,
        },
        null_values=["U"],
    )
    dfs.append(df)

print("Processed all the CSV files, concatenating them")

# concatenate the dataframes
df = pl.concat(dfs)

df = df.unique()
print(df.describe())

# print  the raw data
print(df.schema)

print("Saving the data")
print("Converting to CSV")

# creating dir
pathlib.Path("data/output/csv").mkdir(parents=True, exist_ok=True)
pathlib.Path("data/output/parquet").mkdir(parents=True, exist_ok=True)

# save to csv
df.write_csv("data/output/csv/lodgements_combined.csv")
print("Done. Converting to parquet")
df.write_parquet("data/output/parquet/lodgements_combined.parquet")
print("Done 🥳 🎉")
