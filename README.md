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

Then click on the file rental_analysis.ipynb

## Data references

- [NSW suburb boundaries](https://portal.spatial.nsw.gov.au/static/exportcontent.html?featureservername=NSW_Administrative_Boundaries_Theme&title=NSW%20Administrative%20Boundaries%20Theme&wgs84Eqv=GDA2020&url=https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Administrative_Boundaries_Theme/FeatureServer)
- [NSW rental bond data](https://www.fairtrading.nsw.gov.au/about-fair-trading/rental-bond-data)
- [Statistical boundaries](https://www.abs.gov.au/websitedbs/censushome.nsf/home/factsheetsgeography/$file/Greater%20Capital%20City%20Statistical%20Area%20-%20Fact%20Sheet.pdf)