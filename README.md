# data analysis of NSW rentals
A quick analysis of the rental market in NSW

This shows how to:

- Scrape data with httpx+beautifulsoup
- Check the data
- Prepare the data for analysis with pandas
- Do some basic analysis with pandas
  - How is distributed the number of bedrooms (e.g. more towards 1 or 2 bedrooms ?)
  - The bedrooms' rentals per year
  - How the price is evolving over time
  - How the price is evolving over time for each number of bedrooms
  - The percent of change per year and month

You can explore the dataset at this url: [NSW rentals datasette](https://nsw-rentals.moospirit.org/)

## Setup

### Virtual environment (Optional)
```bash
python3 -m venv venv
source venv/bin/activate

```

### Install dependencies
```bash
pip install -r requirements.txt
```

## Content

- [rent_analysis.ipynb](rent_analysis.ipynb) - Jupyter notebook with the analysis

# how tu run ?

```bash
jupyter notebook
```

Then client on the file rental_analysis.ipynb