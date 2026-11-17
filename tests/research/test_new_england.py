import pandas as pd
from compare_new_england import summarize

def test_pooled_differs_from_state_mean():
    frames={}
    for s in ('09','23','25','33','44','50'):
        frames[s]=pd.DataFrame({'household_income_annual':[12000], 'gross_rent_monthly':[500 if s=='23' else 100], 'household_weight':[100 if s=='23' else 1]})
    stats,b=summarize(frames)
    assert b['maine']==1
    assert b['other_five_pooled']==0
    assert b['ne_pooled']>b['ne_state_mean']
    assert b['ne_state_median']==0
