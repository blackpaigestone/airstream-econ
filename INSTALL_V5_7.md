# V5.7 installation and run

From `~/Downloads/airstream-economics`, with `.venv` active:

```bash
mkdir -p /tmp/airstream-v5-7
unzip -o ~/Downloads/airstream-economics-v5-7-patch.zip -d /tmp/airstream-v5-7
cp /tmp/airstream-v5-7/src/research/historical_ne_v57.py src/research/
cp /tmp/airstream-v5-7/tests/research/test_historical_ne_v57.py tests/research/
cp /tmp/airstream-v5-7/refresh_historical_ne.py /tmp/airstream-v5-7/run_v57.py ./
cp /tmp/airstream-v5-7/RESEARCH_V5_7.md /tmp/airstream-v5-7/INSTALL_V5_7.md ./
python -m compileall -q src tests refresh_historical_ne.py run_v57.py
python -m pytest -q
```

Start with 2023 to catch year-specific Census changes before a large download:

```bash
python refresh_historical_ne.py --years 2023
python run_v57.py --years 2023 2024
```

Then retrieve the remaining years and build the full 2021–2024 descriptive panel:

```bash
python refresh_historical_ne.py --years 2021 2022
python run_v57.py --years 2021 2022 2023 2024
```

Failures are reported per state-year and successful files are preserved; a failed run exits nonzero. Do not commit raw or derived data. Before committing, inspect `git diff --cached --name-only`.
