# V5.7 — Historical New England ACS PUMS (2021–2024)

## Scope

This is a **first historical descriptive release**, not a final inferential release. It runs the V5.6 definitions on 2021, 2022, 2023 and 2024 ACS 1-year PUMS state samples for CT, ME, MA, NH, RI and VT. The 2020 standard ACS 1-year series is unavailable. The scripts refuse to extend to earlier years without variable/coding harmonization.

## Reproducibility and provenance

`refresh_historical_ne.py` retrieves the missing 2021–2023 state-years using the existing API retrieval, `RELSHIPP` reference-person mapping, group-quarters exclusion, and household-person count validation. Each state-year is saved separately with provenance and audit files. Existing files are never overwritten. `run_v57.py` requires all six states in every requested year and reads the same V5.6 validated prepared structure. It emits historical_strata.csv, historical_extraction_audit.csv, young_adults_living_alone.csv and endpoint_changes.csv.

## Interpretive limits

- No bulk PUMS cross-check yet: API response completeness is not externally certified.
- No replicate weights in the current extraction: no survey-design standard errors, confidence intervals, or statistical significance claims. The `sample_n` field is the number of eligible unweighted sample records, not the population count.
- PUMS annual samples are repeated cross-sections, **not** a longitudinal household panel.
- Housing burden is a within-year ratio of nominal annual household income to nominal gross rent; the ratio does not require CPI adjustment, but any future comparison of dollar levels must adjust for inflation and PUMS adjustment factors (`ADJINC`/`ADJHSG`) appropriately.
- The 25–34, one-person renter subgroup conditions on successfully formed households; it cannot directly measure those unable to live independently.
- Current renter income denominator exclusions and missing values follow V5.6; inspect the annual audits for denominator drift.
- `safe_max_rows=150000` is a **size safeguard**, not independent completeness verification. If an API request fails or exceeds the cap, use official Census bulk files after integrating a compatible bulk workflow; do not increase limits indefinitely or silently drop states.
- Endpoint percentage-point changes are **descriptive**. Do not claim causation or statistically significant change.

## Next for V6

1. Reconcile each state-year against official Census bulk PUMS counts and source documentation.
2. Incorporate household replicate weights (`WGTP1`–`WGTP80`) and the ACS PUMS variance method; calculate uncertainty for state, pooled, and differences.
3. Harmonize and extend historical series before 2021 (2010–2019 where data support it), retaining the 2020 gap.
4. Examine household formation and living-with-parents indicators using the person universe, not only observed renter households.
5. Integrate validated historical findings into the dashboard with explicit coverage and uncertainty labels.
