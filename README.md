# The Economics of Mobility

An interactive Dash research prototype exploring generational housing affordability, the financial case for full-time motorhome living, and valuation of a specific 2020 Airstream Atlas Tommy Bahama.

## Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python refresh_data.py  # requires internet; retrieves and stores observed FRED CSV data
python -m pytest -q
python app.py
```

Open http://127.0.0.1:8050 . Historical charts explicitly show a missing-data notice until the refresh succeeds. No invented economic observations are bundled.

## Data policy

`data/raw/*.csv` is generated from official FRED series. The series register is in `src/data_sources.py`. Refresh is intentionally separate from dashboard startup; it never silently changes a chart during a presentation. Check series definitions and price-year units before combining measures.

## Research status

- **Implemented**: amortization, 36-month rent-versus-Atlas economic cost and cash-flow comparison; interactive sensitivity controls; J.D. Power guide benchmark; source register; route corridor; historical chart ingestion.
- **Not yet implemented**: age-adjusted historical housing burden; comparable RV transaction analysis; campground sampling; 2028 travel itinerary; state and provincial tax/insurance costs; Subaru keep/sell comparison; lender-versus-family-loan cash flows; quantitative uncertainty bands.
- **Evidence**: seller quoted $155,000 during buyer tour; guide benchmark $150,150 average retail and $124,600 low retail. Maintenance reported verbally and not yet documented.

## Key caution

This is an exploratory decision tool, not a certified vehicle appraisal or proof of generational causal effects. Resale value and travel operating expenses are user-defined assumptions. Rent comparison omits utility costs on rental side and moving/deposit alternatives until those are documented.
