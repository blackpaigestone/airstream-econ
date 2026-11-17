# V5.8 install and run (macOS)

From `~/Downloads/airstream-economics` with `.venv` active:

```bash
mkdir -p /tmp/airstream-v5-8
unzip -o ~/Downloads/airstream-economics-v5-8-patch.zip -d /tmp/airstream-v5-8
cp /tmp/airstream-v5-8/src/research/long_run_v58.py src/research/
cp /tmp/airstream-v5-8/tests/research/test_long_run_v58.py tests/research/
cp /tmp/airstream-v5-8/build_long_run_v58.py ./
cp /tmp/airstream-v5-8/RESEARCH_V5_8.md /tmp/airstream-v5-8/INSTALL_V5_8.md ./
mkdir -p data/templates
cp /tmp/airstream-v5-8/data/templates/decennial_aggregates_template.csv data/templates/
python -m pytest -q
python build_long_run_v58.py
```

Outputs: `data/derived/v58/long_run_panel.csv`, `source_coverage_1990_2024.csv`, `long_run_audit.json`. This first run uses real V5.7 2021–2024 observations and documents the earlier missing years. It does not download 1990/2000 PUMS automatically.

To add **externally harmonized and documented** decennial weighted aggregates (not raw IPUMS CSV), populate a separate CSV using `data/templates/decennial_aggregates_template.csv` as the header and run:

```bash
python build_long_run_v58.py --decennial-aggregates path/to/validated_decennial_aggregates.csv
```

Do not put invented values in the template. The current adapter is a safe import contract, not a decennial microdata processor.

After reviewing outputs:

```bash
git add src/research/long_run_v58.py tests/research/test_long_run_v58.py build_long_run_v58.py RESEARCH_V5_8.md INSTALL_V5_8.md data/templates/decennial_aggregates_template.csv
git diff --cached --stat
git commit -m "Add V5.8 source-aware 1990-2024 long-run research spine"
git push origin main
```
