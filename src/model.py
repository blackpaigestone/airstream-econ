"""Transparent nominal-dollar ownership calculations. No appreciation assumed."""
def monthly_payment(principal, annual_rate, years):
    if principal < 0 or years <= 0 or annual_rate < 0: raise ValueError('Invalid financing input')
    n = int(years * 12)
    r = annual_rate / 1200
    return principal / n if r == 0 else principal * r / (1 - (1+r)**(-n))

def loan_balance(principal, annual_rate, years, months):
    payment = monthly_payment(principal, annual_rate, years)
    r = annual_rate / 1200
    if months >= years*12: return 0.
    if r == 0: return max(0., principal-payment*months)
    return max(0., principal*(1+r)**months-payment*((1+r)**months-1)/r)

def scenario(price=155000, rate=8, years=15, months=36, campsite=600, diesel=350, other=550, resale_pct=70, down=0, upfront=0, rent=3000):
    principal=price-down
    pmt=monthly_payment(principal,rate,years)
    bal=loan_balance(principal,rate,years,months)
    resale=price*resale_pct/100
    operations=months*(campsite+diesel+other)
    cash_out=down+upfront+months*pmt+operations
    net_cost=cash_out+bal-resale
    return dict(payment=pmt, monthly=pmt+campsite+diesel+other, balance=bal, resale=resale,
                cash_out=cash_out, net_cost=net_cost, rent_cost=rent*months,
                monthly_cash_difference=rent-(pmt+campsite+diesel+other),
                net_difference=rent*months-net_cost)
