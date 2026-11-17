# V5.2.1 — Correcting the published Census ACS income age bands

## Source correction

The published ACS 1-year table **B19049** contains household-income medians by age of householder in **Under 25**, **25–44**, **45–64**, and **65+** age groups. It does **not** contain the 25–34, 35–44, and 45–54 categories of tenure table B25007. The V5.2 income downloader incorrectly expected the tenure bands and therefore rejected every year. This patch uses the actual B19049 labels and keeps the two charts independent. Never estimate a narrower group's median from published broader-group medians.

## Income comparability

B19049's metadata says "Median household income in the past 12 months (in [survey year] inflation-adjusted dollars)". Within a given survey, income is adjusted to that survey year's dollar reference; **different survey years are not expressed in one common dollar base**. The nominal/survey-year dollar chart is a descriptive published-level chart. For the *real income index* the app divides each survey-year median by annual average CPI and indexes each group to 2010=100. This is a **single cross-year deflation**, not double-deflation. Median income is household income, not an individual's earnings, after-tax resources, or savings. CPI annual averages approximate a survey-year price reference and are not a perfect match for the ACS interview-month adjustment.

## Limits and next research steps

The B19049 age bands do not resolve the main 25–34 research population; that requires a different source (potentially ACS PUMS microdata), with explicit household weights and treatment of household composition. No direct age-for-age comparison between the B19049 and B25007 lines is supported. No 2020 ACS standard one-year observations; do not interpolate.

The income panel remains a national descriptive time series, not evidence of household savings, independent living costs, or financial readiness.
