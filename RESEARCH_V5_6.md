# V5.6 — New England household composition (descriptive pilot)

This release advances the empirical research from six-state aggregate rent burden to **2024 subgroup comparisons** by householder age (25–34, 35–44, 45–54), household size (one versus multiple persons), and number of earners (zero, one, two or more). It also writes extraction and denominator audits.

## Strict boundaries

- Source: the existing 2024 ACS 1-year PUMS API extracts, **not yet reconciled against official bulk files**. `external_bulk_verified=False` is intentional.
- Household weight `WGTP` yields **descriptive point estimates only**. This release does not provide survey-design standard errors, confidence intervals, or statistical-significance claims. Future work requires replicate weights and official replicate-weight variance formulas.
- Numerator: weighted count of renters with `12 * GRNTP / HINCP >= threshold`. Denominator: renters with positive annual household income, nonnegative observed gross rent, and positive household weight. Nonpositive income is excluded, not imputed. No causal claims.
- All state, pooled New England, equal-state mean/median, and Maine-excluded comparisons are separate estimands.
- A subgroup comparison is omitted unless **all six states** have valid observations. Small subgroups may be unstable; no suppression or precision threshold has yet been implemented, so **do not publish subgroup estimates as final findings**.
- ACS PUMS is a **repeated cross-section**, not a household panel. Year-specific harmonization, income/housing inflation adjustment, and 2020 ACS standard 1-year gap are not addressed by this release.
- Age is the **householder's age**, not the age of all adults living in the unit. Renter burden is not the cost of forming an independent household and does not identify adults who cannot afford to live independently.

## Next milestone: V5.7 / V6 readiness

1. Obtain official 2024 ACS 1-year PUMS bulk extracts and independently reconcile per-state H/P counts, occupancy, and key totals.
2. Retain official household replicate weights (WGTP1–WGTP80), implement and test ACS variance estimation, and assess subgroup precision.
3. Extend 2021–2023 (and earlier years only with validated relationship-variable mappings), ensure year-specific survey definitions, deflators, and inflation adjustment.
4. Integrate validated regional series and subgroup analyses into the dashboard, preserving provenance and missing-year flags.
