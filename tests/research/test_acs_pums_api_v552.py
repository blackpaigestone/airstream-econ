"""Live-response-shaped tests for Census's automatically appended filter fields."""
import pytest
from src.research.acs_pums_api import retrieve_state_pums

class Response:
    def __init__(self, value): self.value = value
    def raise_for_status(self): pass
    def json(self): return self.value

class Session:
    def __init__(self, responses): self.responses = iter(responses); self.params = []
    def get(self, url, params, timeout):
        self.params.append(params)
        assert 'RT' not in params['get'].split(',')
        assert params['RT'] in ('H', 'P')
        return Response(next(self.responses))

H = [['SERIALNO','NP','TEN','HINCP','GRNTP','WGTP','RT','state'],
     ['A','2','3','40000','1100','100','H','23']]
P = [['SERIALNO','SPORDER','RELSHIPP','AGEP','WAGP','SEMP','RT','state'],
     ['A','1','20','29','40000','0','P','23'],
     ['A','2','34','28','20000','0','P','23']]

def test_live_shaped_headers_are_unique_and_join():
    h,p,meta = retrieve_state_pums(2024,23,key='TEST_KEY',session=Session([H,P]))
    assert list(h.columns) == ['SERIALNO','ST','NP','TEN','HINCP','GRNTP','WGTP']
    assert list(p.columns) == ['SERIALNO','SPORDER','RELSHIPP','AGEP','WAGP','SEMP']
    assert len(h)==1 and len(p)==2 and meta['persons']==2

def test_missing_person_record_fails_closed():
    with pytest.raises(RuntimeError, match='counts do not match'):
        retrieve_state_pums(2024,23,key='TEST_KEY',session=Session([H,P[:2]]))

def test_duplicate_person_record_fails_closed():
    with pytest.raises(RuntimeError, match='Duplicate person'):
        retrieve_state_pums(2024,23,key='TEST_KEY',session=Session([H,P+[P[1]]]))

def test_missing_filter_column_fails_closed():
    broken = [['SERIALNO','NP','TEN','HINCP','GRNTP','WGTP','state'],
              ['A','2','3','40000','1100','100','23']]
    with pytest.raises(RuntimeError, match='missing columns'):
        retrieve_state_pums(2024,23,key='TEST_KEY',session=Session([broken,P]))
