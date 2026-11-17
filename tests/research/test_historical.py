from pathlib import Path
import pandas as pd
import pytest
from src.research.historical import build_historical_panel, REQUIRED


def write_data(folder, key, years, values):
    pd.DataFrame({'date': [f'{year}-01-01' for year in years], 'value': values}).to_csv(folder / f'{key}.csv', index=False)


def fixture_data(tmp_path):
    years = [1990, 1991, 1992]
    inputs = {
        'CPIAUCSL': [100, 110, 120],
        'MEHOINUSA672N': [50000, 55000, 55000],
        'MSPUS': [100000, 121000, 144000],
        'USSTHPI': [100, 121, 144],
        'MORTGAGE30US': [8, 8, 8],
    }
    for k, v in inputs.items():
        write_data(tmp_path, k, years, v)
    return inputs


def test_base_year_normalization(tmp_path):
    fixture_data(tmp_path)
    panel = build_historical_panel(tmp_path)
    for key in ('real_income_index','real_new_home_price_index','real_fhfa_index','new_home_price_to_income_index','mortgage_payment_to_income_index'):
        assert panel.loc[0, key] == pytest.approx(100)


def test_real_income_not_double_deflated(tmp_path):
    fixture_data(tmp_path)
    panel = build_historical_panel(tmp_path)
    assert panel.loc[1, 'real_income_index'] == pytest.approx(110)
    assert panel.loc[1, 'real_new_home_price_index'] == pytest.approx(110)
    assert panel.loc[1, 'new_home_price_to_income_index'] == pytest.approx(100)
    assert panel.loc[1, 'mortgage_payment_to_income_index'] == pytest.approx(100)


def test_payment_burden_responds_to_interest_rates(tmp_path):
    fixture_data(tmp_path)
    write_data(tmp_path, 'MORTGAGE30US', [1990,1991,1992], [8, 12, 8])
    panel = build_historical_panel(tmp_path)
    assert panel.loc[1, 'mortgage_payment_to_income_index'] > 100


def test_missing_data_never_fabricated(tmp_path):
    fixture_data(tmp_path)
    (tmp_path / 'MSPUS.csv').unlink()
    with pytest.raises(FileNotFoundError):
        build_historical_panel(tmp_path)


def test_common_years_only(tmp_path):
    fixture_data(tmp_path)
    write_data(tmp_path, 'USSTHPI', [1990,1992], [100,144])
    panel = build_historical_panel(tmp_path)
    assert list(panel.year) == [1990,1992]


def test_no_baseline(tmp_path):
    fixture_data(tmp_path)
    with pytest.raises(ValueError, match='baseline'):
        build_historical_panel(tmp_path, base_year=1989)


def test_income_duplicates_rejected(tmp_path):
    fixture_data(tmp_path)
    pd.DataFrame({'date':['1990-01-01','1990-06-01'], 'value':[50000,51000]}).to_csv(tmp_path/'MEHOINUSA672N.csv', index=False)
    with pytest.raises(ValueError, match='one observation'):
        build_historical_panel(tmp_path)
