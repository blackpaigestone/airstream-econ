# V5.8 — 1990–2024 long-run research architecture

**Primary research question:** Has the cost of maintaining economic freedom increased faster than the purchasing power of income—and has that change delayed the age at which people can meaningfully exercise economic independence?

## Scope of this release

This is a **source-aware research spine**, not a finished 1990–2024 historical estimate. It builds a long-format panel from actual V5.7 2021–2024 renter burden estimates, records availability and gaps for 1990–2024, and provides a strict adapter for externally harmonized 1990/2000 weighted decennial estimates. **No missing years are interpolated or filled.** No decennial data are included until the researcher supplies a validated extract.

## Source eras and harmonization tasks

- **1990 and 2000:** decennial Census PUMS (e.g., IPUMS USA extract, with citation and extract provenance). Secure source microdata and harmonize tenure, householder age, gross rent, income, relationships, households, sample universe, and household weights. Do not assume an ACS definition is directly applicable.
- **2005–2019:** ACS 1-year PUMS, pending validated relationship codes, monetary adjustments, inflation base, housing variables, and consistent survey universe. The V5.5 ingestion currently rejects pre-2021 relationship mapping; this is intentional.
- **2020:** no standard ACS 1-year PUMS release; preserve the gap.
- **2021–2024:** existing V5.7 annual six-state extracts and descriptive weighted estimates; external bulk-file sample completeness and replicate-weight uncertainty remain unverified.
- **1991–1999 and 2001–2004:** no directly comparable annual ACS 1-year microdata series in this pipeline. Do not interpolate a continuous line through the decennial benchmarks.

## Required long-run indicators (future phases)

1. Housing: burden ≥30% and ≥50%, real gross rent, price of one-person independent housing.
2. Income: real individual earned income, household income, income distributions, and earned-income purchasing power.
3. Household formation: living with parents, living with partner, sharing housing with non-partners, independent one-person household formation.
4. Economic freedom: transparent income and cost thresholds for sustaining an independent household, with sensitivity analyses.
5. Regional benchmarks: Maine, five-state pooled comparator, New England pooled and equal-state mean/median; do not conflate them.

**Estimands differ:** current V5.7 burden applies only to existing eligible renter households; independence formation requires all relevant adults as denominator, not just existing renters. A young person living with parents is not counted as an independent renter, but cannot be assumed economically constrained without additional evidence.

## Minimum source evidence to add decennial aggregates

The `decennial_aggregates_template.csv` is a *schema*, not data. Each nonempty row must have year, geography, age/household/earner group, independently computed weighted numerator and denominator, unweighted sample n, nonblank source ID, harmonization document reference, and weighting basis. The adapter rejects invalid counts and labels every imported decennial estimate **not yet cross-survey harmonized**. A proper 1990–2024 trend requires additional validation beyond this import.

## V6 gate

Do not present a continuous 1990–2024 trend or claim delay in age of independence until historical microdata harmonization, survey design variance, inflation normalization, source completeness, and denominator selection are resolved. All current output remains descriptive and provisional.
