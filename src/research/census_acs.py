"""Observed Census ACS 1-year national tenure-by-age counts (not readiness).

Uses public Census API B25007: tenure by age of householder. Data are
published population estimates, NOT household-level microdata or costs.
"""
from pathlib import Path
import json
import os
import re
import pandas as pd
import requests

API = 'https://api.census.gov/data'
GROUP = 'B25007'
BANDS = {'25–34': '25 to 34 years', '35–44': '35 to 44 years', '45–54': '45 to 54 years'}


def identify_variables(metadata):
    """Derive column IDs from official metadata, avoiding assumed positions."""
    variables = metadata['variables']
    out = {}
    for key, details in variables.items():
        if not re.fullmatch(r'B25007_\d{3}E', key):
            continue
        label = details.get('label', '')
        if '!!' not in label:
            continue
        tokens = [x.rstrip(':').strip() for x in label.split('!!')]
        if not tokens or 'Estimate' not in tokens[0]:
            continue
        for band, needle in BANDS.items():
            if any(needle.lower() in token.lower() for token in tokens):
                if any('owner occupied' in token.lower() for token in tokens):
                    tenure = 'owner'
                elif any('renter occupied' in token.lower() for token in tokens):
                    tenure = 'renter'
                else:
                    continue
                if (band, tenure) in out:
                    raise ValueError(f'Ambiguous ACS metadata for {band} {tenure}')
                out[(band, tenure)] = key
    expected = {(band, tenure) for band in BANDS for tenure in ('owner', 'renter')}
    if set(out) != expected:
        raise ValueError(f'ACS B25007 age/tenure mapping incomplete: {sorted(expected-set(out))}')
    return out


def parse_response(metadata, payload, year):
    mapping = identify_variables(metadata)
    if len(payload) != 2 or not isinstance(payload[0], list):
        raise ValueError('Expected one national ACS data record')
    record = dict(zip(payload[0], payload[1]))
    if record.get('us') != '1':
        raise ValueError('Expected US geography')
    rows = []
    for band in BANDS:
        counts = {}
        for tenure in ('owner', 'renter'):
            raw = record.get(mapping[(band, tenure)])
            if raw is None or not re.fullmatch(r'\d+', str(raw)):
                raise ValueError(f'Invalid ACS count {year} {band} {tenure}: {raw}')
            counts[tenure] = int(raw)
        total = counts['owner'] + counts['renter']
        if total == 0:
            raise ValueError('Zero households in ACS age cell')
        rows.append(dict(source_id='CENSUS_ACS1_B25007',year=year,age_band=band,
                         owner_households=counts['owner'],renter_households=counts['renter'],
                         total_households=total,renter_share=counts['renter']/total,
                         owner_share=counts['owner']/total,
                         source_url=f'{API}/{year}/acs/acs1/groups/{GROUP}.json'))
    return rows


def _read_json(response, *, context):
    """Reject Census HTML error pages, including HTTP-200 missing/invalid-key pages."""
    response.raise_for_status()
    content_type = response.headers.get('Content-Type', '').lower()
    if 'json' not in content_type:
        # Do not include response URLs or bodies: URLs may contain the API key.
        raise ValueError(f'{context}: Census returned non-JSON content ({content_type or "unknown"}); check API key and access')
    try:
        return response.json()
    except ValueError as exc:
        raise ValueError(f'{context}: Census returned malformed JSON') from exc


def fetch_year(year, session=None, timeout=25):
    if not 2005 <= year <= 2100:
        raise ValueError('ACS 1-year year outside expected range')
    if year == 2020:
        raise ValueError('2020 ACS standard 1-year data were not released')
    s = session or requests.Session()
    root = f'{API}/{year}/acs/acs1'
    metadata_resp = s.get(f'{root}/groups/{GROUP}.json', timeout=timeout)
    metadata = _read_json(metadata_resp, context=f'{year} metadata')
    mapping = identify_variables(metadata)
    fields = ['NAME'] + sorted(set(mapping.values()))
    params = {'get': ','.join(fields), 'for': 'us:1'}
    key = os.getenv('CENSUS_API_KEY', '').strip()
    if key:
        params['key'] = key
    # Passing the key only as a query parameter; never print the response URL.
    data_resp = s.get(root, params=params, timeout=timeout)
    payload = _read_json(data_resp, context=f'{year} data')
    return parse_response(metadata, payload, year)


