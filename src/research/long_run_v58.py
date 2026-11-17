"""V5.8: source-aware long-run research spine; no historical values fabricated.

Inputs are published/previously computed aggregates, NOT harmonized microdata.
The decennial adapter accepts only documented externally computed weighted counts.
"""
from pathlib import Path
import json
import pandas as pd

STATES = {'Connecticut','Maine','Massachusetts','New Hampshire','Rhode Island','Vermont'}
METRIC = 'renter_gross_rent_burden_ge_30pct'
BASE = ['year','geography','metric','age_group','household_group','earner_group','estimate','sample_n','source_id','source_type','weight_basis','comparability_status','variance_status','bulk_verified','notes']
DECADES = {1990,2000}


def inventory():
    rows=[]
    for year in range(1990,2025):
        if year in DECADES:
            source='DECENNIAL_PUMS'; status='awaiting_harmonized_extract'; cadence='decennial'
        elif year < 2005:
            source='NONE_IN_V58'; status='no_comparable_annual_ACS1_PUMS'; cadence='none'
        elif year == 2020:
            source='ACS1_PUMS'; status='no_standard_acs1_release'; cadence='none'
        elif year <= 2020:
            source='ACS1_PUMS'; status='requires_historical_variable_harmonization'; cadence='annual'
        elif year <= 2024:
            source='ACS1_PUMS'; status='available_from_v57_if_run'; cadence='annual'
        rows.append({'year':year,'source_family':source,'cadence':cadence,'coverage_status':status,
                     'independence_measure_status':'not_implemented',
                     'comparability_note':'Do not connect dissimilar survey measures as a continuous trend.'})
    return pd.DataFrame(rows)


def from_v57(path):
    frame=pd.read_csv(path)
    required={'year','geography','age_group','household_group','earner_group','threshold','rate','sample_n','external_bulk_verified','uncertainty_status'}
    if required-set(frame):raise ValueError(f'V5.7 input missing {sorted(required-set(frame))}')
    frame=frame.loc[frame.threshold.eq(.30)].copy()
    if frame.empty:raise ValueError('V5.7 input has no >=30% estimates')
    if not frame.year.isin([2021,2022,2023,2024]).all():raise ValueError('Unexpected V5.7 year')
    if frame.rate.isna().any() or ~frame.rate.between(0,1).all():raise ValueError('Invalid rates')
    out=pd.DataFrame({
        'year':frame.year.astype(int),'geography':frame.geography,'metric':METRIC,
        'age_group':frame.age_group,'household_group':frame.household_group,
        'earner_group':frame.earner_group,'estimate':frame.rate,'sample_n':frame.sample_n,
        'source_id':frame.year.map(lambda y:f'ACS1_PUMS_{y}_V57'),
        'source_type':'ACS1_PUMS_derived','weight_basis':'WGTP household weight',
        'comparability_status':'within_2021_2024_provisional',
        'variance_status':frame.uncertainty_status,
        'bulk_verified':frame.external_bulk_verified.astype(bool),
        'notes':'2021-24 descriptive renter sample; selected households only; not an independence formation rate',
    })
    return out[BASE]


def decennial_from_aggregates(path):
    """Strict import for independently harmonized decennial *weighted counts*.

    This deliberately does not guess the 1990/2000 tenure, income, rent,
    relationship, inflation, or sample weight mappings.
    """
    df=pd.read_csv(path)
    required={'year','geography','age_group','household_group','earner_group','weighted_burdened','weighted_eligible','sample_n','source_id','harmonization_document','weight_basis'}
    if required-set(df):raise ValueError(f'Decennial input missing {sorted(required-set(df))}')
    if df.empty:return pd.DataFrame(columns=BASE)
    if not df.year.isin(DECADES).all():raise ValueError('Decennial input only supports 1990 and 2000')
    if not df.geography.isin(STATES).all():raise ValueError('Only individual New England states accepted')
    for field in ('source_id','harmonization_document','weight_basis'):
        if df[field].isna().any() or df[field].astype(str).str.strip().eq('').any():raise ValueError(f'{field} must be documented')
    for field in ('weighted_burdened','weighted_eligible','sample_n'):
        df[field]=pd.to_numeric(df[field],errors='coerce')
    if df[['weighted_burdened','weighted_eligible','sample_n']].isna().any().any():raise ValueError('Missing weighted counts or sample size')
    if (df.weighted_eligible<=0).any() or (df.weighted_burdened<0).any() or (df.weighted_burdened>df.weighted_eligible).any() or (df.sample_n<1).any():
        raise ValueError('Invalid decennial denominator, numerator, or sample count')
    if df.duplicated(['year','geography','age_group','household_group','earner_group']).any():raise ValueError('Duplicate decennial cell')
    out=pd.DataFrame({
        'year':df.year.astype(int),'geography':df.geography,'metric':METRIC,
        'age_group':df.age_group,'household_group':df.household_group,'earner_group':df.earner_group,
        'estimate':df.weighted_burdened/df.weighted_eligible,'sample_n':df.sample_n,
        'source_id':df.source_id,'source_type':'DECENNIAL_PUMS_user_harmonized_aggregate',
        'weight_basis':df.weight_basis,'comparability_status':'not_yet_cross_survey_harmonized',
        'variance_status':'not_estimated','bulk_verified':False,
        'notes':'External harmonization document: '+df.harmonization_document.astype(str)+'; do not compare directly with ACS until validated',
    })
    return out[BASE]


def build(v57_path, decennial_path=None):
    frames=[from_v57(v57_path)]
    if decennial_path is not None:
        frames.append(decennial_from_aggregates(decennial_path))
    result=pd.concat(frames,ignore_index=True)
    key=['year','geography','metric','age_group','household_group','earner_group']
    if result.duplicated(key).any():raise ValueError('Duplicate long-run cells')
    return result.sort_values(key).reset_index(drop=True)


def write_outputs(out, panel):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    panel.to_csv(out/'long_run_panel.csv',index=False)
    inventory().to_csv(out/'source_coverage_1990_2024.csv',index=False)
    audit={'panel_rows':len(panel),'observed_years':sorted(int(y) for y in panel.year.unique()),
           'source_types':sorted(panel.source_type.unique().tolist()),
           'cross_survey_trend_validated':False,'variance_estimated':False,
           'official_bulk_completeness_verified':False,
           'warning':'1990/2000 are not automatically comparable to ACS; no interpolation; no independence rate yet.'}
    (out/'long_run_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    return audit
