import pandas as pd
import pytest
from src.research.long_run_v58 import inventory,decennial_from_aggregates,from_v57,build

def test_coverage_distinguishes_decennial_2020_and_acs():
    d=inventory().set_index('year')
    assert d.loc[1990,'source_family']=='DECENNIAL_PUMS'
    assert d.loc[2020,'coverage_status']=='no_standard_acs1_release'
    assert d.loc[2010,'coverage_status']=='requires_historical_variable_harmonization'
    assert d.loc[2024,'source_family']=='ACS1_PUMS'

def test_v57_adapter(tmp_path):
    p=tmp_path/'v57.csv'
    pd.DataFrame([dict(year=2024,geography='Maine',age_group='25-34',household_group='one_person',earner_group='all',threshold=.3,rate=.49,sample_n=75,external_bulk_verified=False,uncertainty_status='not_estimated')]).to_csv(p,index=False)
    d=from_v57(p)
    assert len(d)==1 and d.iloc[0].estimate==.49
    assert d.iloc[0].comparability_status=='within_2021_2024_provisional'

def test_decennial_fails_closed_on_missing_provenance(tmp_path):
    p=tmp_path/'dec.csv'
    pd.DataFrame([dict(year=1990,geography='Maine',age_group='25-34',household_group='one_person',earner_group='all',weighted_burdened=2,weighted_eligible=4,sample_n=4,source_id='',harmonization_document='doc',weight_basis='weight')]).to_csv(p,index=False)
    with pytest.raises(ValueError,match='source_id'):decennial_from_aggregates(p)

def test_decennial_valid_aggregate(tmp_path):
    p=tmp_path/'dec.csv'
    pd.DataFrame([dict(year=1990,geography='Maine',age_group='25-34',household_group='one_person',earner_group='all',weighted_burdened=2,weighted_eligible=4,sample_n=4,source_id='IPUMS_1990_EXTRACT',harmonization_document='method.md',weight_basis='HHWT')]).to_csv(p,index=False)
    d=decennial_from_aggregates(p)
    assert d.iloc[0].estimate==.5
    assert d.iloc[0].comparability_status=='not_yet_cross_survey_harmonized'

def test_decennial_rejects_invalid_denominator(tmp_path):
    p=tmp_path/'dec.csv'
    pd.DataFrame([dict(year=2000,geography='Maine',age_group='all',household_group='all',earner_group='all',weighted_burdened=5,weighted_eligible=4,sample_n=4,source_id='extract',harmonization_document='doc',weight_basis='HHWT')]).to_csv(p,index=False)
    with pytest.raises(ValueError,match='Invalid decennial'):decennial_from_aggregates(p)
