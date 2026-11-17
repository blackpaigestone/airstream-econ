from src.model import monthly_payment,loan_balance,scenario

def test_zero_rate():assert monthly_payment(120000,0,10)==1000

def test_paid_off():assert loan_balance(120000,8,10,120)==0

def test_baseline():
    x=scenario()
    assert 1400<x['payment']<1600
    assert abs(x['net_cost']-(x['cash_out']+x['balance']-x['resale']))<.01

def test_invalid():
    try: monthly_payment(-1,8,15)
    except ValueError: pass
    else: raise AssertionError('Negative principal accepted')
