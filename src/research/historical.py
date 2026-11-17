"""Historical national benchmarks. Descriptive comparisons, not causal estimates."""
from pathlib import Path
import pandas as pd

REQUIRED = ('CPIAUCSL', 'MEHOINUSA672N', 'MSPUS', 'USSTHPI', 'MORTGAGE30US')

def annual_series(series, folder):
    """Annual arithmetic mean for high-frequency series; annual income as reported."""
    path = Path(folder) / f'{series}.csv'
    if not path.is_file():
        raise FileNotFoundError(f'Missing {series}; run python refresh_data.py')
    df = pd.read_csv(path)
    if not {'date', 'value'}.issubset(df.columns):
        raise ValueError(f'{series}: expected date and value columns')
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna(subset=['date', 'value'])
    if df.empty or df['date'].duplicated().any():
        raise ValueError(f'{series}: empty or duplicate dates')
    df['year'] = df['date'].dt.year
    if series == 'MEHOINUSA672N':
        if df['year'].duplicated().any():
            raise ValueError('Income series must have one observation per year')
        return df.set_index('year')['value'].sort_index()
    return df.groupby('year')['value'].mean().sort_index()

def build_historical_panel(folder='data/raw', base_year=1990, end_year=None):
    """Build common-year indices; never fill or extrapolate missing observations.

    MEHOINUSA672N is ALREADY real. We never deflate it again.
    Nominal new-home prices and mortgage payments are divided by CPI *relative
    to base_year*, so the resulting indexed ratios are price-base invariant.
    """
    if not isinstance(base_year, int):
        raise ValueError('base_year must be an integer')
    series = {key: annual_series(key, folder) for key in REQUIRED}
    panel = pd.concat(series, axis=1, join='inner').sort_index()
    panel = panel.loc[panel.index >= base_year]
    if end_year is not None:
        panel = panel.loc[panel.index <= end_year]
    if base_year not in panel.index:
        raise ValueError(f'No common baseline observation for {base_year}')
    if panel.empty:
        raise ValueError('No common historical years')
    if (panel[list(REQUIRED)] <= 0).any().any():
        raise ValueError('All input values must be positive')
    base = panel.loc[base_year]
    cpi_rel = panel['CPIAUCSL'] / base['CPIAUCSL']
    real_income_rel = panel['MEHOINUSA672N'] / base['MEHOINUSA672N']
    real_home_rel = (panel['MSPUS'] / base['MSPUS']) / cpi_rel
    real_fhfa_rel = (panel['USSTHPI'] / base['USSTHPI']) / cpi_rel
    rate = panel['MORTGAGE30US'] / 1200
    n = 360
    payment_factor = rate / (1 - (1 + rate) ** (-n))
    payment_rel = (panel['MSPUS'] / base['MSPUS']) * (payment_factor / payment_factor.loc[base_year])
    out = pd.DataFrame(index=panel.index)
    out.index.name = 'year'
    out['real_income_index'] = 100 * real_income_rel
    out['real_new_home_price_index'] = 100 * real_home_rel
    out['real_fhfa_index'] = 100 * real_fhfa_rel
    out['new_home_price_to_income_index'] = 100 * real_home_rel / real_income_rel
    out['mortgage_payment_to_income_index'] = 100 * payment_rel / cpi_rel / real_income_rel
    out['mortgage_rate_pct'] = panel['MORTGAGE30US']
    out['nominal_new_home_price'] = panel['MSPUS']
    out['cpi'] = panel['CPIAUCSL']
    out['real_median_household_income'] = panel['MEHOINUSA672N']
    return out.reset_index()
