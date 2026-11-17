# V5 — Historical household evidence: data contract and research boundaries

## Research questions
1. Has a standardized real income gain become less effective at creating savings capacity and asset access?
2. Has the cost and economic value of preserving flexibility changed?
3. When does ownership outweigh the option value of mobility?
4. Has the age of independent financial readiness shifted, accounting for household economies of scale?

## Current status
V5 provides an **evidence ingestion and visualization interface**, not a historical estimate. The supplied update contains **no historical household microdata**. Until a harmonized extract is provided, the tab shows an explicit unavailable-data notice. The national FRED indices from V3 remain distinct from age-specific evidence.

## Required file
`data/external/household_harmonized.csv`, one row per household per source and survey year. Columns:

| column | definition |
| --- | --- |
| source_id | stable identifier for the original survey and harmonization version (e.g. `SCF_2022_v1`); do not mix incompatible series under one ID |
| year | actual survey observation year |
| household_id | anonymized within-source household ID |
| age | reference adult's age, integer |
| adults | number of adults in household, integer >=1 |
| dependents | dependent count, integer >=0 |
| earners | earning adults, integer 0 through adults |
| tenure | `renter`, `owner`, or `other` |
| annual_disposable_income | annual after-tax resources, nonnegative |
| annual_essential_spending | annual essential spending, nonnegative; must be consistently defined |
| liquid_assets | liquid resources, nonnegative |
| weight | positive household survey weight, not normalized to 1 |

**All financial amounts must be in a consistent price basis within a record.** For cross-year dollar comparisons, harmonize monetary fields to the same real-dollar reference year before charting and document the deflator and reference year. Readiness ratios within a year are price-level invariant if all financial fields share a basis. The code does not perform deflation automatically. Never treat pre-tax income as disposable income or total spending as essential spending without documenting a changed definition.

## Output measures
- Weighted share with nonnegative cashflow.
- Weighted share satisfying a **scenario readiness proxy**: disposable income positive; annual income minus essentials at least 10% of disposable income; liquid assets at least three months of essential expenses.
- Weighted annual disposable income, essential spending, and savings capacity.
- Weighted mean annual essential spending per adult.
- Observed solo-renter versus shared-adult-renter per-adult essential-spending ratio. **Not causal:** composition, housing quality, local prices, household selection and dependents differ.

Each cell is calculated **within source/year/age bracket**, never pooled across source IDs. Minimum unweighted cell count: 30 (a pragmatic display threshold, not a survey statistical reliability standard). Sample sizes, source IDs, and missing-data status are visible. Survey design variance, replicate weights, nonresponse, topcoding, and confidence intervals are not yet implemented; do not publish population uncertainty claims from these estimates.

## Data acquisition and harmonization plan
1. Identify public, documented microdata and documentation for BLS Consumer Expenditure Survey, Federal Reserve SCF, and Census household/income products.
2. Verify that **income, essential spending, and liquid assets are jointly observed**. If no single survey contains all fields, create separate source-specific analyses. **Never fabricate missing components or join unrelated household records.** CE may support expenses better than assets; SCF may support assets better than essentials.
3. Obtain legal usage terms and documentation for each wave. Record sampling frame, unit of observation, reference-person age, household composition, weights, survey years, variable definitions, missing-value codes, and dollar basis.
4. Create reproducible ETL per survey in `src/research/`, preserving raw data provenance and validation logs. Do not commit confidential or restricted microdata.
5. Harmonize age groups 25–34, 35–44, 45–54; track household type and earners separately.
6. Apply survey weights and design-appropriate variance estimation; examine alternative definitions of essential expenses and reserves.
7. Only then estimate historical trends and, if age-specific observations support it, a readiness-age gap. A single 25–34 age bin cannot identify a precise age at readiness.

## Reproducibility
`python -m pytest -q` runs synthetic unit tests (test data never enter the dashboard). The app reads only the real file at the declared location. Source-specific ETL and provenance records are future deliverables.
