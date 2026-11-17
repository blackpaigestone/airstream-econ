import pandas as pd
import pytest
from src.research.census_rent_burden import parse_burden, validate_burden_panel, refresh_burden


def sample(year=2024):
    codes = {'B25070_001E': 1000, 'B25070_007E': 100,
             'B25070_008E': 100, 'B25070_009E': 100,
             'B25070_010E': 200, 'B25070_011E': 100, 'us': '1'}
    return [list(codes), [str(x) for x in codes.values()]]


def test_parse_denominator_excludes_not_computed():
    row = parse_burden(sample(), 2024)
    assert row['computed_renter_households'] == 900
    assert row['burden_30_households'] == 500
    assert row['burden_50_households'] == 200
    assert row['burden_30_share'] == pytest.approx(5/9)
    assert row['burden_50_share'] == pytest.approx(2/9)


def test_reject_missing_or_invalid_values():
    payload = sample()
    payload[1][1] = '-666666666'
    with pytest.raises(ValueError, match='Invalid'):
        parse_burden(payload, 2024)


def test_reject_inconsistent_counts():
    payload = sample()
    payload[1][0] = '200'
    with pytest.raises(ValueError, match='Inconsistent'):
        parse_burden(payload, 2024)


def test_reject_duplicate_years():
    row = parse_burden(sample(), 2024)
    with pytest.raises(ValueError, match='duplicate'):
        validate_burden_panel(pd.DataFrame([row, row]))


def test_refresh_provenance_and_missing_year(tmp_path):
    def fake(year):
        if year == 2020:
            raise ValueError('2020 ACS standard 1-year data were not released')
        return parse_burden(sample(), year)
    d, record = refresh_burden(2019, 2021,
        destination=tmp_path/'burden.csv', provenance=tmp_path/'provenance.json', fetcher=fake)
    assert d.year.tolist() == [2019, 2021]
    assert record['failures'][0]['year'] == 2020
    assert (tmp_path/'burden.csv').exists()
