"""V5: descriptive weighted household evidence from explicitly harmonized survey extracts.

This module does NOT download or claim to harmonize raw BLS/Census/SCF files.
Each input row is one household observation, with its own documented survey weight.
"""
from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED = ('source_id','year','household_id','age','adults','dependents','earners',
            'tenure','annual_disposable_income','annual_essential_spending',
            'liquid_assets','weight')
BANDS = ((25,34,'25–34'),(35,44,'35–44'),(45,54,'45–54'))


def validate_households(frame):
    missing = sorted(set(REQUIRED) - set(frame.columns))
    if missing:
        raise ValueError(f'Missing V5 columns: {missing}')
    if frame.empty:
        raise ValueError('No household observations')
    d = frame.loc[:,list(REQUIRED)].copy()
    for col in ('source_id','household_id','tenure'):
        if d[col].isna().any() or d[col].astype(str).str.strip().eq('').any():
            raise ValueError(f'Blank {col}')
        d[col] = d[col].astype(str).str.strip()
    for col in set(REQUIRED)-{'source_id','household_id','tenure'}:
        d[col] = pd.to_numeric(d[col],errors='raise')
        if not np.isfinite(d[col]).all():
            raise ValueError(f'Nonfinite {col}')
    for col in ('year','age','adults','dependents','earners'):
        if (d[col] != np.floor(d[col])).any():
            raise ValueError(f'{col} must be integer-valued')
        d[col] = d[col].astype(int)
    if not d['year'].between(1980,2100).all() or not d['age'].between(18,100).all():
        raise ValueError('Invalid year or reference-person age')
    if (d.adults < 1).any() or (d.dependents < 0).any() or (d.earners < 0).any() or (d.earners > d.adults).any():
        raise ValueError('Invalid household composition')
    if (d[['annual_disposable_income','annual_essential_spending','liquid_assets']] < 0).any().any():
        raise ValueError('Financial fields must be nonnegative')
    if (d.weight <= 0).any():
        raise ValueError('Survey weights must be positive')
    if not d.tenure.isin(('renter','owner','other')).all():
        raise ValueError('tenure must be renter, owner or other')
    if d.duplicated(['source_id','year','household_id']).any():
        raise ValueError('Duplicate source/year/household')
    return d


def summarize_households(frame, reserve_months=3, min_savings_rate=0.10, min_sample=30):
    """Within-source/year descriptive estimates; no pooling or cross-survey inference.

    Income and spending are annual amounts in the same dollar basis within each row.
    Liquid assets must be measured in that same dollar basis. Readiness is a proxy,
    not a validated historical measure of financial independence.
    """
    if reserve_months < 0 or not 0 <= min_savings_rate <= 1 or min_sample < 1:
        raise ValueError('Invalid analysis parameters')
    d = validate_households(frame)
    d['age_band'] = pd.NA
    for lo,hi,label in BANDS:
        d.loc[d.age.between(lo,hi),'age_band'] = label
    d = d.dropna(subset=['age_band']).copy()
    if d.empty:
        return pd.DataFrame(columns=['source_id','year','age_band','group','n','weighted_n','readiness_share','positive_cashflow_share','weighted_income','weighted_essential_spending','weighted_savings_capacity','weighted_per_adult_essentials','weighted_independent_premium'])
    d['cashflow'] = d.annual_disposable_income - d.annual_essential_spending
    d['positive'] = d.cashflow >= 0
    d['ready'] = ((d.annual_disposable_income > 0) &
                  (d.cashflow >= min_savings_rate*d.annual_disposable_income) &
                  (d.liquid_assets >= reserve_months*d.annual_essential_spending/12))
    d['per_adult_essentials'] = d.annual_essential_spending/d.adults
    d['group'] = 'all households'
    # A single adult renter is distinct from one earner in a larger household.
    solo = (d.adults == 1) & (d.dependents == 0) & (d.tenure == 'renter')
    shared = (d.adults >= 2) & (d.dependents == 0) & (d.tenure == 'renter')
    d.loc[solo,'group'] = 'solo adult renter'
    d.loc[shared,'group'] = 'shared adult renter'
    rows=[]
    for (source,year,band),part in d.groupby(['source_id','year','age_band'],sort=True):
        def weighted(p,col):
            return float(np.average(p[col],weights=p.weight)) if len(p) else float('nan')
        solo_p=part.loc[solo.reindex(part.index,fill_value=False)]
        shared_p=part.loc[shared.reindex(part.index,fill_value=False)]
        # Descriptive comparison of observed groups, NOT a causal cost-sharing effect.
        premium = (weighted(solo_p,'per_adult_essentials') / weighted(shared_p,'per_adult_essentials')
                   if len(solo_p)>=min_sample and len(shared_p)>=min_sample and weighted(shared_p,'per_adult_essentials')>0
                   else float('nan'))
        for group,p in [('all households',part),('solo adult renter',solo_p),('shared adult renter',shared_p)]:
            if len(p)<min_sample:
                continue
            rows.append(dict(source_id=source,year=int(year),age_band=band,group=group,
                n=len(p),weighted_n=float(p.weight.sum()),
                readiness_share=weighted(p,'ready'),positive_cashflow_share=weighted(p,'positive'),
                weighted_income=weighted(p,'annual_disposable_income'),
                weighted_essential_spending=weighted(p,'annual_essential_spending'),
                weighted_savings_capacity=weighted(p,'cashflow'),
                weighted_per_adult_essentials=weighted(p,'per_adult_essentials'),
                weighted_independent_premium=premium if group=='all households' else float('nan')))
    return pd.DataFrame(rows)


def load_evidence(path='data/external/household_harmonized.csv', **kwargs):
    path=Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'No harmonized household extract at {path}; see RESEARCH_V5.md')
    return summarize_households(pd.read_csv(path),**kwargs)
