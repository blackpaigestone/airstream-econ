"""Scenario functions; not estimates from historical household microdata."""
from src.model import monthly_payment, loan_balance

def flexibility_cost(monthly_essentials, runway_months, transition_reserve, annual_net_income):
    if min(monthly_essentials,runway_months,transition_reserve,annual_net_income)<0 or annual_net_income==0: raise ValueError('Invalid inputs')
    required=monthly_essentials*runway_months+transition_reserve
    return dict(required=required,income_share=required/annual_net_income,months_income=required/(annual_net_income/12))

def income_gain_value(annual_net_income,essential_share,annual_gain,target):
    if annual_net_income<=0 or not 0<=essential_share<=1 or annual_gain<0 or target<0: raise ValueError('Invalid inputs')
    before=annual_net_income*(1-essential_share)
    after=before+annual_gain
    return dict(before=before,after=after,years_before=target/before if before>0 else float('inf'),years_after=target/after if after>0 else float('inf'))

def opportunity_value(benefit,transition_cost):
    return benefit-transition_cost

def five_year_outcome(monthly_net_job,monthly_net_business,monthly_operating,starting_liquid, resale_pct,price=155000,rate=8,term=15,months=60,sale_cost_pct=5):
    if monthly_operating<0 or starting_liquid<0 or not 0<=resale_pct<=150: raise ValueError('Invalid inputs')
    payment=monthly_payment(price,rate,term)
    balance=loan_balance(price,rate,term,months)
    monthly_saving=monthly_net_job+monthly_net_business-monthly_operating-payment
    cash_before_sale=starting_liquid+months*monthly_saving
    net_sale_proceeds=price*resale_pct/100*(1-sale_cost_pct/100)-balance
    return dict(payment=payment,loan_balance=balance,monthly_saving=monthly_saving,cash_before_sale=cash_before_sale,net_sale_proceeds=net_sale_proceeds,liquid_after_sale=cash_before_sale+net_sale_proceeds)
