"""V5.8.2: resumable ACS 1-year PUMS bulk downloader and conservative ingestion.

Pilot years 2015-2018. No external Census population-count certification or
survey replicate-weight uncertainty is implied by successful ingestion.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from research.historical_bulk_v581 import STATES, prepare, save

BASE = 'https://www2.census.gov/programs-surveys/acs/data/pums/{year}/1-Year'
YEARS = range(2015, 2019)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    """Download atomically; failed transfers never leave a seemingly valid ZIP."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.acs-', suffix='.part', dir=destination.parent)
    os.close(fd)
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'airstream-econ-research/5.8.2'})
        with urllib.request.urlopen(request, timeout=120) as response, open(tmp, 'wb') as target:
            shutil.copyfileobj(response, target)
        os.replace(tmp, destination)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def extract_one(archive: Path, target: Path, expected: str) -> None:
    """Extract exactly one expected CSV, avoiding archive path traversal."""
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError(f'ZIP integrity failed: {archive}')
        matches = [n for n in z.namelist() if Path(n).name.lower() == expected.lower() and not n.endswith('/')]
        if len(matches) != 1:
            raise ValueError(f'Expected exactly one {expected} in {archive}; found {matches}')
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix='.acs-', suffix='.csv.part', dir=target.parent)
        os.close(fd)
        try:
            with z.open(matches[0]) as source, open(tmp, 'wb') as dest:
                shutil.copyfileobj(source, dest)
            os.replace(tmp, target)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


def ensure_file(year: int, state: str, kind: str, raw_root: Path, *, offline: bool = False) -> dict:
    if year not in YEARS or state not in STATES or kind not in ('h', 'p'):
        raise ValueError('Only 2015–2018, six NE states, h/p files supported')
    abbr = {'09':'ct','23':'me','25':'ma','33':'nh','44':'ri','50':'vt'}[state]
    archive_name = f'csv_{kind}{abbr}.zip'
    # 2015–2016 archives use ssYY[h|p]ST.csv; 2017+ use psam_[h|p]FIPS.csv.
    expected = (f'ss{str(year)[-2:]}{kind}{abbr}.csv' if year <= 2016
                else f'psam_{kind}{state}.csv')
    folder = raw_root / str(year)
    archive = folder / archive_name
    extracted = folder / expected
    url = f'{BASE.format(year=year)}/{archive_name}'
    if not archive.exists():
        if offline:
            raise FileNotFoundError(f'Offline archive missing: {archive}')
        download(url, archive)
    try:
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:
                raise ValueError(f'Corrupt ZIP: {archive}')
            if len([n for n in z.namelist() if Path(n).name.lower() == expected.lower()]) != 1:
                raise ValueError(f'Missing or duplicate {expected} in {archive}')
    except (zipfile.BadZipFile, ValueError):
        # Do not silently overwrite downloaded or manually supplied evidence.
        raise
    if not extracted.exists():
        extract_one(archive, extracted, expected)
    # Detect stale or altered extracts by streaming a comparison to the ZIP member.
    with zipfile.ZipFile(archive) as z:
        member = next(n for n in z.namelist() if Path(n).name.lower() == expected.lower())
        expected_hash = hashlib.sha256()
        with z.open(member) as source:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                expected_hash.update(block)
    if sha256(extracted) != expected_hash.hexdigest():
        raise ValueError(f'Extract differs from archive; move aside and retry: {extracted}')
    return {'year': year, 'state_fips': state, 'kind': kind, 'url': url,
            'archive': str(archive), 'archive_sha256': sha256(archive),
            'csv': str(extracted), 'csv_sha256': sha256(extracted),
            'csv_bytes': extracted.stat().st_size}


def inspect_panel(path: Path, years: list[int], states: list[str]) -> dict:
    """Report subgroup coverage without assuming fixed row counts across years."""
    if not path.exists():
        return {'panel_path': str(path), 'exists': False}
    with path.open(newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or 'year' not in reader.fieldnames:
            return {'panel_path': str(path), 'exists': True, 'error': 'No year column'}
        rows_by_year: dict[str, int] = {}
        for row in reader:
            key = str(row['year'])
            rows_by_year[key] = rows_by_year.get(key, 0) + 1
    return {'panel_path': str(path), 'exists': True, 'rows_by_year': rows_by_year,
            'note': 'Row-count differences are flagged for review, not automatically imputed.'}


def run(*, years: list[int], states: list[str], raw_root: Path,
        prepared_root: Path, audit_root: Path, offline: bool = False,
        download_only: bool = False, skip_existing: bool = True) -> dict:
    if not years or not states or any(y not in YEARS for y in years) or any(s not in STATES for s in states):
        raise ValueError('Specify supported years (2015–2018) and six-state FIPS codes')
    audit_root.mkdir(parents=True, exist_ok=True)
    report = {'version': '5.8.2', 'years': years, 'states': states, 'items': [],
              'certification': {'archive_integrity': 'checked',
                'household_person_match': 'checked by V5.8.1 importer when imported',
                'external_source_completeness': 'NOT CERTIFIED',
                'survey_design_uncertainty': 'NOT ESTIMATED',
                'cross_year_comparability': 'NOT CERTIFIED'}}
    for year in years:
        for state in states:
            output = prepared_root / str(year) / f'state_{state}.csv'
            entry = {'year': year, 'state_fips': state}
            if output.exists() and skip_existing and not download_only:
                entry['status'] = 'skipped_existing'
                report['items'].append(entry)
                print(f'SKIP {year} state {state}: {output}', flush=True)
                continue
            try:
                files = [ensure_file(year, state, kind, raw_root, offline=offline) for kind in ('h', 'p')]
                entry['sources'] = files
                if download_only:
                    entry['status'] = 'downloaded'
                else:
                    prepared, audit = prepare(Path(files[0]['csv']), Path(files[1]['csv']), year, state)
                    audit['v582_sources'] = files
                    saved = save(prepared, audit, prepared_root)
                    entry.update(status='imported', prepared_path=str(saved), prepared_rows=len(prepared),
                                 audit_path=str(saved.with_suffix('.audit.json')))
                print(f"OK {year} state {state}: {entry['status']}", flush=True)
            except Exception as exc:
                entry.update(status='failed', error=f'{type(exc).__name__}: {exc}')
                print(f"FAIL {year} state {state}: {entry['error']}", flush=True)
            report['items'].append(entry)
            # Persist progress even if a later state fails.
            (audit_root / 'v582_run.json').write_text(json.dumps(report, indent=2) + '\n')
    report['counts'] = {status: sum(x['status'] == status for x in report['items'])
                        for status in ('imported','downloaded','skipped_existing','failed')}
    (audit_root / 'v582_run.json').write_text(json.dumps(report, indent=2) + '\n')
    return report
