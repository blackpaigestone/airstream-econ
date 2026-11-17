"""Refresh official US ACS 1-year national renter housing-cost burden."""
import argparse
from src.research.census_rent_burden import refresh_burden

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=2010)
    parser.add_argument('--end', type=int, default=2024)
    args = parser.parse_args()
    data, provenance = refresh_burden(args.start, args.end)
    print(f"Retrieved {len(data)} national year observations: {sorted(data.year.tolist())}")
    print(f"Skipped/failed years: {provenance['failures']}")
    print('Saved data/external/census_acs_rent_burden.csv and provenance JSON')
