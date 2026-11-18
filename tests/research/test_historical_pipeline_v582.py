import hashlib
import json
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from research.historical_pipeline_v582 import ensure_file, extract_one, inspect_panel, run


def _archive(folder, name, member, content=b'SERIALNO,ST\n1,23\n'):
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(folder / name, 'w') as z:
        z.writestr(member, content)


def test_offline_archives_and_hashes(tmp_path):
    folder = tmp_path / '2018'
    _archive(folder, 'csv_hme.zip', 'psam_h23.csv')
    record = ensure_file(2018, '23', 'h', tmp_path, offline=True)
    assert Path(record['csv']).read_bytes() == b'SERIALNO,ST\n1,23\n'
    assert record['csv_sha256'] == hashlib.sha256(b'SERIALNO,ST\n1,23\n').hexdigest()
    assert record['url'].endswith('/2018/1-Year/csv_hme.zip')


def test_tampered_extraction_fails(tmp_path):
    folder = tmp_path / '2018'
    _archive(folder, 'csv_hme.zip', 'psam_h23.csv')
    ensure_file(2018, '23', 'h', tmp_path, offline=True)
    (folder / 'psam_h23.csv').write_text('tampered')
    with pytest.raises(ValueError, match='Extract differs'):
        ensure_file(2018, '23', 'h', tmp_path, offline=True)


def test_wrong_member_fails(tmp_path):
    folder = tmp_path / '2018'
    _archive(folder, 'csv_hme.zip', 'unexpected.csv')
    with pytest.raises(ValueError, match='Missing or duplicate'):
        ensure_file(2018, '23', 'h', tmp_path, offline=True)


def test_unsupported_year_rejected(tmp_path):
    with pytest.raises(ValueError):
        ensure_file(2014, '23', 'h', tmp_path, offline=True)


def test_run_failure_is_audited(tmp_path):
    report = run(years=[2018], states=['23'], raw_root=tmp_path / 'raw',
                 prepared_root=tmp_path / 'prepared', audit_root=tmp_path / 'audit', offline=True)
    assert report['counts']['failed'] == 1
    assert 'Offline archive missing' in report['items'][0]['error']
    assert json.loads((tmp_path / 'audit' / 'v582_run.json').read_text())['counts']['failed'] == 1


def test_run_skips_existing(tmp_path):
    out = tmp_path / 'prepared' / '2018' / 'state_23.csv'
    out.parent.mkdir(parents=True)
    out.write_text('already prepared')
    report = run(years=[2018], states=['23'], raw_root=tmp_path / 'raw',
                 prepared_root=tmp_path / 'prepared', audit_root=tmp_path / 'audit', offline=True)
    assert report['counts']['skipped_existing'] == 1


def test_download_only_no_import(tmp_path):
    raw = tmp_path / 'raw'
    _archive(raw / '2018', 'csv_hme.zip', 'psam_h23.csv')
    _archive(raw / '2018', 'csv_pme.zip', 'psam_p23.csv')
    report = run(years=[2018], states=['23'], raw_root=raw,
                 prepared_root=tmp_path / 'prepared', audit_root=tmp_path / 'audit',
                 offline=True, download_only=True)
    assert report['counts']['downloaded'] == 1
    assert len(report['items'][0]['sources']) == 2


def test_panel_coverage(tmp_path):
    path = tmp_path / 'panel.csv'
    path.write_text('year,value\n2019,1\n2019,2\n2021,3\n')
    assert inspect_panel(path, [], [])['rows_by_year'] == {'2019': 2, '2021': 1}


@pytest.mark.parametrize('year,kind,member', [
    (2015, 'h', 'ss15hct.csv'),
    (2015, 'p', 'ss15pct.csv'),
    (2016, 'h', 'ss16hct.csv'),
    (2016, 'p', 'ss16pct.csv'),
    (2017, 'h', 'psam_h09.csv'),
    (2017, 'p', 'psam_p09.csv'),
])
def test_historical_archive_filename_mapping(tmp_path, year, kind, member):
    _archive(tmp_path / str(year), f'csv_{kind}ct.zip', member)
    result = ensure_file(year, '09', kind, tmp_path, offline=True)
    assert Path(result['csv']).name == member
    assert Path(result['csv']).exists()
