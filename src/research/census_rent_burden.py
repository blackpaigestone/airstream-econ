"""Observed national ACS 1-year B25070 gross-rent burden, all renter households.

Denominator excludes 'not computed' (B25070_011E). This table does NOT
identify the age of the householder or single-person household status.
"""
from pathlib import Path
import json
import os
import pandas as pd
import requests
from src.research.census_acs import API, _read_json, _safe_failure

GROUP = 'B25070'
CODES = ('B25070_001E', 'B25070_007E', 'B25070_008E',
         'B25070_009E', 'B25070_010E', 'B25070_011E')


def parse_burden(payload, year):
    if not isinstance(payload, list) or len(payload) != 2 or not all(isinstance(v, list) for v in payload):
        raise ValueError('Expected one national B25070 record')
    if len(payload[0]) != len(payload[1]):
        raise ValueError('B25070 header/value mismatch')
    rec = dict(zip(payload[0], payload[1]))
    if rec.get('us') != '1':
        raise ValueError('Expected national US geography')
    values = {}
    for code in CODES:
        raw = rec.get(code)
        if not isinstance(raw, str) or not raw.isdigit():
            raise ValueError(f'Invalid B25070 value for {code}: {raw!r}')
        values[code] = int(raw)
    total = values['B25070_001E']
    not_computed = values['B25070_011E']
    denominator = total - not_computed
    burden_30 = sum(values[code] for code in CODES[1:5])
    burden_50 = values['B25070_010E']
    if not (total > 0 and denominator > 0 and 0 <= burden_50 <= burden_30 <= denominator):
        raise ValueError('Inconsistent B25070 count totals')
    return {'source_id': 'CENSUS_ACS1_B25070', 'year': int(year),
            'total_renter_households': total, 'not_computed': not_computed,
            'computed_renter_households': denominator,
            'burden_30_households': burden_30, 'burden_50_households': burden_50,
            'burden_30_share': burden_30 / denominator,
            'burden_50_share': burden_50 / denominator,
            'source_url': f'{API}/{year}/acs/acs1/groups/{GROUP}.json'}


def fetch_burden_year(year, session=None, timeout=25):
    if not 2005 <= year <= 2100:
        raise ValueError('ACS year outside range')
    if year == 2020:
        raise ValueError('2020 ACS standard 1-year data were not released')
    session = session or requests.Session()
    params = {'get': ','.join(CODES), 'for': 'us:1'}
    key = os.getenv('CENSUS_API_KEY', '').strip()
    if key:
        params['key'] = key
    response = session.get(f'{API}/{year}/acs/acs1', params=params, timeout=timeout)
    return parse_burden(_read_json(response, context=f'{year} rent burden data'), year)


def validate_burden_panel(frame):
    required = {'source_id', 'year', 'total_renter_households', 'not_computed',
                'computed_renter_households', 'burden_30_households',
                'burden_50_households', 'burden_30_share', 'burden_50_share', 'source_url'}
    if not required.issubset(frame.columns) or frame.empty:
        raise ValueError('Missing or empty ACS B25070 panel')
    d = frame.copy()
    numeric = required - {'source_id', 'source_url'}
    for col in numeric:
        d[col] = pd.to_numeric(d[col], errors='raise')
    if d[list(numeric)].isna().any().any() or d.duplicated(['year']).any():
        raise ValueError('Missing or duplicate B25070 observations')
    if not d.source_id.eq('CENSUS_ACS1_B25070').all():
        raise ValueError('Unexpected source ID')
    if not (d.computed_renter_households == d.total_renter_households - d.not_computed).all():
        raise ValueError('Incorrect B25070 denominator')
    if not ((d.burden_50_households <= d.burden_30_households) &
            (d.burden_30_households <= d.computed_renter_households) &
            (d.computed_renter_households > 0)).all():
        raise ValueError('Invalid B25070 counts')
    for threshold in ('30', '50'):
        expected = d[f'burden_{threshold}_households'] / d.computed_renter_households
        if not ((d[f'burden_{threshold}_share'] - expected).abs() < 1e-9).all():
            raise ValueError(f'Incorrect {threshold}% burden share')
    return d.sort_values('year').reset_index(drop=True)


def load_burden_panel(path='data/external/census_acs_rent_burden.csv'):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f'ACS rent burden data missing: {p}')
    return validate_burden_panel(pd.read_csv(p))


def refresh_burden(start=2010, end=2024,
                   destination='data/external/census_acs_rent_burden.csv',
                   provenance='data/external/census_acs_rent_burden_provenance.json',
                   fetcher=fetch_burden_year):
    if not 2005 <= start <= end <= 2100:
        raise ValueError('Invalid ACS year range')
    rows, failures = [], []
    for year in range(start, end + 1):
        try:
            rows.append(fetcher(year))
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            failures.append({'year': year, 'reason': _safe_failure(exc)})
    if not rows:
        raise RuntimeError(f'No B25070 years retrieved; failures: {failures}')
    d = validate_burden_panel(pd.DataFrame(rows))
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(dest, index=False)
    record = {'source': 'US Census ACS 1-year B25070', 'geography': 'United States',
              'universe': 'renter-occupied housing units; all ages',
              'denominator': 'B25070_001E minus B25070_011E (not computed)',
              'burden_30_numerator': 'sum B25070_007E through B25070_010E',
              'burden_50_numerator': 'B25070_010E',
              'years_requested': [start, end], 'years_retrieved': [int(y) for y in d.year],
              'failures': failures, 'source_url': f'{API}/2024/acs/acs1/groups/{GROUP}.json',
              'limitations': 'Not age-specific, not solo/shared, not causal; 2020 ACS 1-year standard release absent; excludes not-computed cases.'}
    p = Path(provenance)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(record, indent=2) + '\n')
    return d, record
