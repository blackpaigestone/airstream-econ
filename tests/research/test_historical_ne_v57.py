import pandas as pd
import pytest
from src.research.historical_ne_v57 import compare_endpoints, historical
from refresh_historical_ne import collect


def test_endpoints_percentage_points():
    rows=[]
    for year, rate in ((2021,.4),(2024,.5)):
        rows.append(dict(year=year, geography='Maine', age_group='25-34', household_group='one_person',earner_group='all',threshold=.30,rate=rate))
    result=compare_endpoints(pd.DataFrame(rows),2021,2024)
    assert result.change_percentage_points.iloc[0] == pytest.approx(10)


def test_missing_endpoint_rejected():
    frame=pd.DataFrame([dict(year=2024, geography='Maine',age_group='25-34',household_group='one_person',earner_group='all',threshold=.30,rate=.5)])
    with pytest.raises(ValueError, match='Both endpoint'):
        compare_endpoints(frame,2021,2024)


def test_invalid_years_rejected():
    with pytest.raises(ValueError, match='Supported historical years'):
        historical([2020])


def test_existing_extract_is_never_overwritten(tmp_path):
    raw=tmp_path/'raw'; prepared=tmp_path/'prepared'
    path=prepared/'2021'/'state_23.csv'
    path.parent.mkdir(parents=True)
    path.write_text('existing')
    status, n=collect(2021,'23',raw,prepared)
    assert (status,n)==('EXISTS',None)
    assert path.read_text()=='existing'
