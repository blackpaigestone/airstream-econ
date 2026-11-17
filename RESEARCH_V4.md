# V4 — Household economies and financial independence readiness

## Status

V4 adds **scenario modeling**, not new observed historical evidence. Existing V3 FRED charts remain observational national benchmarks. **No claim that 25–34-year-olds are worse off today has been established by this release.** No age-specific historical readiness curve is shown without real microdata.

## Four research questions

1. Has the economic value of a standardized real income gain changed for younger single-income renters?
2. Has the cost and economic option value of maintaining financial flexibility changed?
3. Under what circumstances does ownership outweigh the option value of mobility?
4. Has the age at which people can independently attain economic stability shifted, and how is that associated with household structure and expenses?

The primary *published* age bracket is **25–34**; 35–44 and 45–54 are comparison groups. Historical readiness at specific ages is a separate microdata research target. Avoid equating age with maturity or treating homeownership as the necessary outcome.

## Model definitions

- Adults = A, earners = E, dependent children = D.
- Monthly expenses = shared fixed costs + A × variable cost per adult + D × variable cost per dependent.
- Monthly net household income = E × net monthly income per earner (scenario simplification; actual earnings can differ).
- Monthly surplus = income − expenses.
- Per-adult cost = total expenses / A. Per-person cost = total expenses / (A + D). These are distinct from OECD or square-root *equivalized* welfare measures.
- Square-root equivalized household income = household income / sqrt(A + D). This is a sensitivity convention, not an empirical expenditure equation.
- Readiness threshold: nonnegative monthly surplus; monthly surplus/income at least user-chosen savings rate; liquid assets at least reserve-months × monthly essential expenses + relocation/opportunity fund.
- Months to reserve = remaining target / positive monthly surplus; otherwise unavailable. Assumes no return, inflation, income change, or shock.

A household can reduce *per-adult* fixed costs with cost-sharing without adding earners. Having multiple earners separately increases household income. Child expenses and economies of scale vary and cannot be inferred from household size alone.

## Observed-data integration contract

`src/research/households.py::readiness_by_age` requires a user-supplied household-year dataset with columns `year`, `age` (reference adult), `household_id`, `monthly_income`, `monthly_essentials`, `liquid_savings`, `adults`, `dependents`. It rejects duplicates, invalid values and missing columns; returns **unweighted** readiness shares by age and year. It is a validation/prototype function only, not a production survey estimator. It is **not wired to a synthetic dataset** or the dashboard.

Before estimating generational readiness: secure an appropriate documented dataset (e.g., BLS Consumer Expenditure Survey microdata for spending, Federal Reserve Survey of Consumer Finances for liquid assets/debt, Census CPS/ACS for incomes/household structure), verify the feasibility of jointly observing all required fields, use survey weights/replicate weights and correct variance estimation, harmonize age and family units, address survey redesigns, and report gaps instead of splicing incompatible survey populations. Cross-survey imputation would require explicit uncertainty and cannot be presented as directly observed household readiness.

## Historical identification plan

- Compare age 25–34 to the same age bracket in past years, using real (inflation-adjusted) consistent measures.
- Stratify one-adult one-earner households, shared-adult households by earners, and households with dependents, subject to sample sizes.
- Evaluate changes in real essential cost, surplus, liquid emergency coverage, and the age distribution of readiness **where a single dataset genuinely measures the ingredients**.
- Compare standardized housing/consumption bundles to actual spending to distinguish price shifts from composition/preferences.
- Report descriptive shifts first; causal attribution needs additional design and sensitivity checks.
- Treat the *independent household cost premium* as a descriptive cost ratio requiring comparable baskets: cost per adult living alone / cost per adult sharing. It is not directly identified from the simplified model.

## Research integrity

Hypothetical default inputs are **not historical data**, historical readiness ages, or evidence of a generational decline. Do not interpret the V4 bar chart as a BLS estimate. An observed historical readiness-age gap remains an open research question.
