import pandas as pd
from src.research.acs_pums_ingest import prepare_pums


def test_group_quarters_excluded_before_householder_validation(tmp_path):
    h = pd.DataFrame([
        dict(SERIALNO='hu1', ST='23', NP=2, TEN=3, HINCP=60000, GRNTP=1200, WGTP=12),
        dict(SERIALNO='gq1', ST='23', NP=1, TEN=0, HINCP=0, GRNTP=0, WGTP=1),
    ])
    p = pd.DataFrame([
        dict(SERIALNO='hu1', SPORDER=1, RELSHIPP=20, AGEP=30, WAGP=50000, SEMP=0),
        dict(SERIALNO='hu1', SPORDER=2, RELSHIPP=21, AGEP=29, WAGP=10000, SEMP=0),
        dict(SERIALNO='gq1', SPORDER=1, RELSHIPP=38, AGEP=20, WAGP=0, SEMP=0),
    ])
    hp, pp = tmp_path/'h.csv', tmp_path/'p.csv'
    h.to_csv(hp,index=False); p.to_csv(pp,index=False)
    out, audit = prepare_pums(hp, pp, 2024, '23')
    assert len(out) == 1
    assert out.iloc[0].household_id == 'hu1'
    assert audit['group_quarters_excluded'] == 1
    assert audit['housing_units_input'] == 1
    assert audit['households_input'] == 2
