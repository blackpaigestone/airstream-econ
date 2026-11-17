"""Retrieve six New England state PUMS samples without overwriting existing data.

API safety thresholds are conservative. For large states use official bulk files;
never interpret an API truncation as a complete sample.
"""
import argparse
import json
from pathlib import Path
from src.research.acs_pums_api import retrieve_state_pums, save_raw
from src.research.acs_pums_ingest import prepare_pums

STATES = {'09':'Connecticut','23':'Maine','25':'Massachusetts',
          '33':'New Hampshire','44':'Rhode Island','50':'Vermont'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--year',type=int,default=2024)
    parser.add_argument('--states',nargs='+',default=list(STATES),help='State FIPS, default all New England')
    parser.add_argument('--raw-root',default='data/raw/pums')
    parser.add_argument('--prepared-root',default='data/external/pums_prepared')
    args=parser.parse_args()
    import pandas as pd
    for state in args.states:
        state=str(state).zfill(2)
        if state not in STATES: parser.error(f'Not a New England FIPS code: {state}')
        root=Path(args.raw_root)/str(args.year)/f'state_{state}_api'
        output=Path(args.prepared_root)/str(args.year)/f'state_{state}.csv'
        if root.exists() or output.exists():
            raise FileExistsError(f'{state}: existing extract at {root} or {output}; no automatic overwrite')
        print(f'Retrieving {STATES[state]} ({state}) {args.year}',flush=True)
        h,p,provenance=retrieve_state_pums(args.year,state)
        # Validate before writing anything.
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            hpath=Path(temp)/'h.csv'; ppath=Path(temp)/'p.csv'
            h.to_csv(hpath,index=False);p.to_csv(ppath,index=False)
            prepared,audit=prepare_pums(hpath,ppath,args.year,state)
        save_raw(h,p,provenance,root)
        output.parent.mkdir(parents=True,exist_ok=True)
        prepared.to_csv(output,index=False)
        output.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2)+'\n')
        print(f'{STATES[state]}: {len(h)} occupied households, {len(p)} persons, {len(prepared)} prepared renters; {output}',flush=True)
    print('API extracts are provisional until independently checked against official Census bulk PUMS counts.',flush=True)

if __name__=='__main__':main()