def validate_panel(frame):
    required = {'source_id','year','age_band','owner_households','renter_households',
                'total_households','renter_share','owner_share','source_url'}
    if not required.issubset(frame.columns):
        raise ValueError(f'Missing ACS panel columns: {sorted(required-set(frame.columns))}')
    if frame.empty:
        raise ValueError('No ACS observations')
    d = frame.copy()
    for col in ('year','owner_households','renter_households','total_households','renter_share','owner_share'):
        d[col] = pd.to_numeric(d[col],errors='raise')
    if d[['year','owner_households','renter_households','total_households','renter_share','owner_share']].isna().any().any():
        raise ValueError('Missing ACS numeric values')
    if d.duplicated(['source_id','year','age_band']).any():
        raise ValueError('Duplicate ACS cells')
    if not d.age_band.isin(BANDS).all() or not d.source_id.eq('CENSUS_ACS1_B25007').all():
        raise ValueError('Unexpected ACS source or age band')
    if ((d.owner_households < 0)|(d.renter_households < 0)|(d.total_households <= 0)).any():
        raise ValueError('Invalid ACS counts')
    if not (d.owner_households+d.renter_households == d.total_households).all():
        raise ValueError('ACS count arithmetic mismatch')
    if not ((d.renter_households/d.total_households-d.renter_share).abs()<1e-9).all():
        raise ValueError('ACS renter share mismatch')
    if not ((d.owner_households/d.total_households-d.owner_share).abs()<1e-9).all():
        raise ValueError('ACS owner share mismatch')
    return d.sort_values(['age_band','year']).reset_index(drop=True)


def load_panel(path='data/external/census_acs_tenure_age.csv'):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'ACS tenure data missing: {path}; run python refresh_household_data.py')
    return validate_panel(pd.read_csv(path))


def _safe_failure(exc):
    """Never persist a request URL, which may contain the secret key."""
    if isinstance(exc, requests.RequestException):
        response = getattr(exc, 'response', None)
        status = getattr(response, 'status_code', None)
        return f'{type(exc).__name__} (HTTP {status})' if status else type(exc).__name__
    message = str(exc)
    key = os.getenv('CENSUS_API_KEY', '').strip()
    if key:
        message = message.replace(key, '[REDACTED]')
    return message[:300]

def refresh(start=2010, end=2024, destination='data/external/census_acs_tenure_age.csv',
            provenance='data/external/census_acs_tenure_age_provenance.json', fetcher=fetch_year):
    if not 2005 <= start <= end <= 2100:
        raise ValueError('Invalid year range')
    rows, failures = [], []
    for year in range(start,end+1):
        try:
            rows.extend(fetcher(year))
        except (requests.RequestException,ValueError,KeyError,TypeError) as exc:
            failures.append({'year':year,'reason':_safe_failure(exc)})
    if not rows:
        raise RuntimeError(f'No ACS years retrieved; nothing written. Failures: {failures}')
    d = validate_panel(pd.DataFrame(rows))
    dest = Path(destination)
    dest.parent.mkdir(parents=True,exist_ok=True)
    d.to_csv(dest,index=False)
    record = {'source':'US Census ACS 1-year detailed table B25007',
              'dataset':'acs/acs1','geography':'United States','age':'age of householder',
              'years_requested':[start,end],'years_retrieved':sorted(d.year.unique().tolist()),
              'failures':failures,'definitions':'Owner/renter occupied units by householder age; counts are published ACS estimates, not individuals or financial readiness.',
              'source_url':'https://api.census.gov/data.html'}
    prov = Path(provenance)
    prov.parent.mkdir(parents=True,exist_ok=True)
    prov.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    return d, record
