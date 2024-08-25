import os
from functools import partial
from glob import glob

import polars as pl
from tqdm import tqdm

xlsx_base_dir = "data/input/xlsx"
csv_base_dir = "data/output/csv"

categories = [
    "refunds",
    "lodgements",
    "held",
]


def convert_xlsx_to_csv(category, filename):
    # get the filename without the extension
    base_name = filename.split("/")[-1].split(".")[0]

    destination = os.path.join(csv_base_dir, category, f"{base_name}.csv")

    # skip the files already converted
    if os.path.exists(destination):
        print(f"Skipping {filename} already converted")
        return

    # read the file, remove the first 2 rows they are the header from NSW
    df = pl.read_excel(
        filename,
        engine="calamine",
        read_options={"header_row": 2},
    )
    print(df.head())
    # save the file
    df.write_csv(destination)


for category in categories:
    # convert the files to CSV
    print(f"🧠 Converting {category} files to CSV")

    file_list = glob(f"{xlsx_base_dir}/{category}/*.xlsx")

    # create destination folder
    os.makedirs(f"{csv_base_dir}/{category}", exist_ok=True)

    convert_category = partial(convert_xlsx_to_csv, category)
    for file in tqdm(file_list):
        convert_xlsx_to_csv(category, file)
