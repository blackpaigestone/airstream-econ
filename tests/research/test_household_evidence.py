import pandas as pd
import pytest
from src.research.household_evidence import validate_households,summarize_households,load_evidence


def sample(n=35):
    rows=[]
    for i in range(n):
        rows.append(dict(source_id='TEST_SYNTHETIC',year=1990,household_id=f's{i}',age=29,adults=1,dependents=0,earners=1,tenure='renter',annual_disposable_income=60000,annual_essential_spending=30000,liquid_assets=10000,weight=2))
        rows.append(dict(source_id='TEST_SYNTHETIC',year=1990,household_id=f'h{i}',age=29,adults=2,dependents=0,earners=2,tenure='renter',annual_disposable_income=100000,annual_essential_spending=42000,liquid_assets=12000,weight=1))
    return pd.DataFrame(rows)

def test_weighted_premium_and_readiness():
    out=summarize_households(sample())
    all_=out[out.group=='all households'].iloc[0]
    assert all_.weighted_independent_premium==pytest.approx(30000/21000)
    assert all_.readiness_share==pytest.approx(1)
    assert all_.n==70

def test_weights_change_result():
    d=sample();d.loc[d.adults==1,'liquid_assets']=0
    out=summarize_households(d)
    a=out[out.group=='all households'].iloc[0]
    assert a.readiness_share==pytest.approx(1/3)

def test_no_small_cells():
    assert summarize_households(sample(2)).empty

def test_bad_columns():
    with pytest.raises(ValueError,match='Missing V5'):
        validate_households(sample().drop(columns=['weight']))

def test_invalid_weights():
    d=sample();d.loc[0,'weight']=0
    with pytest.raises(ValueError,match='weights'):
        validate_households(d)

def test_duplicate():
    d=sample();d.loc[1,'household_id']=d.loc[0,'household_id']
    with pytest.raises(ValueError,match='Duplicate'):
        validate_households(d)

def test_no_cross_source_pooling():
    d=sample();other=d.copy();other.source_id='SECOND_SYNTHETIC';other.year=2000
    out=summarize_households(pd.concat([d,other],ignore_index=True))
    assert len(out)==6

def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_evidence(tmp_path/'missing.csv')

def test_age_bands():
    d=sample();d.loc[d.adults==2,'age']=39
    out=summarize_households(d)
    assert set(out.age_band)=={'25–34','35–44'}
    assert out.weighted_independent_premium.isna().all()

def test_negative_expenses():
    d=sample();d.loc[0,'annual_essential_spending']=-1
    with pytest.raises(ValueError,match='nonnegative'):
        validate_households(d)
