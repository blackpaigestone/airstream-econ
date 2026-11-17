# V5.5.3 — New England PUMS ingestion

Install this patch over V5.5.2. The updated 2021–2024 ingestion uses `RELSHIPP=20` for the reference person, not the obsolete `RELP=0`. Includes all six New England state FIPS codes and separately stored prepared samples. No historical multi-year results or dashboard changes are claimed.

## Install

```bash
cd ~/Downloads/airstream-economics
source .venv/bin/activate
mkdir -p backups /tmp/airstream-v5-5-3
cp src/research/acs_pums_api.py backups/acs_pums_api-before-v553.py
cp src/research/acs_pums_ingest.py backups/acs_pums_ingest-before-v553.py
unzip -o ~/Downloads/airstream-economics-v5-5-3-patch.zip -d /tmp/airstream-v5-5-3
cp /tmp/airstream-v5-5-3/src/research/*.py src/research/
cp /tmp/airstream-v5-5-3/tests/research/*.py tests/research/
cp /tmp/airstream-v5-5-3/refresh_new_england_pums.py ./
cp /tmp/airstream-v5-5-3/compare_new_england.py ./
cp /tmp/airstream-v5-5-3/INSTALL_V5_5_3.md ./
cp /tmp/airstream-v5-5-3/RESEARCH_V5_5_3.md ./
python -m compileall -q src tests refresh_new_england_pums.py compare_new_england.py
python -m pytest -q
```

## Retrieve and compare

Ensure `CENSUS_API_KEY` is exported. Start with one state to verify the end-to-end fix:

```bash
python refresh_new_england_pums.py --year 2024 --states 23
```

Then request the other five states:

```bash
python refresh_new_england_pums.py --year 2024 --states 09 25 33 44 50
```

The fail-closed API guard may reject large states (especially Massachusetts) if the response is too large; do not raise the safety threshold just to make it pass. Official bulk PUMS is the fallback. Only after all six state extracts exist:

```bash
python compare_new_england.py --year 2024 --threshold 0.30
python compare_new_england.py --year 2024 --threshold 0.50
```

**Never commit `data/raw/pums/` or `data/external/pums_prepared/` until exclusion and release policy are reviewed.** Check `.gitignore` first.

## Commit code after tests and retrieval checks

```bash
git add src/research/acs_pums_api.py src/research/acs_pums_ingest.py tests/research/test_acs_pums_api.py tests/research/test_acs_pums_api_v552.py tests/research/test_acs_pums_ingest.py tests/research/test_new_england.py refresh_new_england_pums.py compare_new_england.py INSTALL_V5_5_3.md RESEARCH_V5_5_3.md
git commit -m "Harmonize 2024 PUMS relationships and add New England comparison pipeline"
git push origin main
```
