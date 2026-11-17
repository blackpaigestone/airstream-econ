"""Observed ACS 1-year B19049 median household income by age of householder.

Published group medians cannot be aggregated or interpreted as individual wages.
"""
from pathlib import Path
import json
import os
import re
import pandas as pd
import requests
from src.research.census_acs import API, _read_json, _safe_failure

# Published ACS B19049 categories, not the narrower B25007 tenure categories.
INCOME_BANDS = {
    "Under 25": "Householder under 25 years",
    "25–44": "Householder 25 to 44 years",
    "45–64": "Householder 45 to 64 years",
    "65+": "Householder 65 years and over",
}

GROUP='B19049'

def identify_income_variables(metadata):
    out={}
    for key,detail in metadata['variables'].items():
        if not re.fullmatch(r'B19049_\d{3}E',key): continue
        label=detail.get('label','')
        if 'Estimate' not in label: continue
        tokens=[v.strip().rstrip(':') for v in label.split('!!')]
        for band,needle in INCOME_BANDS.items():
            if any(needle.lower() in token.lower() for token in tokens):
                if band in out: raise ValueError(f'Ambiguous ACS B19049 income variable for {band}')
                out[band]=key
    if set(out)!=set(INCOME_BANDS):
        raise ValueError(f'ACS B19049 income mapping incomplete: {sorted(set(INCOME_BANDS)-set(out))}')
    return out

def parse_income(metadata,payload,year):
    mapping=identify_income_variables(metadata)
    if not isinstance(payload,list) or len(payload)!=2 or not all(isinstance(x,list) for x in payload):
        raise ValueError('Expected one national ACS income record')
    if len(payload[0])!=len(payload[1]):raise ValueError('ACS income header/value mismatch')
    record=dict(zip(payload[0],payload[1]))
    if record.get('us')!='1':raise ValueError('Expected US geography')
    rows=[]
    for band,key in mapping.items():
        raw=record.get(key)
        if not isinstance(raw,str) or not re.fullmatch(r'\d+',raw) or int(raw)<=0:
            raise ValueError(f'Invalid ACS median income {year} {band}: {raw}')
        rows.append({'source_id':'CENSUS_ACS1_B19049','year':year,'age_band':band,
                     'median_household_income':int(raw),
                     'source_url':f'{API}/{year}/acs/acs1/groups/{GROUP}.json'})
    return rows

def fetch_income_year(year,session=None,timeout=25):
    if not 2005<=year<=2100:raise ValueError('ACS year outside range')
    if year==2020:raise ValueError('2020 ACS standard 1-year data were not released')
    session=session or requests.Session()
    root=f'{API}/{year}/acs/acs1'
    metadata=_read_json(session.get(f'{root}/groups/{GROUP}.json',timeout=timeout),context=f'{year} income metadata')
    mapping=identify_income_variables(metadata)
    params={'get':','.join(['NAME']+sorted(mapping.values())),'for':'us:1'}
    key=os.getenv('CENSUS_API_KEY','').strip()
    if key:params['key']=key
    payload=_read_json(session.get(root,params=params,timeout=timeout),context=f'{year} income data')
    return parse_income(metadata,payload,year)

def validate_income_panel(frame):
    cols={'source_id','year','age_band','median_household_income','source_url'}
    if not cols.issubset(frame):raise ValueError('Missing ACS income columns')
    if frame.empty:raise ValueError('Empty ACS income panel')
    d=frame.copy()
    for col in ('year','median_household_income'):
        d[col]=pd.to_numeric(d[col],errors='raise')
    if d[['year','median_household_income']].isna().any().any():raise ValueError('Missing income values')
    if (d.median_household_income<=0).any() or not d.age_band.isin(INCOME_BANDS).all() or not d.source_id.eq('CENSUS_ACS1_B19049').all():
        raise ValueError('Invalid ACS income cell')
    if d.duplicated(['year','age_band']).any():raise ValueError('Duplicate ACS income cell')
    return d.sort_values(['age_band','year']).reset_index(drop=True)

def load_income_panel(path='data/external/census_acs_income_age.csv'):
    p=Path(path)
    if not p.exists():raise FileNotFoundError(f'ACS income data missing: {p}')
    return validate_income_panel(pd.read_csv(p))

def real_income_index(frame,cpi_path,base_year=2010):
    """Normalize each survey-year dollar median by annual CPI, then index to base year.

ACS B19049 uses the survey year as its inflation-adjusted dollar reference;
across survey years, these are year-specific dollar levels, not a common base.
"""
    cpi=pd.read_csv(cpi_path)
    if not {'date','value'}.issubset(cpi):raise ValueError('CPI requires date,value columns')
    cpi['year']=pd.to_datetime(cpi['date'],errors='raise').dt.year
    cpi['value']=pd.to_numeric(cpi['value'],errors='raise')
    annual=cpi.groupby('year',as_index=False)['value'].mean().rename(columns={'value':'cpi'})
    if (annual.cpi<=0).any():raise ValueError('Nonpositive CPI')
    d=validate_income_panel(frame).merge(annual,on='year',how='inner',validate='many_to_one')
    if d.empty:raise ValueError('No overlapping income and CPI years')
    d['real_proxy']=d.median_household_income/d.cpi
    bases=d.loc[d.year.eq(base_year),['age_band','real_proxy']].rename(columns={'real_proxy':'base_real'})
    if set(bases.age_band)!=set(INCOME_BANDS):raise ValueError(f'Income baseline {base_year} missing for one or more age bands')
    d=d.merge(bases,on='age_band',validate='many_to_one')
    d['real_income_index']=100*d.real_proxy/d.base_real
    return d.drop(columns=['real_proxy','base_real'])

def refresh_income(start=2010,end=2024,destination='data/external/census_acs_income_age.csv',
                   provenance='data/external/census_acs_income_age_provenance.json',fetcher=fetch_income_year):
    if not 2005<=start<=end<=2100:raise ValueError('Invalid ACS year range')
    rows=[];failures=[]
    for year in range(start,end+1):
        try:rows.extend(fetcher(year))
        except (requests.RequestException,ValueError,KeyError,TypeError) as exc:
            failures.append({'year':year,'reason':_safe_failure(exc)})
    if not rows:raise RuntimeError(f'No ACS income years retrieved; failures: {failures}')
    d=validate_income_panel(pd.DataFrame(rows))
    dest=Path(destination);dest.parent.mkdir(parents=True,exist_ok=True);d.to_csv(dest,index=False)
    record={'source':'US Census ACS 1-year B19049','geography':'United States',
            'population':'households by age of householder','measure':'median household income in survey-year inflation-adjusted dollars (ACS B19049)',
            'years_requested':[start,end],'years_retrieved':sorted(d.year.unique().tolist()),
            'failures':failures,'source_url':'https://api.census.gov/data.html',
            'warning':'Published B19049 age bands are Under 25, 25–44, 45–64, 65+; these are household medians, not wages or disposable income. Each survey year uses its own price reference; normalize with CPI for longitudinal comparisons.'}
    p=Path(provenance);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(record,indent=2)+'\n')
    return d,record
