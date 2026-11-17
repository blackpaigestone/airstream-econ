"""Download documented, observed ACS national tenure by age of householder."""
import argparse
from src.research.census_acs import refresh

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--start',type=int,default=2010)
    parser.add_argument('--end',type=int,default=2024)
    args=parser.parse_args()
    data,record=refresh(args.start,args.end)
    print(f'Retrieved {len(record["years_retrieved"])} ACS years; {len(data)} age-year cells.')
    print('Years:',record['years_retrieved'])
    print('Unavailable years:',record['failures'])
    print('Saved data/external/census_acs_tenure_age.csv and provenance JSON')
