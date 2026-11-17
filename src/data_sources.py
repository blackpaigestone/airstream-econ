"""Download raw observations; never synthesize missing historical observations."""
from pathlib import Path
from io import StringIO
import requests
import pandas as pd
SERIES={
 'CPIAUCSL':'Consumer price index, all urban consumers',
 'MEHOINUSA672N':'Real median household income (FRED series-specific price base)',
 'MSPUS':'Median sales price, new houses sold (not all existing homes)',
 'USSTHPI':'FHFA house price index',
 'MORTGAGE30US':'30-year fixed mortgage rate',
 'UNRATE':'Unemployment rate',
 'CIVPART':'Civilian labor force participation',
}
def fetch(series, directory='data/raw'):
    if series not in SERIES: raise ValueError('Unknown series')
    url=f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}'
    response=requests.get(url,timeout=35,headers={'User-Agent':'airstream-economics-research/0.1'})
    response.raise_for_status()
    df=pd.read_csv(StringIO(response.text))
    df.columns=['date','value']
    df['date']=pd.to_datetime(df['date'],errors='raise')
    df['value']=pd.to_numeric(df['value'],errors='coerce')
    df=df.dropna(subset=['value']).sort_values('date')
    if df.empty: raise ValueError(f'No usable data for {series}')
    path=Path(directory);path.mkdir(parents=True,exist_ok=True)
    df.to_csv(path/f'{series}.csv',index=False)
    return df

def load(series, directory='data/raw'):
    path=Path(directory)/f'{series}.csv'
    if not path.exists(): return None
    df=pd.read_csv(path,parse_dates=['date'])
    return df if not df.empty else None
