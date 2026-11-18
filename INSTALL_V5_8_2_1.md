# V5.8.2.1 — ACS 2015–2016 ZIP member compatibility

This patch replaces only the V5.8.2 module and its test file. It does not overwrite the runner, V5.8.1 importer, or any raw/prepared data.

From the project root:

```bash
unzip -o ~/Downloads/airstream-economics-v5-8-2-1-patch.zip -d .
PYTHONPATH="$PWD/src" python -m pytest -q
PYTHONPATH="$PWD/src" python run_historical_v582.py --years 2015 2016
python build_historical_bridge_v581.py --years 2015 2016 2017 2018 2019
```

2015–2016 use `ssYYhST.csv` / `ssYYpST.csv`; 2017–2018 use `psam_hFIPS.csv` / `psam_pFIPS.csv`. The 2015–2016 person archive member convention is tested synthetically but has not been verified against the user's local Census ZIP files. If an archive fails, inspect `unzip -Z1 data/raw/pums/2015/csv_pct.zip` and share output before proceeding. Ingestion success does not certify external completeness or survey-design uncertainty.
