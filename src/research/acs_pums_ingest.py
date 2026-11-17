"""V5.5: ingest matched ACS 1-year PUMS household/person CSV extracts.

Input is a *single state/year* pair of official unmodified PUMS CSV files.
No estimates are imputed. Output conforms to the V5.4 prepared extract schema.
"""
from pathlib import Path
import pandas as pd
import numpy as np

SOURCE_BASE = 'https://www.census.gov/programs-surveys/acs/microdata/access.html'
COLUMNS = ['source_id','source_url','year','household_id','householder_age',
           'household_size','adult_count','earner_count','tenure',
           'household_income_annual','gross_rent_monthly','household_weight']
H_COLS = ['SERIALNO','ST','NP','TEN','HINCP','GRNTP','WGTP']
P_COLS = ['SERIALNO','SPORDER','RELSHIPP','AGEP','WAGP','SEMP']


def _read_csv(path, columns):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    # Strings preserve leading zeros and avoid float-coerced household IDs.
    data = pd.read_csv(path, dtype={'SERIALNO':'string', 'ST':'string'}, low_memory=False)
    missing = set(columns) - set(data.columns)
    if missing:
        raise ValueError(f'{path.name}: missing required PUMS fields {sorted(missing)}; do not infer unavailable fields')
    return data[columns].copy()


def _number(frame, cols):
    for col in cols:
        frame[col] = pd.to_numeric(frame[col], errors='coerce')
    return frame


def prepare_pums(household_csv, person_csv, year, state_fips, *, source_url=SOURCE_BASE):
    """Return prepared renter households and an explicit ingestion audit.

    Household IDs are scoped to source_id (survey year and state). The output
    retains zero/negative HINCP for V5.4 to exclude from ratio denominators.
    Gross rent must be observed (GRNTP); no substitution with contract rent.
    """
    year = int(year)
    if year == 2020 or year < 2010 or year > 2024:
        raise ValueError('Supported ACS 1-year research window is 2010–2019, 2021–2024; 2020 unavailable')
    state = str(state_fips).zfill(2)
    if not state.isdigit() or len(state) != 2:
        raise ValueError('State must be a two-digit FIPS code')
    h = _number(_read_csv(household_csv, H_COLS), ['NP','TEN','HINCP','GRNTP','WGTP'])
    p = _number(_read_csv(person_csv, P_COLS), ['SPORDER','RELSHIPP','AGEP','WAGP','SEMP'])
    if h.SERIALNO.isna().any() or p.SERIALNO.isna().any():
        raise ValueError('Missing SERIALNO')
    if h.SERIALNO.duplicated().any():
        raise ValueError('Duplicate household SERIALNO')
    if h.ST.astype(str).str.zfill(2).ne(state).any():
        raise ValueError('Household input contains other states; supply one state/year pair')
    if p.duplicated(['SERIALNO','SPORDER']).any():
        raise ValueError('Duplicate person SERIALNO/SPORDER')
    unknown = set(p.SERIALNO) - set(h.SERIALNO)
    if unknown:
        raise ValueError('Person input includes households absent from supplied household file')
    # TEN=0 denotes group quarters, which have no household reference person.
    # Validate all person counts against their source records before restricting
    # the household-level analysis to occupied housing units.
    group_quarters_count = int(h.TEN.eq(0).sum())
    invalid_ten = h.TEN.isna() | ~h.TEN.isin([0,1,2,3,4])
    if invalid_ten.any():
        raise ValueError(f'Unexpected or missing TEN in {int(invalid_ten.sum())} records')
    housing_ids = set(h.loc[h.TEN.isin([1,2,3,4]), 'SERIALNO'])
    h = h.loc[h.TEN.isin([1,2,3,4])].copy()
    p = p.loc[p.SERIALNO.isin(housing_ids)].copy()
    # 2021–2024 RELSHIPP=20 identifies the reference person.
    # Earlier years require an explicit harmonization layer.
    if year not in (2021, 2022, 2023, 2024):
        raise ValueError('RELSHIPP mapping validated for 2021–2024 only')
    ref = p.loc[p.RELSHIPP.eq(20), ['SERIALNO','AGEP']]
    if ref.SERIALNO.duplicated().any():
        raise ValueError('Multiple reference persons for a household')
    people = p.groupby('SERIALNO', observed=True).agg(
        observed_people=('SPORDER','size'),
        adult_count=('AGEP',lambda x: int(x.ge(18).sum())),
        earner_count=('WAGP',lambda x: 0),
    ).reset_index()
    # Earners = positive wage + self-employment income; NOT all positive personal income.
    p['earned_income'] = p[['WAGP','SEMP']].fillna(0).sum(axis=1)
    earners = p.groupby('SERIALNO', observed=True)['earned_income'].apply(lambda s: int(s.gt(0).sum()))
    people['earner_count'] = people.SERIALNO.map(earners)
    merged = h.merge(people, on='SERIALNO', how='left', validate='one_to_one')
    merged = merged.merge(ref.rename(columns={'AGEP':'householder_age'}), on='SERIALNO', how='left', validate='one_to_one')
    if merged[['observed_people','householder_age','adult_count','earner_count']].isna().any().any():
        raise ValueError('Household missing people or reference person')
    if merged.NP.ne(merged.observed_people).any():
        raise ValueError('Household NP does not match person-record count')
    if merged[['NP','WGTP','householder_age']].isna().any().any() or merged.WGTP.le(0).any():
        raise ValueError('Missing or invalid household count, weight, or age')
    renter = merged.TEN.isin([3,4])
    eligible = merged.loc[renter].copy()
    missing_rent = eligible.GRNTP.isna() | eligible.GRNTP.lt(0)
    missing_income = eligible.HINCP.isna()
    # Missing rent/income is excluded from prepared extract, never filled with zero.
    good = eligible.loc[~(missing_rent | missing_income)].copy()
    source_id = f'ACS1_PUMS_{year}_ST{state}'
    out = pd.DataFrame({
        'source_id':source_id, 'source_url':source_url, 'year':year,
        'household_id':good.SERIALNO.astype(str),
        'householder_age':good.householder_age.astype(int),
        'household_size':good.NP.astype(int),
        'adult_count':good.adult_count.astype(int),
        'earner_count':good.earner_count.astype(int),
        'tenure':'renter', 'household_income_annual':good.HINCP,
        'gross_rent_monthly':good.GRNTP, 'household_weight':good.WGTP,
    }, columns=COLUMNS)
    audit = {'source_id':source_id, 'year':year, 'state_fips':state,
             'households_input':int(len(h) + group_quarters_count),
             'group_quarters_excluded':group_quarters_count,
             'housing_units_input':int(len(h)), 'person_records_housing_units':int(len(p)),
             'renter_households':int(len(eligible)),
             'excluded_missing_gross_rent':int(missing_rent.sum()),
             'excluded_missing_household_income':int(missing_income.sum()),
             'prepared_renter_households':int(len(out)),
             'nonpositive_income_retained_for_denominator_exclusion':int(out.household_income_annual.le(0).sum()),
             'source_url':source_url, 'household_file':Path(household_csv).name,
             'person_file':Path(person_csv).name,
             'limitations':'State/year ACS 1-year PUMS sample; household weight WGTP; no replicate-weight variance estimation in V5.5.'}
    if out.empty:
        raise ValueError('No renter households with observed HINCP and GRNTP')
    return out, audit
