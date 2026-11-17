# V5.3 — National renter housing-cost burden

## Research contribution

Adds observed annual ACS 1-year table B25070 for US renter-occupied housing units, all householder ages, as a distinct panel within Household evidence. The objective is to observe national renter housing-cost burden alongside, but **not merge with**, the age-specific B25007 tenure and B19049 household income data.

## Operational definitions

- Total renter-occupied housing units: B25070_001E.
- Not computed: B25070_011E.
- Eligible denominator: B25070_001E minus B25070_011E.
- Burdened at >=30% of household income: B25070_007E + _008E + _009E + _010E.
- Severely burdened at >=50%: B25070_010E.
- Gross rent generally includes contract rent plus estimated utilities and fuels paid by the renter; this is distinct from contract rent.
- Unit of observation: annual national estimate, not an individual household.
- ACS standard 1-year 2020 observations were not released; leave a visible gap. API failures are logged and not interpolated.

## Interpretation boundaries

B25070 does not disaggregate by householder age or household sharing. Its denominators differ from B19049 median household income and B25007 tenure. Do not claim that the national burden series estimates the cost burden of 25–34-year-olds. The percentage measures are descriptive, not causal and not financial-readiness measures. The 30% threshold is conventional, not a universal affordability criterion. Counts and shares are survey estimates with uncertainty; margins of error are not yet modeled. Survey-year household composition can change, and an index of income alone does not estimate income remaining after rent.

## Next research step

Locate harmonized ACS PUMS household-level records to jointly estimate householder age, household income, gross rent, household composition, and weights; compare exact age bands and solo/shared categories, while handling geographic coverage, income topcoding, negative/zero income, allocation flags, uncertainty, and repeated cross-sections. Do not interpret repeated cross-sections as following the same households.

Official variable documentation: https://api.census.gov/data/2024/acs/acs1/groups/B25070.json
