"""V5.7: retrieve 2021–2023 six-state ACS1 PUMS, fail-closed, no overwrites."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from src.research.acs_pums_api import retrieve_state_pums, save_raw
from src.research.acs_pums_ingest import prepare_pums
from src.research.new_england_v56 import STATES


def collect(year, state, raw_root='data/raw/pums', prepared_root='data/external/pums_prepared', safe_max_rows=150000):
    state = str(state).zfill(2)
    if state not in STATES or int(year) not in (2021, 2022, 2023, 2024):
        raise ValueError('Only six New England states and 2021–2024 supported')
    raw = Path(raw_root) / str(year) / f'state_{state}_api'
    out = Path(prepared_root) / str(year) / f'state_{state}.csv'
    if raw.exists() or out.exists():
        return 'EXISTS', None
    h, p, provenance = retrieve_state_pums(year, state, safe_max_rows=safe_max_rows)
    with TemporaryDirectory() as temp:
        hp, pp = Path(temp) / 'h.csv', Path(temp) / 'p.csv'
        h.to_csv(hp, index=False)
        p.to_csv(pp, index=False)
        prepared, audit = prepare_pums(hp, pp, year, state)
    # Validate entire dataset before persisting; preserve the same non-overwrite policy.
    save_raw(h, p, provenance, raw)
    out.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(out, index=False)
    out.with_suffix('.audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    return 'SAVED', len(prepared)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--years', nargs='+', type=int, default=[2021, 2022, 2023])
    parser.add_argument('--states', nargs='+', default=list(STATES))
    parser.add_argument('--safe-max-rows', type=int, default=150000)
    parser.add_argument('--raw-root', default='data/raw/pums')
    parser.add_argument('--prepared-root', default='data/external/pums_prepared')
    args = parser.parse_args()
    if args.safe_max_rows < 1:
        parser.error('--safe-max-rows must be positive')
    failed = []
    for year in args.years:
        for state in args.states:
            state = str(state).zfill(2)
            try:
                status, n = collect(year, state, args.raw_root, args.prepared_root, args.safe_max_rows)
                print(f'{year} {state} {STATES[state]}: {status}' + (f' ({n} prepared renters)' if n is not None else ''), flush=True)
            except Exception as exc:
                failed.append((year, state, str(exc)))
                print(f'{year} {state}: FAILED {type(exc).__name__}: {exc}', flush=True)
    if failed:
        print(f'\n{len(failed)} extraction(s) failed. Existing successful state-years were preserved.')
        raise SystemExit(1)
    print('All requested extracts present. External bulk completeness NOT certified.')


if __name__ == '__main__':
    main()
