"""V5.6 reproducible descriptive ACS PUMS stratification and extraction audits.

No survey-design confidence intervals or external bulk-file certification.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

STATES = {'09':'Connecticut','23':'Maine','25':'Massachusetts','33':'New Hampshire','44':'Rhode Island','50':'Vermont'}
REQUIRED = {'source_id','year','household_id','householder_age','household_size','adult_count','earner_count','household_income_annual','gross_rent_monthly','household_weight','tenure'}


def load_states(year=2024, root='data/external/pums_prepared', raw_root='data/raw/pums', require_audits=True):
    if year not in (2021,2022,2023,2024):
        raise ValueError('V5.6 only supports 2021–2024 with validated RELSHIPP mapping')
    frames = {}
    audit_rows = []
    for state, name in STATES.items():
        path = Path(root)/str(year)/f'state_{state}.csv'
        if not path.is_file():
            raise FileNotFoundError(f'Missing {path}; six-state analysis requires every state')
        df = pd.read_csv(path, dtype={'household_id':'string','source_id':'string'})
        if df.empty or REQUIRED - set(df):
            raise ValueError(f'Empty or missing required fields in {path}: {sorted(REQUIRED-set(df))}')
        source = f'ACS1_PUMS_{year}_ST{state}'
        if not df.source_id.eq(source).all() or not pd.to_numeric(df.year,errors='coerce').eq(year).all():
            raise ValueError(f'Source/year mismatch in {path}')
        if df.household_id.isna().any() or df.household_id.duplicated().any():
            raise ValueError(f'Missing or duplicate household identifiers in {path}')
        if not df.tenure.eq('renter').all():
            raise ValueError(f'Non-renter observation in {path}')
        audit_path = path.with_suffix('.audit.json')
        provenance_path = Path(raw_root)/str(year)/f'state_{state}_api'/'api_provenance.json'
        if require_audits and (not audit_path.is_file() or not provenance_path.is_file()):
            raise FileNotFoundError(f'Missing audit/provenance for {name}: {audit_path}, {provenance_path}')
        audit = json.loads(audit_path.read_text()) if audit_path.exists() else {}
        provenance = json.loads(provenance_path.read_text()) if provenance_path.exists() else {}
        if audit:
            if audit.get('source_id') != source or audit.get('prepared_renter_households') != len(df):
                raise ValueError(f'Audit mismatch in {audit_path}')
        if provenance:
            if str(provenance.get('state_fips')).zfill(2) != state or provenance.get('year') != year:
                raise ValueError(f'Provenance mismatch in {provenance_path}')
        audit_rows.append({'state':state,'name':name,'year':year,'prepared_rows':len(df),
                           'housing_units':audit.get('housing_units_input'),
                           'group_quarters_excluded':audit.get('group_quarters_excluded'),
                           'renter_households_before_missing_exclusions':audit.get('renter_households'),
                           'missing_rent_excluded':audit.get('excluded_missing_gross_rent'),
                           'missing_income_excluded':audit.get('excluded_missing_household_income'),
                           'api_household_records':provenance.get('households'),
                           'api_person_records':provenance.get('persons'),
                           'external_bulk_verified':False})
        df['state_fips'] = state
        frames[state] = df
    return pd.concat(frames.values(),ignore_index=True), pd.DataFrame(audit_rows)


def stratify(df):
    data=df.copy()
    for col in ('householder_age','household_size','adult_count','earner_count','household_income_annual','gross_rent_monthly','household_weight'):
        data[col]=pd.to_numeric(data[col],errors='coerce')
    data['age_group']=np.select([data.householder_age.between(25,34),data.householder_age.between(35,44),data.householder_age.between(45,54)],['25-34','35-44','45-54'],default='other')
    data['household_group']=np.where(data.household_size.eq(1),'one_person','two_plus_people')
    data['earner_group']=np.select([data.earner_count.eq(0),data.earner_count.eq(1),data.earner_count.ge(2)],['zero','one','two_plus'],default='unknown')
    data['valid_denominator']=(data.household_income_annual.gt(0)&data.gross_rent_monthly.ge(0)&data.household_weight.gt(0)&data.household_income_annual.notna()&data.gross_rent_monthly.notna())
    data['rent_income_ratio']=12*data.gross_rent_monthly/data.household_income_annual.where(data.household_income_annual.gt(0))
    return data


def _estimate(data,threshold):
    eligible=data.loc[data.valid_denominator]
    if eligible.empty:return None
    weights=eligible.household_weight
    if weights.sum()<=0:return None
    return {'sample_n':int(len(eligible)),'weighted_denominator':float(weights.sum()),
            'weighted_numerator':float(weights.loc[eligible.rent_income_ratio.ge(threshold)].sum()),
            'rate':float(weights.loc[eligible.rent_income_ratio.ge(threshold)].sum()/weights.sum())}


def analyze(data, thresholds=(.30,.50)):
    rows=[]
    for age in ('all','25-34','35-44','45-54'):
        for household in ('all','one_person','two_plus_people'):
            for earner in ('all','zero','one','two_plus'):
                sub=data
                if age!='all':sub=sub.loc[sub.age_group.eq(age)]
                if household!='all':sub=sub.loc[sub.household_group.eq(household)]
                if earner!='all':sub=sub.loc[sub.earner_group.eq(earner)]
                for threshold in thresholds:
                    state_stats={s:_estimate(sub.loc[sub.state_fips.eq(s)],threshold) for s in STATES}
                    if any(v is None for v in state_stats.values()):
                        continue  # No six-state benchmark if any state lacks observations.
                    others=[s for s in STATES if s!='23']
                    def pooled(states):
                        return sum(state_stats[s]['weighted_numerator'] for s in states)/sum(state_stats[s]['weighted_denominator'] for s in states)
                    def append(label,rate,n=None):
                        rows.append({'age_group':age,'household_group':household,'earner_group':earner,'threshold':threshold,
                                     'geography':label,'rate':rate,'sample_n':n,'uncertainty_status':'not_estimated',
                                     'external_bulk_verified':False})
                    for s in STATES:append(STATES[s],state_stats[s]['rate'],state_stats[s]['sample_n'])
                    append('New England pooled',pooled(list(STATES)))
                    append('New England state mean',float(np.mean([state_stats[s]['rate'] for s in STATES])))
                    append('New England state median',float(np.median([state_stats[s]['rate'] for s in STATES])))
                    append('Other five pooled',pooled(others))
                    append('Other five state mean',float(np.mean([state_stats[s]['rate'] for s in others])))
                    append('Other five state median',float(np.median([state_stats[s]['rate'] for s in others])))
    return pd.DataFrame(rows)
