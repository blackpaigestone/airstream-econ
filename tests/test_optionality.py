import pytest
from src.optionality import flexibility_cost,income_gain_value,opportunity_value,five_year_outcome

def test_flexibility_basket():
    x=flexibility_cost(3000,6,10000,75000)
    assert x['required']==28000
    assert x['income_share']==pytest.approx(28000/75000)

def test_income_gain():
    x=income_gain_value(75000,.8,5000,60000)
    assert x['before']==pytest.approx(15000)
    assert x['years_before']==pytest.approx(4)
    assert x['years_after']==pytest.approx(3)

def test_opportunity():
    assert opportunity_value(25000,5000)-opportunity_value(25000,15000)==10000

def test_five_year_reconciliation():
    x=five_year_outcome(6500,0,1500,5000,60)
    assert x['liquid_after_sale']==pytest.approx(x['cash_before_sale']+x['net_sale_proceeds'])
    assert x['loan_balance']>0

def test_negative_business_scenario():
    a=five_year_outcome(6500,0,1500,5000,60)
    b=five_year_outcome(6500,-500,1500,5000,60)
    assert a['liquid_after_sale']-b['liquid_after_sale']==pytest.approx(30000)
