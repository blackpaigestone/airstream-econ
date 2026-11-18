"""V5.8.1: conservative importer for user-supplied official ACS1 PUMS bulk CSV.

Supports 2015–2019 only; no claim of external bulk completeness.
RELP=0 and RELSHIPP=20 are selected from actual person-file columns, not guessed.
"""
from pathlib import Path
import hashlib
import json
import pandas as pd

STATES={'09':'Connecticut','23':'Maine','25':'Massachusetts','33':'New Hampshire','44':'Rhode Island','50':'Vermont'}
BASE=['source_id','source_url','year','household_id','householder_age','household_size','adult_count','earner_count','tenure','household_income_annual','gross_rent_monthly','household_weight']

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def prepare(households, persons, year, state, *, relationship=None):
    year=int(year);state=str(state).zfill(2)
    if year not in range(2015,2020) or state not in STATES:
        raise ValueError('Pilot accepts 2015–2019 and six New England states only')
    h=pd.read_csv(households,dtype={'SERIALNO':'string','ST':'string'},low_memory=False)
    p=pd.read_csv(persons,dtype={'SERIALNO':'string'},low_memory=False)
    hc={'SERIALNO','ST','NP','TEN','HINCP','GRNTP','WGTP'}
    pc={'SERIALNO','SPORDER','AGEP','WAGP','SEMP'}
    if hc-set(h) or pc-set(p):raise ValueError(f'Missing housing {sorted(hc-set(h))} or person {sorted(pc-set(p))} fields')
    available=[(x,code) for x,code in [('RELP',0),('RELSHIPP',20)] if x in p]
    if relationship is None:
        if len(available)!=1:raise ValueError('Specify --relationship RELP or RELSHIPP when ambiguous/unavailable')
        relationship=available[0][0]
    if relationship not in ('RELP','RELSHIPP') or relationship not in p:
        raise ValueError('Relationship column missing or unsupported')
    code={'RELP':0,'RELSHIPP':20}[relationship]
    if h.SERIALNO.isna().any() or h.SERIALNO.duplicated().any():raise ValueError('Invalid housing SERIALNO')
    if p.SERIALNO.isna().any() or p.duplicated(['SERIALNO','SPORDER']).any():raise ValueError('Invalid person identifiers')
    if h.ST.astype('string').str.zfill(2).ne(state).any():raise ValueError('Housing state mismatch')
    if not set(p.SERIALNO).issubset(set(h.SERIALNO)):raise ValueError('Unmatched person SERIALNO')
    for col in ['NP','TEN','HINCP','GRNTP','WGTP']:h[col]=pd.to_numeric(h[col],errors='coerce')
    for col in ['SPORDER','AGEP','WAGP','SEMP',relationship]:p[col]=pd.to_numeric(p[col],errors='coerce')
    # Group quarters are not occupied households; keep explicit exclusion count.
    gq=h.TEN.eq(0)
    occupied=h.loc[h.TEN.isin([1,2,3,4]) & h.NP.gt(0)].copy()
    people=p.loc[p.SERIALNO.isin(occupied.SERIALNO)].copy()
    counts=people.groupby('SERIALNO').size()
    if occupied.empty or not occupied.set_index('SERIALNO').NP.eq(counts.reindex(occupied.SERIALNO).to_numpy()).all():
        raise ValueError('Missing people or NP count mismatch; bulk extract incomplete')
    refs=people.loc[people[relationship].eq(code),['SERIALNO','AGEP']]
    if refs.SERIALNO.duplicated().any() or set(refs.SERIALNO)!=set(occupied.SERIALNO):
        raise ValueError('Expected exactly one relationship-coded reference person per occupied household')
    people['earned']=people[['WAGP','SEMP']].fillna(0).sum(axis=1)
    agg=people.groupby('SERIALNO').agg(adult_count=('AGEP',lambda x:int(x.ge(18).sum())),earner_count=('earned',lambda x:int(x.gt(0).sum())))
    merged=occupied.merge(refs.rename(columns={'AGEP':'householder_age'}),on='SERIALNO',validate='one_to_one').join(agg,on='SERIALNO',validate='one_to_one')
    if merged[['WGTP','householder_age','adult_count','earner_count']].isna().any().any() or merged.WGTP.le(0).any():
        raise ValueError('Invalid weight, age, or household composition')
    renters=merged.loc[merged.TEN.isin([3,4])].copy()
    missing_rent=renters.GRNTP.isna()|renters.GRNTP.lt(0)
    missing_income=renters.HINCP.isna()
    good=renters.loc[~(missing_rent|missing_income)].copy()
    if good.empty:raise ValueError('No eligible renters')
    sid=f'ACS1_PUMS_{year}_ST{state}'
    out=pd.DataFrame({'source_id':sid,'source_url':'https://www.census.gov/programs-surveys/acs/microdata/access.html',
      'year':year,'household_id':good.SERIALNO.astype('string'),'householder_age':good.householder_age.astype(int),
      'household_size':good.NP.astype(int),'adult_count':good.adult_count.astype(int),'earner_count':good.earner_count.astype(int),
      'tenure':'renter','household_income_annual':good.HINCP,'gross_rent_monthly':good.GRNTP,'household_weight':good.WGTP})[BASE]
    audit={'source_id':sid,'year':year,'state_fips':state,'relationship_variable':relationship,'reference_person_code':code,
      'housing_rows':len(h),'person_rows':len(p),'group_quarters_excluded':int(gq.sum()),'occupied_households':len(occupied),
      'renter_households':len(renters),'excluded_missing_gross_rent':int(missing_rent.sum()),
      'excluded_missing_household_income':int(missing_income.sum()),'prepared_renter_households':len(out),
      'housing_sha256':digest(households),'persons_sha256':digest(persons),'bulk_verified':False,
      'monetary_note':'Unadjusted nominal PUMS HINCP/GRNTP; ratio only, no cross-year dollar comparison.',
      'limitations':'Official-file provenance must be checked manually; no external sample count certification or replicate-weight variance.'}
    return out,audit

def save(prepared,audit,root):
    root=Path(root);path=root/str(audit['year'])/f"state_{audit['state_fips']}.csv"
    apath=path.with_suffix('.audit.json')
    if path.exists() or apath.exists():raise FileExistsError(f'Will not overwrite {path}')
    path.parent.mkdir(parents=True,exist_ok=True)
    prepared.to_csv(path,index=False)
    apath.write_text(json.dumps(audit,indent=2)+'\n')
    return path
