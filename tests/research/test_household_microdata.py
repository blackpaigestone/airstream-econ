import pandas as pd
import pytest
from src.research.household_microdata import validate_households, summarize_renter_burden

def fixture():
    return pd.DataFrame([{'source_id':'TEST','source_url':'https://example.org/source',
        'year':2022,'household_id':str(i),'householder_age':30,'household_size':1 if i<35 else 2,
        'adult_count':1 if i<35 else 2,'earner_count':1,'tenure':'renter',
        'household_income_annual':24000,'gross_rent_monthly':1000 if i%2 else 300,
        'household_weight':2 if i%3 else 1} for i in range(80)])

def test_weighted_shares_and_strata():
    d=summarize_renter_burden(fixture())
    assert len(d)==2
    assert set(d.household_type)=={'one-person','multi-person'}
    assert d.burden_30_share.between(0,1).all()
    assert (d.burden_50_share<=d.burden_30_share).all()

def test_no_duplicate_household():
    d=fixture();d.loc[1,'household_id']='0'
    with pytest.raises(ValueError,match='Duplicate'):validate_households(d)

def test_invalid_weights_rejected():
    d=fixture();d.loc[0,'household_weight']=0
    with pytest.raises(ValueError,match='Weights'):validate_households(d)

def test_missing_required_column():
    with pytest.raises(ValueError,match='Missing'):validate_households(fixture().drop(columns='adult_count'))

def test_low_n_suppressed():
    assert summarize_renter_burden(fixture().head(10)).empty

def test_nonpositive_income_excluded():
    d=fixture();d.loc[0,'household_income_annual']=0
    out=summarize_renter_burden(d)
    assert int(out.n_excluded.sum())==1

def test_household_size_not_earner_count():
    d=fixture();d.loc[d.household_size==2,'earner_count']=0
    assert len(summarize_renter_burden(d))==2
