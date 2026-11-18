# V5.8.1 installation and operation

Install files from patch ZIP preserving directories, run `python -m pytest -q`.

## Source files

Obtain **official ACS 1-year PUMS housing and person CSV files** for one state and year (2015–2019) from https://www.census.gov/programs-surveys/acs/microdata/access.html . The importer expects unmodified records with `SERIALNO, ST, NP, TEN, HINCP, GRNTP, WGTP` in housing and `SERIALNO, SPORDER, AGEP, WAGP, SEMP`, plus `RELP` or `RELSHIPP` in person data. If official downloads are split into files, concatenate *same state/year and record type* with one header and verify counts and identifiers first. Do not concatenate across states or years. Use one state/year at a time. Official files may be large.

Example for **Maine 2019** (replace with your actual extracted CSV paths):

```bash
python import_historical_bulk.py --year 2019 --state 23 \
  --households data/raw/pums/2019/maine_housing.csv \
  --persons data/raw/pums/2019/maine_persons.csv
```

For older records containing `RELP`, the reference person is code 0; for records containing `RELSHIPP`, the reference person is code 20. When both fields are present, specify `--relationship RELP` or `--relationship RELSHIPP` after confirming the Census data dictionary for that year. Never substitute `SPORDER=1`.

The importer creates `data/external/pums_prepared/YEAR/state_XX.csv` and a corresponding `.audit.json`. It refuses to overwrite either file. **The presence of these files does not certify official bulk completeness.**

Once **all six states for the same year** have been imported, run:

```bash
python build_historical_bridge_v581.py --years 2019
```

This reads `data/derived/v58/long_run_panel.csv`, adds the historical estimates, and writes `data/derived/v581/long_run_panel.csv`. It refuses to overwrite an existing output. To include more years, import six states per year, then run the bridge with all years together into a new output path, e.g. `--years 2018 2019 --out data/derived/v581/long_run_panel_2018_2019.csv`.

**Limitations:** 2015–2019 only. Historical monetary fields are used as *within-year ratios* without inflation adjustment; real-dollar comparisons are not implemented. Replicate-weight uncertainty, independent source count certification, 2005–2014 harmonization, and 1990/2000 IPUMS ingestion remain outstanding. 2020 standard ACS1 is unavailable. Historical trends are provisional.
