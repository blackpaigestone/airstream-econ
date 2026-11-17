# V5.6 installation

Run in `~/Downloads/airstream-economics` with `.venv` activated. Download the ZIP into `~/Downloads`.

```bash
mkdir -p /tmp/airstream-v5-6
unzip -o ~/Downloads/airstream-economics-v5-6-patch.zip -d /tmp/airstream-v5-6
cp /tmp/airstream-v5-6/src/research/new_england_v56.py src/research/
cp /tmp/airstream-v5-6/tests/research/test_new_england_v56.py tests/research/
cp /tmp/airstream-v5-6/run_v56.py ./
cp /tmp/airstream-v5-6/RESEARCH_V5_6.md ./
python -m compileall -q src tests run_v56.py
python -m pytest -q
python run_v56.py --year 2024
```

Expected outputs (untracked derived data):

- `data/derived/v56/2024/extraction_audit.csv`
- `data/derived/v56/2024/denominator_audit.csv`
- `data/derived/v56/2024/descriptive_strata.csv`

Do not commit raw, prepared, or derived PUMS CSVs. Ensure `.gitignore` excludes `data/raw/`, `data/external/pums_prepared/`, and `data/derived/`. No existing research or dashboard code is overwritten.
