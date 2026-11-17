from src.data_sources import SERIES,fetch
for key in SERIES:
    try:
        df=fetch(key)
        print(f'OK {key}: {len(df)} observations, {df.date.min().date()} to {df.date.max().date()}')
    except Exception as e:
        print(f'UNAVAILABLE {key}: {e}')
