import pandas as pd
import pytest
from src.research.new_england_v56 import STATES, stratify, analyze, load_states


def fixture_data():
    rows=[]
    for state in STATES:
        for i, income in enumerate((12000,48000)):
            rows.append({'state_fips':state,'householder_age':30,'household_size':1+i,'adult_count':1+i,'earner_count':i,
                         'household_income_annual':income,'gross_rent_monthly':600,'household_weight':1+i,
                         'household_id':str(i)})
    return stratify(pd.DataFrame(rows))


def test_pooled_and_mean_separate():
    result=analyze(fixture_data())
    base=result[(result.age_group=='all')&(result.household_group=='all')&(result.earner_group=='all')&(result.threshold==.3)]
    assert len(base)==12
    assert base.loc[base.geography=='Maine','rate'].iloc[0]==pytest.approx(1/3)
    assert base.loc[base.geography=='New England pooled','rate'].iloc[0]==pytest.approx(1/3)


def test_no_zero_income_in_denominator():
    data=fixture_data()
    data.loc[data.index[0],'household_income_annual']=0
    data=stratify(data)
    assert not data.loc[0,'valid_denominator']


def test_missing_state_fails_closed(tmp_path):
    with pytest.raises(FileNotFoundError):load_states(2024,root=tmp_path)


def test_2020_not_supported(tmp_path):
    with pytest.raises(ValueError):load_states(2020,root=tmp_path)
