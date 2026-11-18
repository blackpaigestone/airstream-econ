import pandas as pd
import pytest
from src.research.historical_bulk_v581 import prepare,save

def fixture(tmp_path,rel='RELP',gq=False):
    h=pd.DataFrame([{'SERIALNO':'a','ST':'23','NP':1,'TEN':3,'HINCP':24000,'GRNTP':800,'WGTP':2}])
    p=pd.DataFrame([{'SERIALNO':'a','SPORDER':1,'AGEP':30,'WAGP':24000,'SEMP':0,rel:0 if rel=='RELP' else 20}])
    if gq:
        h.loc[len(h)]={'SERIALNO':'g','ST':'23','NP':1,'TEN':0,'HINCP':0,'GRNTP':0,'WGTP':1}
        p.loc[len(p)]={'SERIALNO':'g','SPORDER':1,'AGEP':20,'WAGP':0,'SEMP':0,rel:16 if rel=='RELP' else 37}
    hp,pp=tmp_path/'h.csv',tmp_path/'p.csv';h.to_csv(hp,index=False);p.to_csv(pp,index=False)
    return hp,pp

def test_relp_2015(tmp_path):
    h,p=fixture(tmp_path)
    out,a=prepare(h,p,2015,'23')
    assert len(out)==1 and out.householder_age.iloc[0]==30 and a['relationship_variable']=='RELP'

def test_relshipp_2019(tmp_path):
    h,p=fixture(tmp_path,'RELSHIPP')
    out,a=prepare(h,p,2019,'23')
    assert len(out)==1 and a['reference_person_code']==20

def test_group_quarters_excluded(tmp_path):
    h,p=fixture(tmp_path,gq=True)
    out,a=prepare(h,p,2018,'23')
    assert len(out)==1 and a['group_quarters_excluded']==1

def test_missing_reference_fails(tmp_path):
    h,p=fixture(tmp_path)
    df=pd.read_csv(p);df['RELP']=1;df.to_csv(p,index=False)
    with pytest.raises(ValueError,match='reference person'):prepare(h,p,2018,'23')

def test_mismatch_fails(tmp_path):
    h,p=fixture(tmp_path)
    df=pd.read_csv(h);df['NP']=2;df.to_csv(h,index=False)
    with pytest.raises(ValueError,match='NP count mismatch'):prepare(h,p,2018,'23')

def test_no_overwrite(tmp_path):
    h,p=fixture(tmp_path);out,a=prepare(h,p,2015,'23')
    save(out,a,tmp_path/'prepared')
    with pytest.raises(FileExistsError):save(out,a,tmp_path/'prepared')

def test_unsupported_year(tmp_path):
    h,p=fixture(tmp_path)
    with pytest.raises(ValueError):prepare(h,p,2000,'23')
