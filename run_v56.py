"""Run V5.6 provisional descriptive New England PUMS research."""
import argparse
from pathlib import Path
import pandas as pd
from src.research.new_england_v56 import load_states, stratify, analyze


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--year',type=int,default=2024)
    parser.add_argument('--prepared-root',default='data/external/pums_prepared')
    parser.add_argument('--raw-root',default='data/raw/pums')
    parser.add_argument('--output-root',default='data/derived/v56')
    args=parser.parse_args()
    df,audit=load_states(args.year,args.prepared_root,args.raw_root)
    prepared=stratify(df)
    results=analyze(prepared)
    if results.empty:raise RuntimeError('No complete six-state comparison strata')
    out=Path(args.output_root)/str(args.year)
    out.mkdir(parents=True,exist_ok=True)
    audit.to_csv(out/'extraction_audit.csv',index=False)
    results.to_csv(out/'descriptive_strata.csv',index=False)
    denominator=prepared.groupby('state_fips',sort=True).agg(prepared_rows=('household_id','size'),valid_income_rent_rows=('valid_denominator','sum')).reset_index()
    denominator['excluded_from_ratio']=denominator.prepared_rows-denominator.valid_income_rent_rows
    denominator.to_csv(out/'denominator_audit.csv',index=False)
    summary=results[(results.age_group=='all')&(results.household_group=='all')&(results.earner_group=='all')]
    print('V5.6 provisional 2024 New England descriptive analysis (NO uncertainty intervals; NO bulk-file certification)')
    print(summary[['threshold','geography','rate','sample_n']].to_string(index=False,formatters={'rate':lambda x:f'{x:.1%}'}))
    print('\nFiles saved to',out)
    print('No inference about statistical significance or historical change is supported yet.')

if __name__=='__main__':main()
