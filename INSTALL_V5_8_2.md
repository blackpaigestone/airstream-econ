# V5.8.2 installation

This is an **overlay patch** for the existing V5.8.1 checkout, not a standalone repository.

```bash
cd ~/Downloads/airstream-economics
source .venv/bin/activate
unzip -o ~/Downloads/airstream-economics-v5-8-2-patch.zip -d .
python -m pytest -q
```

Start with one year to validate Census file availability and historical schema:

```bash
python run_historical_v582.py --years 2018
```

If 2018 passes, proceed with the remaining years:

```bash
python run_historical_v582.py --years 2015 2016 2017
```

Or download without preparing:

```bash
python run_historical_v582.py --years 2015 2016 2017 2018 --download-only
```

Run using archives already downloaded (no network):

```bash
python run_historical_v582.py --years 2018 --offline
```

Outputs:
- `data/raw/pums/<year>/csv_[hp]<state>.zip` (source archives)
- `data/raw/pums/<year>/psam_[hp]<FIPS>.csv` (extracted)
- `data/external/pums_prepared/<year>/state_<FIPS>.csv` and `.audit.json`
- `data/derived/v582/v582_run.json` (latest run summary; run-level audit overwritten on each invocation)

The script skips existing prepared outputs and never overwrites them. On failures it records errors and returns exit code 1 after attempting remaining states. Inspect the audit before proceeding. Downloaded archives are not silently replaced if corrupted. Run-level audit is **latest run only**, not a longitudinal event store.

Once all six states are successfully prepared for each requested year, build the bridge:

```bash
python build_historical_bridge_v581.py --years 2015 2016 2017 2018 2019
```

Confirm CLI support for multiple years with `python build_historical_bridge_v581.py --help` before running. The bridge's own validations and coverage reporting remain authoritative.

Commit source files only:

```bash
git add src/research/historical_pipeline_v582.py run_historical_v582.py tests/research/test_historical_pipeline_v582.py INSTALL_V5_8_2.md RESEARCH_V5_8_2.md
git diff --cached --stat
git commit -m "Add V5.8.2 historical PUMS ingestion runner and integrity audits"
git push origin main
```
