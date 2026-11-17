"""ACS 1-year PUMS API retrieval, bounded and fail-closed.

Retrieves *complete* state-level housing/person records for a small state only.
If response volume approaches a possible API ceiling, refuses to write and
instructs caller to use the official bulk PUMS files instead.
"""
import json
import os
from pathlib import Path
import requests
import pandas as pd

H_FIELDS = ('SERIALNO','NP','TEN','HINCP','GRNTP','WGTP')
P_FIELDS = ('SERIALNO','SPORDER','RELSHIPP','AGEP','WAGP','SEMP')
API_ROOT = 'https://api.census.gov/data'
SAFE_MAX_ROWS = 45000  # deliberately conservative; not a claim about Census's actual cap


def _payload(response, url):
    response.raise_for_status()
    try:
        value = response.json()
    except (ValueError, TypeError) as exc:
        raise RuntimeError(f'Census returned non-JSON data for {url}; verify API key and endpoint') from exc
    if not isinstance(value, list) or len(value) < 2 or not isinstance(value[0], list):
        raise RuntimeError(f'Unexpected or empty PUMS response from {url}: {str(value)[:180]}')
    columns = value[0]
    if len(set(columns)) != len(columns) or any(len(row) != len(columns) for row in value[1:]):
        raise RuntimeError('Malformed Census PUMS response')
    return pd.DataFrame(value[1:], columns=columns)


def retrieve_state_pums(year, state, *, key=None, session=None, safe_max_rows=SAFE_MAX_ROWS):
    year = int(year)
    if year not in (2021, 2022, 2023, 2024):
        raise ValueError('API-first pilot supports 2021–2024 only; earlier years require year-specific harmonization')
    state = str(state).zfill(2)
    if len(state) != 2 or not state.isdigit():
        raise ValueError('State must be a two-digit FIPS code')
    key = key or os.environ.get('CENSUS_API_KEY')
    if not key:
        raise RuntimeError('Set CENSUS_API_KEY in your shell; never place keys in files or Git')
    session = session or requests.Session()
    url = f'{API_ROOT}/{year}/acs/acs1/pums'
    result = {}
    for record_type, fields in [('H', H_FIELDS), ('P', P_FIELDS)]:
        params = {'get': ','.join(fields), 'for': f'state:{int(state)}', 'RT': record_type, 'key': key}
        response = session.get(url, params=params, timeout=120)
        try:
            frame = _payload(response, url)
        except requests.HTTPError as exc:
            detail = response.text[:350] if hasattr(response, 'text') else ''
            raise RuntimeError(f'Census {record_type} request failed for {year} state {state}: {detail}') from exc
        required = set(fields) | {'RT', 'state'}
        missing_columns = required - set(frame.columns)
        if missing_columns:
            raise RuntimeError(f'PUMS {record_type} response missing columns: {sorted(missing_columns)}')
        if len(frame) >= safe_max_rows:
            raise RuntimeError(f'{record_type} query returned {len(frame)} rows; completeness cannot be guaranteed. Use official bulk files for this state/year.')
        if not frame.RT.eq(record_type).all():
            raise RuntimeError(f'Unexpected record type in {record_type} response')
        geo_col = 'state' if 'state' in frame.columns else 'ST' if 'ST' in frame.columns else None
        if geo_col is None or not frame[geo_col].astype(str).str.zfill(2).eq(state).all():
            raise RuntimeError(f'PUMS {record_type} geography mismatch')
        if frame.SERIALNO.isna().any() or frame.SERIALNO.duplicated().any() and record_type == 'H':
            raise RuntimeError(f'Invalid SERIALNO values in {record_type} response')
        if record_type == 'H':
            frame['ST'] = state
            # Vacant units have no person records. Only occupied households are joined.
            frame = frame[pd.to_numeric(frame.NP, errors='coerce').gt(0)].copy()
            frame = frame[['SERIALNO', 'ST', 'NP', 'TEN', 'HINCP', 'GRNTP', 'WGTP']]
        else:
            frame = frame[frame.SERIALNO.isin(result['H'].SERIALNO)].copy()
            frame = frame[list(P_FIELDS)]
        result[record_type] = frame
    if result['H'].empty or result['P'].empty:
        raise RuntimeError('No matching occupied household/person observations')
    missing = set(result['H'].SERIALNO) - set(result['P'].SERIALNO)
    if missing:
        raise RuntimeError(f'{len(missing)} occupied households lack person records; aborting incomplete API extraction')
    if result['P'].duplicated(['SERIALNO', 'SPORDER']).any():
        raise RuntimeError('Duplicate person identifiers in PUMS response')
    person_counts = result['P'].groupby('SERIALNO').size()
    expected_counts = pd.to_numeric(result['H'].set_index('SERIALNO')['NP'], errors='coerce')
    if expected_counts.isna().any() or not expected_counts.eq(person_counts.reindex(expected_counts.index)).all():
        raise RuntimeError('Person record counts do not match household NP; incomplete or inconsistent API extraction')
    provenance = {'source': url, 'year': year, 'state_fips': state,
                  'retrieval_method': 'Census ACS1 PUMS API; RT=H and RT=P; for=state',
                  'households': len(result['H']), 'persons': len(result['P']), 'relationship_variable': 'RELSHIPP', 'reference_person_code': 20,
                  'safety_max_rows_per_response': safe_max_rows,
                  'warning': 'Internal household/person count checks passed; external completeness is NOT certified. Cross-check official bulk files before inference.'}
    return result['H'], result['P'], provenance


def save_raw(h, p, provenance, root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    paths = (root / 'households_api.csv', root / 'persons_api.csv', root / 'api_provenance.json')
    if any(path.exists() for path in paths):
        raise FileExistsError(f'Existing API extract in {root}; move or remove it deliberately before refreshing')
    h.to_csv(paths[0], index=False)
    p.to_csv(paths[1], index=False)
    paths[2].write_text(json.dumps(provenance, indent=2) + '\n')
    return paths
