"""Import one state-year of locally downloaded, official ACS PUMS bulk CSVs."""
import argparse
from src.research.historical_bulk_v581 import prepare,save

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--year',type=int,required=True)
    p.add_argument('--state',required=True,help='Two-digit state FIPS, e.g. 23 for Maine')
    p.add_argument('--households',required=True,help='Unmodified ACS1 housing PUMS CSV')
    p.add_argument('--persons',required=True,help='Unmodified ACS1 person PUMS CSV')
    p.add_argument('--relationship',choices=['RELP','RELSHIPP'])
    p.add_argument('--out',default='data/external/pums_prepared')
    a=p.parse_args()
    frame,audit=prepare(a.households,a.persons,a.year,a.state,relationship=a.relationship)
    dest=save(frame,audit,a.out)
    print(f'SAVED {dest} ({len(frame)} prepared renters); relationship={audit["relationship_variable"]}')
    print('Source completeness and survey-design uncertainty NOT certified.')
if __name__=='__main__':main()
