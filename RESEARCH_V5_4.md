# V5.4 — Household-level affordability foundation

**Status: research infrastructure, not a populated historical microdata result.**

## Scope
The prepared extract is one row per household per source/year. A validated source-specific transformation must join household and person records and identify the actual householder. Do not treat every adult as the householder. The `source_id` and `source_url` must identify an official source and its vintage. No raw PUMS files are bundled and no example synthetic observations are treated as evidence.

## Required fields
See `data/external/household_microdata_prepared_SCHEMA.csv`. `household_income_annual` is annual household income in survey-reported dollars; `gross_rent_monthly` is gross monthly rent including relevant utilities, with harmonized definitions and documented top-codes. `household_weight` is the appropriate household survey weight. `adult_count` counts adults under an explicitly documented age rule; `earner_count` counts persons with earnings under a documented earnings definition. `household_size` is the total number of persons. `tenure` must be renter or owner. `household_id` must be unique within source and year. The schema is a **contract**, not a promise that every year of ACS PUMS exposes comparable variables.

## Measures and denominators
Only renter households with strictly positive annual household income and nonnegative gross monthly rent are in the computed-ratio denominator. Burden is 12 × gross monthly rent / annual household income. Weighted shares use household weights. Nonpositive-income households are excluded from the computed denominator and counted separately; they are not assumed affordable. The model suppresses cells with fewer than 30 unweighted eligible households. Results are separated by source, survey year, age of householder (25–34, 35–44, 45–54), and one-person versus multi-person household. Multi-person does **not** imply multiple adults or multiple earners.

## Limitations / required before publication
The app does not compute design-correct standard errors, replicate-weight intervals, statistical significance, causal sharing effects, or financial readiness. A real extract requires upstream checks for PUMS geography, household-person joins, codebooks and year-specific changes, survey design, inflation harmonization for dollar comparisons, missing data, and disclosure controls. Weighted burden shares are descriptive. Do not combine this output with published ACS B25070 estimates as though they had identical universes or sample definitions. V5.5 should implement and document a source-specific PUMS acquisition/harmonization pipeline, then V5.6 should add survey-design uncertainty and longitudinal QA.
