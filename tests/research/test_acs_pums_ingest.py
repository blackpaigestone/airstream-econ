import pandas as pd
import pytest
from src.research.acs_pums_ingest import prepare_pums
from src.research.household_microdata import validate_households, summarize_renter_burden


def inputs(tmp_path):
    h=tmp_path/'h.csv'; p=tmp_path/'p.csv'
    pd.DataFrame([
        dict(SERIALNO='0001',ST='23',NP=1,TEN=3,HINCP=24000,GRNTP=800,WGTP=10),
        dict(SERIALNO='0002',ST='23',NP=2,TEN=4,HINCP=60000,GRNTP=1500,WGTP=20),
        dict(SERIALNO='0003',ST='23',NP=1,TEN=1,HINCP=100000,GRNTP=-1,WGTP=5),
    ]).to_csv(h,index=False)
    pd.DataFrame([
        dict(SERIALNO='0001',SPORDER=1,RELSHIPP=20,AGEP=29,WAGP=24000,SEMP=0),
        dict(SERIALNO='0002',SPORDER=1,RELSHIPP=20,AGEP=35,WAGP=40000,SEMP=0),
        dict(SERIALNO='0002',SPORDER=2,RELSHIPP=34,AGEP=30,WAGP=20000,SEMP=0),
        dict(SERIALNO='0003',SPORDER=1,RELSHIPP=20,AGEP=52,WAGP=100000,SEMP=0),
    ]).to_csv(p,index=False)
    return h,p


def test_prepares_and_validates(tmp_path):
    h,p=inputs(tmp_path)
    d,a=prepare_pums(h,p,2024,'23')
    assert len(d)==2
    assert d.household_id.tolist()==['0001','0002']
    assert d.householder_age.tolist()==[29,35]
    assert d.earner_count.tolist()==[1,2]
    assert d.adult_count.tolist()==[1,2]
    assert a['renter_households']==2
    assert len(validate_households(d))==2
    result=summarize_renter_burden(d,min_n=1)
    assert len(result)==2


def test_rejects_incomplete_person_file(tmp_path):
    h,p=inputs(tmp_path)
    df=pd.read_csv(p,dtype={'SERIALNO':str})
    df=df.iloc[:-1]
    df.to_csv(p,index=False)
    with pytest.raises(ValueError,match='missing people or reference person'):
        prepare_pums(h,p,2024,'23')


def test_rejects_state_mismatch(tmp_path):
    h,p=inputs(tmp_path)
    with pytest.raises(ValueError,match='other states'):
        prepare_pums(h,p,2024,'36')


def test_2020_not_available(tmp_path):
    h,p=inputs(tmp_path)
    with pytest.raises(ValueError,match='2020 unavailable'):
        prepare_pums(h,p,2020,'23')


def test_rejects_missing_required_field(tmp_path):
    h,p=inputs(tmp_path)
    df=pd.read_csv(h,dtype={'SERIALNO':str,'ST':str}).drop(columns=['GRNTP'])
    df.to_csv(h,index=False)
    with pytest.raises(ValueError,match='missing required PUMS fields'):
        prepare_pums(h,p,2024,'23')
