"""Build the 1990–2024 source-aware panel from real available inputs."""
import argparse
from src.research.long_run_v58 import build,write_outputs

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--v57',default='data/derived/v57/historical_strata.csv')
    p.add_argument('--decennial-aggregates',default=None,help='OPTIONAL independently harmonized 1990/2000 weighted cells')
    p.add_argument('--out',default='data/derived/v58')
    a=p.parse_args()
    panel=build(a.v57,a.decennial_aggregates)
    audit=write_outputs(a.out,panel)
    print('V5.8 long-run research spine built:',a.out)
    print('Observed years:',audit['observed_years'])
    print('Rows:',audit['panel_rows'])
    print('Historical coverage is not equivalent to a continuous 1990–2024 series.')
    print('No 1990/2000 estimates are fabricated; provide verified harmonized aggregates to add them.')
if __name__=='__main__':main()
