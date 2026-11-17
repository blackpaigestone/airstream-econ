"""Descriptive 2024 state and New England renter-burden point estimates.
Not survey-design confidence intervals. Excludes missing/nonpositive income.
"""
import argparse
from pathlib import Path
import pandas as pd

STATES={'09':'Connecticut','23':'Maine','25':'Massachusetts','33':'New Hampshire','44':'Rhode Island','50':'Vermont'}

def summarize(frames,threshold=.30):
    stats={}
    for state,df in frames.items():
        income=pd.to_numeric(df['household_income_annual'],errors='coerce')
        rent=pd.to_numeric(df['gross_rent_monthly'],errors='coerce')
        weight=pd.to_numeric(df['household_weight'],errors='coerce')
        valid=(income>0)&rent.ge(0)&weight.gt(0)&income.notna()&rent.notna()&weight.notna()
        if not valid.any():raise ValueError(f'No valid denominator in state {state}')
        burden=12*rent[valid]/income[valid]>=threshold
        stats[state]={'weighted_n':float(weight[valid].sum()),'weighted_burdened':float(weight[valid][burden].sum()),'rate':float(weight[valid][burden].sum()/weight[valid].sum()),'unweighted_n':int(valid.sum())}
    def pooled(keys):return sum(stats[s]['weighted_burdened'] for s in keys)/sum(stats[s]['weighted_n'] for s in keys)
    others=[s for s in STATES if s!='23']
    rates=pd.Series({s:stats[s]['rate'] for s in STATES})
    return stats,{'maine':stats['23']['rate'],'ne_pooled':pooled(STATES),'ne_state_mean':float(rates.mean()),'ne_state_median':float(rates.median()),'other_five_pooled':pooled(others),'other_five_state_mean':float(rates[others].mean()),'other_five_state_median':float(rates[others].median())}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--year',type=int,default=2024);ap.add_argument('--root',default='data/external/pums_prepared');ap.add_argument('--threshold',type=float,default=.30);a=ap.parse_args()
    if not 0<a.threshold<=1:ap.error('threshold must be in (0,1]')
    frames={}
    for state in STATES:
        path=Path(a.root)/str(a.year)/f'state_{state}.csv'
        if not path.is_file():raise FileNotFoundError(f'Missing {path}; do not calculate regional benchmark from incomplete states')
        frames[state]=pd.read_csv(path)
        if frames[state]['year'].nunique()!=1 or int(frames[state]['year'].iloc[0])!=a.year:raise ValueError(f'Year mismatch: {path}')
        if not frames[state]['source_id'].astype(str).eq(f'ACS1_PUMS_{a.year}_ST{state}').all():raise ValueError(f'Source mismatch: {path}')
    stats,benchmark=summarize(frames,a.threshold)
    print('Provisional weighted point estimates; not externally certified; no uncertainty intervals.')
    for s in STATES:print(f'{STATES[s]:16} {stats[s]["rate"]:.1%} (sample n={stats[s]["unweighted_n"]})')
    print('\nBenchmarks:')
    for k,v in benchmark.items():print(f'{k:26} {v:.1%}')

if __name__=='__main__':main()
