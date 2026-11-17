# V5.5.3 research protocol

- Scope: ACS 1-year PUMS **2021–2024 only**, six New England states, with 2024 first. These are repeated cross-sections, not a household panel.
- The 2024 person variable is `RELSHIPP`; Census code `20` is the reference person. `RELP` is not accepted by the live 2024 endpoint. Historical variable coding must be checked before expanding earlier than 2021.
- Household and person records join on `SERIALNO` **within state/year**. Household count `NP` must equal observed person records; incomplete responses are rejected.
- Rates use `WGTP` and households with positive observed income and valid gross rent; ratios are `12*GRNTP/HINCP`.
- Pooled regional estimate is household-weighted across six states; mean/median of state estimates treat each state equally. The five-state comparison excludes Maine from the benchmark.
- No confidence intervals, replicate-weight uncertainty, equivalence scale, causal interpretation, or historical inference is provided by this patch.
- **Completeness limitation:** matching `NP` and person counts does not prove API extraction completeness against Census bulk files. External count verification is required before publication or inference.
- **Size limitation:** API retrieval deliberately refuses responses of >=45,000 records; use official bulk PUMS for large states. Never interpret an incomplete regional set as New England.
- The existing dashboard's prepared CSV is not automatically replaced or extended by this patch. This avoids silently turning a Maine chart into a regional chart.
