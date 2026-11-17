# V5.1 — First observed age-specific household series

## What this release does
Adds a reproducible **US Census American Community Survey (ACS) 1-year** data acquisition pipeline and a separate observed-data chart in the existing **Household evidence** tab. The chart uses ACS detailed table **B25007, Tenure by Age of Householder**, for ages 25–34, 35–44 and 45–54. It displays the share or estimated number of owner- and renter-occupied households by age of the householder.

Source: https://api.census.gov/data.html ; table metadata per year: `https://api.census.gov/data/YYYY/acs/acs1/groups/B25007.json`.

## Running
From the project root with its virtual environment active:

```bash
python refresh_household_data.py --start 2010 --end 2024
python -m pytest -q
python app.py
```

The command contacts the **public US Census API** (internet access required). It writes `data/external/census_acs_tenure_age.csv` and `data/external/census_acs_tenure_age_provenance.json` with successful years and recorded failures. **2020 ACS 1-year standard data were not released**, so a missing 2020 observation is expected. Other missing years must be investigated; do not interpolate or silently treat missingness as zero. This code derives variable IDs from official year-specific metadata labels, rather than assuming their positions. If the Census API changes its labels or structure, the downloader will fail visibly instead of guessing.

The downloader was unit-tested with mocked responses. **Live Census API access was unavailable in the build environment, so the data download and live integration must be verified on your Mac.** No actual Census data are included in the update ZIP. Do not present the test fixtures as empirical observations.

## Interpretation
The ACS tenure series is **not** a measure of financial readiness, independent living, household expense, wealth, or affordability. Age is that of the **householder**, not every adult resident. A renter-share trend cannot establish that ownership is becoming easier or harder: it may reflect household formation, preferences, financing, geographic composition, and other factors. Counts are ACS population estimates with sampling uncertainty; this release does not fetch margins of error. Do not use these charts for statistical significance claims.

The original V5 survey-weighted readiness chart remains empty until a properly harmonized household extract with jointly observed income, essential spending and liquid assets is obtained. Never combine unrelated survey respondents to manufacture those fields.

## Next data layers
1. Census published historical income by age of householder (H-10) with verified price basis and coverage; compare 25–34 with older age brackets, and document any changed income definition.
2. BLS Consumer Expenditure Survey public-use microdata for spending and household composition; document coverage and survey weighting.
3. Federal Reserve Survey of Consumer Finances for liquid assets, debt and financial resilience; keep its triennial waves distinct.
4. Compare fixed chronological ages and financial-readiness ages only when variables are jointly observed and comparably defined. Household size, number of earners, and dependent children must remain separate analytical dimensions.

## Source and version control
The generated CSV and provenance JSON are small, public-derived research outputs. Inspect the provenance file and spot-check official published table values before citing results. Never commit restricted microdata or personal household identifiers.
