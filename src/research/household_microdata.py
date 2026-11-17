"""V5.4 validated household-level *prepared extract* analysis.

Not a raw PUMS parser. A household-person join, householder selection, gross-rent
harmonization, universe, and provenance must be verified upstream.
"""
from pathlib import Path
import pandas as pd
import numpy as np

REQUIRED = ('source_id','source_url','year','household_id','householder_age',
            'household_size','adult_count','earner_count','tenure',
            'household_income_annual','gross_rent_monthly','household_weight')
AGE_BANDS = {'25–34': (25,34), '35–44': (35,44), '45–54': (45,54)}
MIN_N = 30


def validate_households(frame):
    missing = set(REQUIRED)-set(frame.columns)
    if missing: raise ValueError(f'Missing household extract columns: {sorted(missing)}')
    if frame.empty: raise ValueError('Empty household extract')
    d = frame.copy()
    for col in ('source_id','source_url','household_id','tenure'):
        if d[col].isna().any() or d[col].astype(str).str.strip().eq('').any():
            raise ValueError(f'Missing values in {col}')
    for col in ('year','householder_age','household_size','adult_count','earner_count',
                'household_income_annual','gross_rent_monthly','household_weight'):
        d[col]=pd.to_numeric(d[col],errors='raise')
        if not np.isfinite(d[col].to_numpy(dtype=float)).all():
            raise ValueError(f'Nonfinite {col}')
    for col in ('year','householder_age','household_size','adult_count','earner_count'):
        if (d[col] != d[col].astype(int)).any(): raise ValueError(f'Noninteger {col}')
    if not d.tenure.isin(['renter','owner']).all(): raise ValueError('Tenure must be renter or owner')
    if (d.household_weight<=0).any(): raise ValueError('Weights must be positive')
    if ((d.household_size<1)|(d.adult_count<1)|(d.adult_count>d.household_size)|
        (d.earner_count<0)|(d.earner_count>d.household_size)).any():
        raise ValueError('Invalid household composition')
    if ((d.householder_age<15)|(d.householder_age>110)|(d.year<2000)|(d.year>2100)).any():
        raise ValueError('Invalid year or householder age')
    if (d.gross_rent_monthly<0).any(): raise ValueError('Gross rent cannot be negative')
    if d.duplicated(['source_id','year','household_id']).any():
        raise ValueError('Duplicate household identifier within source/year')
    # An explicit, independently reviewed metadata record is required for each extract.
    if d.source_url.astype(str).str.startswith('http').eq(False).any():
        raise ValueError('Missing source provenance URL')
    return d


def load_households(path='data/external/household_microdata_prepared.csv'):
    p=Path(path)
    if not p.exists(): raise FileNotFoundError(f'Prepared household extract unavailable: {p}')
    return validate_households(pd.read_csv(p, dtype={'household_id':str,'source_id':str}))


def summarize_renter_burden(frame, min_n=MIN_N):
    """Weighted renter burden by year, age and household size; no pooling of sources.

    The denominator is renters with strictly positive annual household income
    and nonnegative reported gross rent. Invalid ratios are excluded and counted.
    Multi-person != multi-adult; earner count is not inferred from household size.
    """
    d=validate_households(frame)
    d=d[d.tenure=='renter'].copy()
    d['age_band']=None
    for band,(lo,hi) in AGE_BANDS.items():
        d.loc[d.householder_age.between(lo,hi),'age_band']=band
    d=d[d.age_band.notna()].copy()
    d['household_type']=np.where(d.household_size==1,'one-person','multi-person')
    d['valid_ratio']=(d.household_income_annual>0)&(d.gross_rent_monthly>=0)
    d['ratio']=np.where(d.valid_ratio,12*d.gross_rent_monthly/d.household_income_annual,np.nan)
    rows=[]
    for (source,year,age,kind),g in d.groupby(['source_id','year','age_band','household_type'],sort=True):
        valid=g[g.valid_ratio]
        n=len(valid)
        if n<min_n: continue
        w=valid.household_weight.to_numpy(dtype=float)
        denom=w.sum()
        rows.append({'source_id':source,'year':int(year),'age_band':age,
                     'household_type':kind,'n_eligible':n,'n_excluded':len(g)-n,
                     'weighted_households':denom,
                     'burden_30_share':float(w[(valid.ratio>=.30).to_numpy()].sum()/denom),
                     'burden_50_share':float(w[(valid.ratio>=.50).to_numpy()].sum()/denom),
                     'effective_n':float(denom**2/(w*w).sum())})
    return pd.DataFrame(rows,columns=['source_id','year','age_band','household_type',
      'n_eligible','n_excluded','weighted_households','burden_30_share','burden_50_share','effective_n'])
