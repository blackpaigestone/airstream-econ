import pandas as pd
import pytest
from src.research.households import household_budget, readiness_budget, readiness_by_age


def test_shared_fixed_costs_reduce_per_adult_cost():
    one = household_budget(1,1,2000,600,3500)
    two = household_budget(2,1,2000,600,3500)
    assert one['per_adult_cost'] == 2600
    assert two['per_adult_cost'] == 1600
    assert two['income'] == one['income']


def test_multiple_earners_are_separate_from_cost_sharing():
    one = household_budget(2,1,2000,600,3500)
    two = household_budget(2,2,2000,600,3500)
    assert one['expenses'] == two['expenses']
    assert two['income'] == 2*one['income']


def test_dependents_costs_and_equivalence():
    b = household_budget(2,2,2000,600,3500,1,400)
    assert b['expenses'] == 3600
    assert b['total_people'] == 3
    assert b['equivalized_income'] == pytest.approx(7000/(3**.5))


@pytest.mark.parametrize('args',[(0,0,100,100,100), (2,3,100,100,100), (1,1,-1,100,100)])
def test_bad_households(args):
    with pytest.raises(ValueError): household_budget(*args)


def test_readiness_requires_reserve_and_savings():
    b = readiness_budget(4000,3000,9000,3,2000,.1)
    assert b['cashflow_positive'] and b['savings_ready']
    assert not b['reserve_ready'] and not b['fully_ready']
    assert b['months_to_reserve'] == 2


def test_readiness_no_positive_surplus():
    b = readiness_budget(2000,2500,0)
    assert b['months_to_reserve'] is None
    assert not b['fully_ready']


def test_microdata_age_grouping_and_no_synthetic_rows():
    d = pd.DataFrame([dict(year=1990,age=25,household_id='a',monthly_income=4000,monthly_essentials=2000,liquid_savings=8000,adults=1,dependents=0),
                      dict(year=1990,age=25,household_id='b',monthly_income=2000,monthly_essentials=2000,liquid_savings=0,adults=1,dependents=0)])
    r = readiness_by_age(d)
    assert len(r) == 1
    assert r.loc[0,'readiness_share'] == .5
    assert r.loc[0,'households'] == 2


def test_microdata_duplicates_rejected():
    d = pd.DataFrame([dict(year=1990,age=25,household_id='a',monthly_income=4000,monthly_essentials=2000,liquid_savings=8000,adults=1,dependents=0)]*2)
    with pytest.raises(ValueError,match='Duplicate'): readiness_by_age(d)
