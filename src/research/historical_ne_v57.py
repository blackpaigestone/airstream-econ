"""Historical descriptive estimates from validated-by-pipeline six-state ACS1 PUMS.

Does not calculate survey-design standard errors or assert external sample completeness.
"""
import pandas as pd
from src.research.new_england_v56 import load_states, stratify, analyze

YEARS = (2021, 2022, 2023, 2024)


def historical(years=YEARS, prepared_root='data/external/pums_prepared', raw_root='data/raw/pums'):
    years = tuple(sorted(set(int(y) for y in years)))
    if not years or any(y not in YEARS for y in years):
        raise ValueError('Supported historical years: 2021–2024 only')
    results, audits = [], []
    for year in years:
        frame, audit = load_states(year, prepared_root, raw_root, require_audits=True)
        output = analyze(stratify(frame))
        if output.empty:
            raise RuntimeError(f'No valid six-state estimates for {year}')
        output.insert(0, 'year', year)
        audit.insert(0, 'analysis_year', year)
        results.append(output)
        audits.append(audit)
    return pd.concat(results, ignore_index=True), pd.concat(audits, ignore_index=True)


def compare_endpoints(history, first=None, last=None, *, threshold=.30, age='25-34', household='one_person', earner='all'):
    first = int(first if first is not None else history.year.min())
    last = int(last if last is not None else history.year.max())
    sub = history.loc[
        history.age_group.eq(age) & history.household_group.eq(household)
        & history.earner_group.eq(earner) & history.threshold.eq(threshold)
        & history.year.isin([first, last])
    ]
    pivot = sub.pivot(index='geography', columns='year', values='rate')
    if first not in pivot.columns or last not in pivot.columns:
        raise ValueError('Both endpoint years required for comparison')
    pivot = pivot[[first, last]].dropna().copy()
    pivot['change_percentage_points'] = 100 * (pivot[last] - pivot[first])
    return pivot.reset_index()
