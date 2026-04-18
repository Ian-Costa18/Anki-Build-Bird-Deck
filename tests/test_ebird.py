from unittest.mock import MagicMock, call, patch

import ebird


def _mock_json_response(data) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = data
    resp.raise_for_status = MagicMock()
    return resp


# ── _headers ──────────────────────────────────────────────────────────────────

def test_headers_reads_env_key(monkeypatch):
    monkeypatch.setenv("EBIRD_API_KEY", "test-key-123")
    assert ebird._headers() == {"X-eBirdApiToken": "test-key-123"}


def test_headers_empty_when_no_env_key(monkeypatch):
    monkeypatch.delenv("EBIRD_API_KEY", raising=False)
    assert ebird._headers() == {"X-eBirdApiToken": ""}


# ── fetch_species ─────────────────────────────────────────────────────────────

TAXONOMY_DATA = [
    {"speciesCode": "bkcchi", "comName": "Black-capped Chickadee", "sciName": "Poecile atricapillus"},
    {"speciesCode": "amerob", "comName": "American Robin", "sciName": "Turdus migratorius"},
]


def test_fetch_species_returns_list(monkeypatch):
    monkeypatch.setenv("EBIRD_API_KEY", "key")
    codes_resp = _mock_json_response(["bkcchi", "amerob"])
    taxonomy_resp = _mock_json_response(TAXONOMY_DATA)

    with patch("ebird.requests.get", side_effect=[codes_resp, taxonomy_resp]):
        result = ebird.fetch_species("US-MA")

    assert len(result) == 2
    assert result[0]["speciesCode"] == "bkcchi"
    assert result[0]["comName"] == "Black-capped Chickadee"
    assert result[0]["sciName"] == "Poecile atricapillus"


def test_fetch_species_respects_limit(monkeypatch):
    monkeypatch.setenv("EBIRD_API_KEY", "key")
    codes_resp = _mock_json_response(["bkcchi", "amerob"])
    taxonomy_resp = _mock_json_response(TAXONOMY_DATA[:1])

    with patch("ebird.requests.get", side_effect=[codes_resp, taxonomy_resp]):
        result = ebird.fetch_species("US-MA", limit=1)

    assert len(result) == 1


def test_fetch_species_batches_large_lists(monkeypatch):
    monkeypatch.setenv("EBIRD_API_KEY", "key")
    # 201 species codes triggers 2 taxonomy batch requests
    codes = [f"sp{i:03d}" for i in range(201)]
    taxonomy_batch1 = [{"speciesCode": c, "comName": c, "sciName": ""} for c in codes[:200]]
    taxonomy_batch2 = [{"speciesCode": c, "comName": c, "sciName": ""} for c in codes[200:]]

    codes_resp = _mock_json_response(codes)
    tax_resp1 = _mock_json_response(taxonomy_batch1)
    tax_resp2 = _mock_json_response(taxonomy_batch2)

    with patch("ebird.requests.get", side_effect=[codes_resp, tax_resp1, tax_resp2]) as mock_get:
        result = ebird.fetch_species("US-MA")

    assert mock_get.call_count == 3  # 1 species list + 2 taxonomy batches
    assert len(result) == 201
