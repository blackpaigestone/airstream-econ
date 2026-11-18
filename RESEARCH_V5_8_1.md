# V5.8.1: historical bulk ingestion pilot

**Canonical question:** Has the cost of maintaining economic freedom increased faster than the purchasing power of income—and has that change delayed the age at which people can meaningfully exercise economic independence?

This milestone introduces a **2015–2019 ACS1 PUMS bulk-file importer**, independent of the existing 2021–2024 API workflow. It matches household and person records, checks `NP`, requires an actual reference-person relationship code (`RELP=0` or `RELSHIPP=20`), excludes group quarters, counts adult and earned-income contributors, and preserves audit hashes. No income/rent imputation. Income <=0 is retained and later excluded from rent-to-income denominators.

The six-state bridge computes provisional weighted gross-rent burden >=30% using the V5.6 estimator and adds observations to a separate long-run panel. It does **not** relabel 1990/2000 benchmarks, claim that 2015–2019 and 2021–2024 are already harmonized, or assert that renters represent all people who might wish to live independently.

## Required future work

1. Validate official Census bulk-file sample counts and geography for every state/year.
2. Validate the exact source-specific codebooks and income/housing adjustment variables (e.g. `ADJINC`, `ADJHSG`) before comparing dollar amounts across years.
3. Implement ACS PUMS replicate-weight variance and confidence intervals; avoid over-interpreting small 25–34 living-alone samples.
4. Expand 2005–2014 with year-specific relationship, income and household schemas.
5. Obtain 1990 and 2000 harmonized decennial extracts (IPUMS USA) with documented variable mapping and sample-universe differences.
6. Construct household-formation outcomes among *all adults*, not only existing renters, for the timing-of-independence research question.

No 1990–2024 continuous annual series or causal conclusion is claimed.
