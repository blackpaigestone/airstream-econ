import pytest
from src.research.acs_pums_api import retrieve_state_pums

class Response:
    def __init__(self, payload): self.payload = payload
    def raise_for_status(self): pass
    def json(self): return self.payload

class Session:
    def __init__(self, responses): self.responses = iter(responses)
    def get(self, url, params, timeout):
        assert params['key'] == 'TEST_KEY'
        assert params['for'] == 'state:23'
        return Response(next(self.responses))

H = [['SERIALNO','RT','NP','TEN','HINCP','GRNTP','WGTP','state'],
     ['A','H','1','3','40000','1100','100','23'],
     ['B','H','0','0',None,None,'100','23']]
P = [['SERIALNO','RT','SPORDER','RELSHIPP','AGEP','WAGP','SEMP','state'],
     ['A','P','1','20','29','40000','0','23']]

def test_api_housing_person_join_universe():
    h,p,meta=retrieve_state_pums(2024,'23',key='TEST_KEY',session=Session([H,P]))
    assert len(h)==len(p)==1
    assert h.iloc[0]['ST']=='23'
    assert 'B' not in set(h.SERIALNO)
    assert meta['year']==2024

def test_api_refuses_unmatched_person_data():
    with pytest.raises(RuntimeError, match='No matching occupied|lack person records'):
        retrieve_state_pums(2024,'23',key='TEST_KEY',session=Session([H,[P[0]]+[['C','P','1','20','29','0','0','23']]]))

def test_api_refuses_possible_truncation():
    with pytest.raises(RuntimeError, match='completeness'):
        retrieve_state_pums(2024,'23',key='TEST_KEY',session=Session([H,P]),safe_max_rows=2)

def test_api_requires_key(monkeypatch):
    monkeypatch.delenv('CENSUS_API_KEY', raising=False)
    with pytest.raises(RuntimeError, match='CENSUS_API_KEY'):
        retrieve_state_pums(2024,'23')

def test_api_rejects_unharmonized_year():
    with pytest.raises(ValueError, match='2021'):
        retrieve_state_pums(2015,'23',key='TEST_KEY')
