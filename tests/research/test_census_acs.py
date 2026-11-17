import json
import pandas as pd
import pytest
from src.research.census_acs import identify_variables, parse_response, validate_panel, refresh, load_panel


def fixture():
    variables={}
    counts={}
    i=1
    for tenure in ('Owner occupied','Renter occupied'):
        for age in ('25 to 34 years','35 to 44 years','45 to 54 years'):
            key=f'B25007_{i:03d}E'
            variables[key]={'label':f'Estimate!!Total:!!{tenure}:!!Householder {age}'}
            counts[key]=str(i*100)
            i+=1
    metadata={'variables':variables}
    payload=[['NAME',*counts,'us'],['United States',*counts.values(),'1']]
    return metadata,payload


def test_metadata_is_label_based():
    m,p=fixture()
    found=identify_variables(m)
    assert len(found)==6
    assert found[('25–34','owner')]=='B25007_001E'
    assert found[('25–34','renter')]=='B25007_004E'


def test_parse_observed_counts_and_share():
    m,p=fixture()
    d=pd.DataFrame(parse_response(m,p,2022))
    r=d[d.age_band=='25–34'].iloc[0]
    assert r.owner_households==100
    assert r.renter_households==400
    assert r.renter_share==0.8
    assert len(validate_panel(d))==3


def test_incomplete_metadata_rejected():
    m,p=fixture()
    del m['variables']['B25007_006E']
    with pytest.raises(ValueError,match='incomplete'):
        identify_variables(m)


def test_invalid_count_rejected():
    m,p=fixture()
    p[1][1]='-666666666'
    with pytest.raises(ValueError,match='Invalid ACS count'):
        parse_response(m,p,2022)


def test_duplicate_cell_rejected():
    m,p=fixture()
    d=pd.DataFrame(parse_response(m,p,2022))
    with pytest.raises(ValueError,match='Duplicate'):
        validate_panel(pd.concat([d,d.iloc[[0]]]))


def test_refresh_records_failed_year_and_provenance(tmp_path):
    m,p=fixture()
    def fetch(year):
        if year==2020:
            raise ValueError('Unavailable')
        return parse_response(m,p,year)
    dest=tmp_path/'acs.csv'
    prov=tmp_path/'provenance.json'
    d, record=refresh(2019,2021,dest,prov,fetch)
    assert len(d)==6
    assert record['years_retrieved']==[2019,2021]
    assert record['failures'][0]['year']==2020
    assert len(load_panel(dest))==6
    assert json.loads(prov.read_text())['years_retrieved']==[2019,2021]


def test_refresh_no_data_does_not_write(tmp_path):
    dest=tmp_path/'acs.csv'
    with pytest.raises(RuntimeError,match='No ACS years'):
        refresh(2020,2020,dest,tmp_path/'p.json',lambda year: (_ for _ in ()).throw(ValueError('missing')))
    assert not dest.exists()
