"""Build a provisional historical New England panel, 2021–2024."""
import argparse
from pathlib import Path
from src.research.historical_ne_v57 import historical, compare_endpoints


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--years', nargs='+', type=int, default=[2021, 2022, 2023, 2024])
    parser.add_argument('--prepared-root', default='data/external/pums_prepared')
    parser.add_argument('--raw-root', default='data/raw/pums')
    parser.add_argument('--output-root', default='data/derived/v57')
    args = parser.parse_args()
    results, audits = historical(args.years, args.prepared_root, args.raw_root)
    out = Path(args.output_root)
    out.mkdir(parents=True, exist_ok=True)
    results.to_csv(out/'historical_strata.csv', index=False)
    audits.to_csv(out/'historical_extraction_audit.csv', index=False)
    young = results.loc[results.age_group.eq('25-34') & results.household_group.eq('one_person') & results.earner_group.eq('all') & results.threshold.eq(.30)]
    young.to_csv(out/'young_adults_living_alone.csv', index=False)
    print('V5.7: provisional weighted estimates; NO survey-design intervals or bulk-file certification')
    print('Years:', sorted(results.year.unique().tolist()))
    for geography in ('Maine', 'Other five pooled'):
        subset = young.loc[young.geography.eq(geography)]
        print(f'\n{geography}: age 25–34, one-person renter households, rent burden >=30%')
        for r in subset.itertuples():
            print(f'  {r.year}: {r.rate:.1%} (sample n={r.sample_n if r.sample_n==r.sample_n else "pooled"})')
    if len(set(args.years)) > 1:
        comparison = compare_endpoints(results, min(args.years), max(args.years))
        comparison.to_csv(out/'endpoint_changes.csv', index=False)
        print('\nEndpoint differences (percentage points; descriptive only):')
        print(comparison.loc[comparison.geography.isin(['Maine','Other five pooled'])].to_string(index=False))
    print('\nOutputs:', out)
    print('Do not infer statistical significance, causation, or same-household changes.')


if __name__ == '__main__':
    main()
