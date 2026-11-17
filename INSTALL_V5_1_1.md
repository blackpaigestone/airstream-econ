# V5.1.1 — Census API authentication patch

This patch modifies only `src/research/census_acs.py` and adds `tests/research/test_census_auth.py`. It preserves all dashboard tabs and existing data schemas.

## Installation

1. Download `airstream-economics-v5-1-1-patch.zip` to `~/Downloads`.
2. In Terminal:

```bash
cd ~/Downloads/airstream-economics
source .venv/bin/activate
mkdir -p backups
cp src/research/census_acs.py backups/census_acs-before-v5-1-1.py
mkdir -p /tmp/airstream-v5-1-1
unzip -o ~/Downloads/airstream-economics-v5-1-1-patch.zip -d /tmp/airstream-v5-1-1
cp /tmp/airstream-v5-1-1/src/research/census_acs.py src/research/
cp /tmp/airstream-v5-1-1/tests/research/test_census_auth.py tests/research/
cp /tmp/airstream-v5-1-1/INSTALL_V5_1_1.md ./
python -m compileall -q app.py src tests refresh_household_data.py
python -m pytest -q
```

Expected: **49 passed** if V5.1 is installed correctly.

## Census key

Use the existing activated key. In the SAME terminal session where you will run the downloader:

```zsh
read -rs 'CENSUS_API_KEY?Paste your activated Census API key: '
echo
export CENSUS_API_KEY
```

Do not paste your key into the chat or commit it to GitHub. The environment variable is temporary and lasts for that shell session and its child processes.

## Retrieve observations

```bash
python refresh_household_data.py --start 2010 --end 2024
```

The script writes:
- `data/external/census_acs_tenure_age.csv`
- `data/external/census_acs_tenure_age_provenance.json`

The 2020 ACS standard one-year dataset was not released. Expect it to appear as unavailable. Other years may also fail due to Census service or data access issues; inspect the `failures` list. A partial result is not a complete series.

## Validate and launch

```bash
python - <<'PY'
from src.research.census_acs import load_panel
panel = load_panel()
print('Years:', sorted(panel.year.unique().tolist()))
print('Rows:', len(panel))
print('Age bands:', sorted(panel.age_band.unique().tolist()))
PY
python app.py
```

Open http://127.0.0.1:8050 and select Household evidence. The ACS tenure chart should now have observations for successfully retrieved years. The readiness proxy remains unavailable until household microdata is integrated.

## Commit

```bash
git add src/research/census_acs.py tests/research/test_census_auth.py INSTALL_V5_1_1.md
git commit -m 'Authenticate and validate Census ACS data retrieval'
git push origin main
```

**Note:** If committing the generated ACS CSV and provenance files, inspect them first and verify your repository's data versioning policy. Never commit the API key.
