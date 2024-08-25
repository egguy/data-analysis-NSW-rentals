from glob import glob

import polars as pl
from tqdm import tqdm
import pathlib

dfs = []
# process the CSV files
for filename in tqdm(glob("data/output/csv/refunds/*.csv")):

    # read the file, treat postcodes as string and parse the dates
    df = pl.read_csv(
        filename,
        schema_overrides={
            "Payment Date": pl.Date,
            "Postcode": str,
        },
        null_values=["U"],
    )
    dfs.append(df)

print("Processed all the CSV files, concatenating them")

# concatenate the dataframes
df = pl.concat(dfs)
# unique the rows
df = df.unique()

numeric_columns = [
    "Payment To Tenant",
    "Payment To Agent",
    "Bedrooms",
    "Days Bond Held",
]

# for col in numeric_columns:
#     df[col] = pd.to_numeric(df[col], errors="coerce")
#
# df = df.dropna(subset=numeric_columns)
# # convert the columns to int
# for col in numeric_columns:
#     df[col] = df[col].astype(int)

# Save the raw data
print(df.describe())
print(df.schema)
print("Saving the data")
print("Converting to CSV")

# creating dir
pathlib.Path("data/output/csv").mkdir(parents=True, exist_ok=True)
pathlib.Path("data/output/parquet").mkdir(parents=True, exist_ok=True)

# save to csv
df.write_csv("data/output/csv/refunds_combined.csv")
print("Done. Converting to parquet")
df.write_parquet("data/output/parquet/refunds_combined.parquet")
print("Done 🥳 🎉")
