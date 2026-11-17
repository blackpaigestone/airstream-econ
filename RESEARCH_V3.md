# V3 — Historical Evidence: National Benchmarks

## Central question
Has the cost of maintaining economic freedom increased faster than the purchasing power of income?

V3 establishes **descriptive national benchmarks**, not a definitive answer. The ultimate target population is younger single-income renter households, which these national series do **not** identify.

## Three complementary research questions
1. Does the same real income gain produce less financial independence today? **Not yet identified.** The V3 chart compares levels and relative housing burdens, not the marginal benefit of an income gain.
2. Has the cost and value of preserving financial flexibility changed? **Not yet estimated.** A defensible historical reference basket needs liquid assets, household expenditure, moving/exit costs, and location-specific employment options.
3. When does asset ownership outweigh mobility's option value? **Not yet estimated.** V2 provides scenarios; historical regional opportunity and transaction cost data are required.

## Computation and provenance
All inputs are the seven FRED CSV files already fetched into `data/raw`. V3 uses `CPIAUCSL`, `MEHOINUSA672N`, `MSPUS`, `USSTHPI`, and `MORTGAGE30US`. The source register lives in `src/data_sources.py`.

- Annual means for monthly, quarterly and weekly series; annual household income as reported. This is a transparent approximation, not a period-end valuation or vintage-corrected dataset.
- Inner join by calendar year: missing years remain missing. No extrapolation or interpolation.
- Default baseline 1990=100; final year is the last **common** year across all five sources, not necessarily 2026.
- `MEHOINUSA672N` is **already inflation adjusted**. Never deflate it again. Its published dollar base may differ from the current CPI reference period, so V3 uses **relative changes** rather than dividing nominal home prices by its reported dollar levels.
- Real home price index = (nominal median new-home sale price / CPI), indexed to 1990.
- Real FHFA index = (FHFA HPI / CPI), indexed to 1990. FHFA all-transactions index and new-home median prices describe different housing concepts.
- Relative new-home price-to-income burden = real new-home price index / real median household income index, rebased to 100. **Not a literal dollar price-to-income multiple.**
- Relative mortgage-payment burden = annual median new-home sale price × standard 30-year fixed-rate amortization factor, divided by CPI and real median household income, rebased to 100. Constant loan-to-value assumption cancels in the index. This is **not actual household payment-to-income**, and excludes taxes, insurance, PMI, down payment, fees and credit availability.
- No causal attribution, uncertainty intervals, or cohort-specific claims.

## Reproducibility
Run `python refresh_data.py`, then `python -m pytest -q`, then `python app.py`. Historical Evidence tab loads local CSVs and reports missing data instead of inventing it.

## Next data acquisition priorities
1. BLS Consumer Expenditure Survey by age and household composition; check comparability across years.
2. Federal Reserve SCF household microdata or published age/household tables for liquid wealth, debt and tenure.
3. Census income by age and household type; avoid comparing national household median to an individual wage.
4. BEA regional price parities, BLS occupational/regional employment, Census migration, and regional housing data.
5. Explicit cost-of-relocation/lease-exit measures, with documented coverage and uncertainty.

## Household strategy context
The Atlas is an asset with depreciation, operating costs and potential debt. Remote employment is the base income; artist-representation business is a separately modeled uncertain venture. Homeownership, overseas living, continued travel, and business-building remain possible future outcomes, not a fixed terminal objective.
