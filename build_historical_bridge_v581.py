"""Append only complete six-state historical bulk years to the V5.8 panel."""
import argparse
import json
from pathlib import Path
import pandas as pd
from src.research.historical_bulk_v581 import STATES
from src.research.new_england_v56 import REQUIRED,stratify,analyze
from src.research.long_run_v58 import BASE,METRIC

def build(years,prepared_root,base_panel):
    panel=pd.read_csv(base_panel)
    if set(BASE)-set(panel):raise ValueError('V5.8 base panel schema mismatch')
    rows=[]
    for year in sorted(set(years)):
        if year not in range(2015,2020):raise ValueError('Bridge only supports 2015–2019')
        frames=[]
        for state in STATES:
            path=Path(prepared_root)/str(year)/f'state_{state}.csv'
            apath=path.with_suffix('.audit.json')
            if not path.exists() or not apath.exists():raise FileNotFoundError(f'Incomplete six-state year: {path} / audit')
            frame=pd.read_csv(path,dtype={'household_id':'string'})
            audit=json.loads(apath.read_text())
            if not len(frame)==audit['prepared_renter_households'] or audit['source_id']!=f'ACS1_PUMS_{year}_ST{state}' or REQUIRED-set(frame):
                raise ValueError(f'Prepared data/audit mismatch {path}')
            frame['state_fips']=state;frames.append(frame)
        estimates=analyze(stratify(pd.concat(frames,ignore_index=True)))
        if estimates.empty:raise ValueError(f'No estimates for {year}')
        sub=estimates.loc[estimates.threshold.eq(.30)].copy()
        for _,r in sub.iterrows():
            rows.append({'year':year,'geography':r.geography,'metric':METRIC,'age_group':r.age_group,
              'household_group':r.household_group,'earner_group':r.earner_group,'estimate':r.rate,'sample_n':r.sample_n,
              'source_id':f'ACS1_PUMS_{year}_V581','source_type':'ACS1_PUMS_bulk_derived',
              'weight_basis':'WGTP household weight','comparability_status':'historical_mapping_provisional',
              'variance_status':'not_estimated','bulk_verified':False,
              'notes':'Historical ACS1 renter burden, six-state completeness of inputs only; cross-era comparability and external bulk counts unverified.'})
    historical=pd.DataFrame(rows,columns=BASE)
    merged=pd.concat([panel[BASE],historical],ignore_index=True)
    key=['year','geography','metric','age_group','household_group','earner_group']
    if merged.duplicated(key).any():raise ValueError('Duplicate historical estimates; refusing merge')
    return merged.sort_values(key).reset_index(drop=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--years',type=int,nargs='+',required=True)
    p.add_argument('--prepared-root',default='data/external/pums_prepared')
    p.add_argument('--base-panel',default='data/derived/v58/long_run_panel.csv')
    p.add_argument('--out',default='data/derived/v581/long_run_panel.csv')
    a=p.parse_args();out=Path(a.out)
    if out.exists():raise FileExistsError(f'Refusing to overwrite {out}')
    frame=build(a.years,a.prepared_root,a.base_panel)
    out.parent.mkdir(parents=True,exist_ok=True);frame.to_csv(out,index=False)
    print('SAVED',out,'rows:',len(frame),'years:',sorted(frame.year.unique().tolist()))
    print('Historical estimates provisional; no 1990/2000 data, uncertainty intervals or certified cross-era trend.')
if __name__=='__main__':main()
