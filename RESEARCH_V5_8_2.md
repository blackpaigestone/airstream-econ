# V5.8.2 research boundaries

- Scope: 2015–2018 ACS 1-year PUMS, six New England states. Uses the existing V5.8.1 `prepare()` and `save()` contracts.
- ZIP integrity and extracted-file hash equality are checked. The run audit records source URLs and SHA-256 digests for each archive and CSV.
- The existing importer checks uniqueness, housing-person joins, NP matching, reference-person uniqueness, and eligible renter preparation.
- No external Census sample-count benchmark is independently reconciled; source completeness is **not certified**.
- No replicate-weight standard errors, confidence intervals, or inferential claims are calculated.
- No claim of comparable real-dollar incomes or rents across years. V5.8.1 outputs nominal fields and explicitly limits interpretation to ratios.
- `RELP` and `RELSHIPP` are resolved by V5.8.1 from actual columns. Year-specific survey semantics still require review before trend claims.
- Differences in subgroup row counts (516 vs 528 observed in the V5.8.1 panel) are not resolved by this patch. Do not infer complete or consistent coverage from a row count alone.
- 2020 standard ACS 1-year data remain absent; 1990/2000 decennial harmonization remains future work.
- Source archive URLs follow the official Census PUMS directory convention; if a year returns 404, the tool records the error instead of fabricating a substitute.
- This patch does not implement the proposed external record-count reconciliation or full cross-year coverage audit. Those remain outstanding validation gates.
