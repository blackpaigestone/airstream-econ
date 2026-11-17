import os
import pytest
import requests
from src.research.census_acs import fetch_year, refresh
from tests.research.test_census_acs import fixture

class FakeResponse:
    def __init__(self, data=None, content_type='application/json', status=200):
        self.data = data
        self.headers = {'Content-Type': content_type}
        self.status_code = status
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError('failure', response=self)
    def json(self):
        return self.data

class FakeSession:
    def __init__(self, metadata, payload, content_type='application/json'):
        self.metadata = metadata
        self.payload = payload
        self.content_type = content_type
        self.calls = []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if '/groups/' in url:
            return FakeResponse(self.metadata)
        return FakeResponse(self.payload, self.content_type)

def test_authenticated_request(monkeypatch):
    monkeypatch.setenv('CENSUS_API_KEY', 'a' * 40)
    m, p = fixture()
    session = FakeSession(m, p)
    assert len(fetch_year(2024, session=session)) == 3
    assert session.calls[1][1]['params']['key'] == 'a' * 40
    assert 'key' not in session.calls[0][1]

def test_key_stripped(monkeypatch):
    monkeypatch.setenv('CENSUS_API_KEY', '  abc  ')
    m, p = fixture()
    session = FakeSession(m, p)
    fetch_year(2024, session=session)
    assert session.calls[1][1]['params']['key'] == 'abc'

def test_no_key(monkeypatch):
    monkeypatch.delenv('CENSUS_API_KEY', raising=False)
    m, p = fixture()
    session = FakeSession(m, p)
    fetch_year(2024, session=session)
    assert 'key' not in session.calls[1][1]['params']

def test_html_invalid_key_is_rejected(monkeypatch):
    monkeypatch.setenv('CENSUS_API_KEY', 'secretvalue')
    m, p = fixture()
    session = FakeSession(m, p, content_type='text/html')
    with pytest.raises(ValueError, match='non-JSON') as exc:
        fetch_year(2024, session=session)
    assert 'secretvalue' not in str(exc.value)

def test_2020_is_skipped_without_request():
    with pytest.raises(ValueError, match='not released'):
        fetch_year(2020)

def test_failure_provenance_redacts_key(monkeypatch, tmp_path):
    monkeypatch.setenv('CENSUS_API_KEY', 'secretvalue')
    m, p = fixture()
    from src.research.census_acs import parse_response
    def fetcher(year):
        if year == 2022:
            raise requests.HTTPError('https://api.census.gov/?key=secretvalue')
        return parse_response(m, p, year)
    _, provenance = refresh(2022, 2023, tmp_path/'panel.csv', tmp_path/'prov.json', fetcher)
    assert 'secretvalue' not in str(provenance)
    assert 'secretvalue' not in (tmp_path/'prov.json').read_text()
