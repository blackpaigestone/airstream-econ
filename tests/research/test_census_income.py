import json
import pandas as pd
import pytest
from src.research.census_income import (
    INCOME_BANDS, identify_income_variables, parse_income,
    validate_income_panel, real_income_index, refresh_income,
)

# Mirrors the ACTUAL 2024 Census B19049 metadata categories.
def fixture(year=2010):
    labels = {
        'B19049_001E': 'Estimate!!Median household income in the past 12 months (in 2024 inflation-adjusted dollars) --!!Total:',
        'B19049_002E': 'Estimate!!Median household income in the past 12 months (in 2024 inflation-adjusted dollars) --!!Total:!!Householder under 25 years',
        'B19049_003E': 'Estimate!!Median household income in the past 12 months (in 2024 inflation-adjusted dollars) --!!Total:!!Householder 25 to 44 years',
        'B19049_004E': 'Estimate!!Median household income in the past 12 months (in 2024 inflation-adjusted dollars) --!!Total:!!Householder 45 to 64 years',
        'B19049_005E': 'Estimate!!Median household income in the past 12 months (in 2024 inflation-adjusted dollars) --!!Total:!!Householder 65 years and over',
    }
    metadata={'variables':{k:{'label':v} for k,v in labels.items()}}
    payload=[['NAME',*labels,'us'],['United States','50000','30000','60000','75000','42000','1']]
    return metadata,payload

def test_mapping_actual_acs_labels():
    metadata,_=fixture()
    assert identify_income_variables(metadata)=={
        'Under 25':'B19049_002E','25–44':'B19049_003E',
        '45–64':'B19049_004E','65+':'B19049_005E',
    }

def test_parse_real_published_bands():
    m,p=fixture()
    d=validate_income_panel(pd.DataFrame(parse_income(m,p,2010)))
    assert len(d)==4
    assert set(d.age_band)==set(INCOME_BANDS)
    assert d.loc[d.age_band=='25–44','median_household_income'].iloc[0]==60000

def test_no_narrow_age_band_inference():
    m,p=fixture()
    d=pd.DataFrame(parse_income(m,p,2010))
    assert not any(age in set(d.age_band) for age in ['25–34','35–44','45–54'])

def test_missing_mapping():
    m,p=fixture();m['variables'].pop('B19049_003E')
    with pytest.raises(ValueError,match='incomplete'):identify_income_variables(m)

def test_invalid_income():
    m,p=fixture();p[1][3]='-666666666'
    with pytest.raises(ValueError,match='Invalid ACS'):parse_income(m,p,2010)

def test_duplicate():
    m,p=fixture();d=pd.DataFrame(parse_income(m,p,2010))
    with pytest.raises(ValueError,match='Duplicate'):validate_income_panel(pd.concat([d,d]))

def test_real_index_same_real_income(tmp_path):
    m,p=fixture();d=pd.DataFrame(parse_income(m,p,2010))
    d2=d.copy();d2['year']=2011;d2['median_household_income']*=2
    cpi=tmp_path/'cpi.csv'
    pd.DataFrame({'date':['2010-01-01','2011-01-01'],'value':[100,200]}).to_csv(cpi,index=False)
    out=real_income_index(pd.concat([d,d2]),cpi)
    assert all(abs(out.real_income_index-100)<1e-8)

def test_real_index_not_double_deflated(tmp_path):
    m,p=fixture();d=pd.DataFrame(parse_income(m,p,2010))
    d2=d.copy();d2['year']=2011;d2['median_household_income']*=1.1
    cpi=tmp_path/'cpi.csv'
    pd.DataFrame({'date':['2010-01-01','2011-01-01'],'value':[100,110]}).to_csv(cpi,index=False)
    out=real_income_index(pd.concat([d,d2]),cpi)
    assert all(abs(out.real_income_index-100)<1e-8)

def test_missing_base(tmp_path):
    m,p=fixture();d=pd.DataFrame(parse_income(m,p,2011))
    cpi=tmp_path/'cpi.csv'
    pd.DataFrame({'date':['2011-01-01'],'value':[100]}).to_csv(cpi,index=False)
    with pytest.raises(ValueError,match='baseline'):real_income_index(d,cpi)

def test_refresh_failure(tmp_path):
    m,p=fixture()
    def fetch(y):
        if y==2020:raise ValueError('not released')
        return parse_income(m,p,y)
    d,r=refresh_income(2019,2021,tmp_path/'income.csv',tmp_path/'provenance.json',fetch)
    assert len(d)==8 and r['years_retrieved']==[2019,2021]
    provenance=json.loads((tmp_path/'provenance.json').read_text())
    assert '25–44' in provenance['warning']
