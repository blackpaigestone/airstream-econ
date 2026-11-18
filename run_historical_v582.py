"""Command-line runner for V5.8.2 historical ACS PUMS ingestion."""
import argparse
from pathlib import Path
from research.historical_pipeline_v582 import STATES, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--years', nargs='+', type=int, default=[2015,2016,2017,2018])
    parser.add_argument('--states', nargs='+', default=list(STATES),
                        help='Two-digit state FIPS; default all six New England states')
    parser.add_argument('--raw-root', type=Path, default=Path('data/raw/pums'))
    parser.add_argument('--prepared-root', type=Path, default=Path('data/external/pums_prepared'))
    parser.add_argument('--audit-root', type=Path, default=Path('data/derived/v582'))
    parser.add_argument('--offline', action='store_true', help='Never access network; use existing archives')
    parser.add_argument('--download-only', action='store_true')
    args = parser.parse_args()
    result = run(years=args.years, states=[s.zfill(2) for s in args.states],
                 raw_root=args.raw_root, prepared_root=args.prepared_root,
                 audit_root=args.audit_root, offline=args.offline,
                 download_only=args.download_only)
    print('SUMMARY', result['counts'])
    print('AUDIT', args.audit_root / 'v582_run.json')
    if result['counts']['failed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
