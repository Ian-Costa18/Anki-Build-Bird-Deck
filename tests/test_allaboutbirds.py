from unittest.mock import MagicMock, patch

from avianki import allaboutbirds


def _mock_response(text: str, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


# ── species_slug ──────────────────────────────────────────────────────────────

def test_species_slug_replaces_spaces():
    assert allaboutbirds.species_slug("Black-capped Chickadee") == "Black-capped_Chickadee"


def test_species_slug_no_change_when_no_spaces():
    assert allaboutbirds.species_slug("Robin") == "Robin"


# ── fetch_browse_species ──────────────────────────────────────────────────────

BROWSE_HTML = """
<a href="/guide/Black-capped_Chickadee/overview">Chickadee</a>
<a href="/guide/American_Robin/overview">Robin</a>
<a href="/guide/Song_Sparrow/overview">Sparrow</a>
"""


def test_fetch_browse_species_parses_slugs():
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response(BROWSE_HTML)):
        result = allaboutbirds.fetch_browse_species("https://www.allaboutbirds.org/guide/browse/...")
    assert result == ["Black-capped_Chickadee", "American_Robin", "Song_Sparrow"]


def test_fetch_browse_species_deduplicates():
    html = BROWSE_HTML + '<a href="/guide/American_Robin/overview">Robin again</a>'
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response(html)):
        result = allaboutbirds.fetch_browse_species("https://example.com")
    assert result.count("American_Robin") == 1


def test_fetch_browse_species_respects_limit():
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response(BROWSE_HTML)):
        result = allaboutbirds.fetch_browse_species("https://example.com", limit=2)
    assert len(result) == 2


def test_fetch_browse_species_constructs_url_from_place_id():
    place_id = "ChIJGzE9DS1l44kRoOhiASS_fHg"
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response(BROWSE_HTML)) as mock_get:
        allaboutbirds.fetch_browse_species(place_id)
    called_url = mock_get.call_args[0][0]
    assert place_id in called_url
    assert called_url.startswith("https://")


def test_fetch_browse_species_returns_empty_on_error():
    with patch("avianki.allaboutbirds.requests.get", side_effect=ConnectionError("down")):
        result = allaboutbirds.fetch_browse_species("https://example.com")
    assert result == []


# ── slug_to_names ─────────────────────────────────────────────────────────────

NAMES_HTML = """
<title>Black-capped Chickadee Overview, All About Birds…</title>
<em class="sci-name">Poecile atricapillus</em>
"""


def test_slug_to_names_parses_title_and_sci_name():
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response(NAMES_HTML)):
        result = allaboutbirds.slug_to_names("Black-capped_Chickadee")
    assert result["comName"] == "Black-capped Chickadee"
    assert result["sciName"] == "Poecile atricapillus"


def test_slug_to_names_fallback_on_missing_sci_name():
    html = "<title>American Robin Overview, All About Birds…</title>"
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response(html)):
        result = allaboutbirds.slug_to_names("American_Robin")
    assert result["comName"] == "American Robin"
    assert result["sciName"] == ""


def test_slug_to_names_uses_itemprop_fallback():
    html = """<title>American Robin Overview, All About Birds…</title>
    <i itemprop="name">Turdus migratorius</i>"""
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response(html)):
        result = allaboutbirds.slug_to_names("American_Robin")
    assert result["sciName"] == "Turdus migratorius"


def test_slug_to_names_fallback_on_request_error():
    with patch("avianki.allaboutbirds.requests.get", side_effect=ConnectionError("down")):
        result = allaboutbirds.slug_to_names("American_Robin")
    assert result["comName"] == "American Robin"
    assert result["sciName"] == ""


# ── fetch_overview ────────────────────────────────────────────────────────────

OVERVIEW_HTML = """
<meta name="description" content="The Black-capped Chickadee is a small bird.">
<em class="sci-name">Poecile atricapillus</em>
<img src="/guide/assets/photo/12345-480px.jpg">
<img src="/guide/assets/photo/67890-480px.jpg">
"""


def test_fetch_overview_parses_description():
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response(OVERVIEW_HTML)):
        result = allaboutbirds.fetch_overview("Black-capped_Chickadee")
    assert "Black-capped Chickadee" in result["desc"]


def test_fetch_overview_parses_sci_name():
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response(OVERVIEW_HTML)):
        result = allaboutbirds.fetch_overview("Black-capped_Chickadee")
    assert result["sciName"] == "Poecile atricapillus"


def test_fetch_overview_constructs_720px_image_urls():
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response(OVERVIEW_HTML)):
        result = allaboutbirds.fetch_overview("Black-capped_Chickadee")
    assert len(result["images"]) == 2
    assert all("720px" in url for url in result["images"])


def test_fetch_overview_uses_itemprop_fallback_for_sci_name():
    html = """
<meta name="description" content="A common backyard bird.">
<i itemprop="name">Turdus migratorius</i>
"""
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response(html)):
        result = allaboutbirds.fetch_overview("American_Robin")
    assert result["sciName"] == "Turdus migratorius"


def test_fetch_overview_returns_empty_on_error():
    with patch("avianki.allaboutbirds.requests.get", side_effect=ConnectionError("down")):
        result = allaboutbirds.fetch_overview("Black-capped_Chickadee")
    assert result["desc"] == ""
    assert result["images"] == []


# ── fetch_sounds ──────────────────────────────────────────────────────────────

SOUNDS_HTML = """
<div name="https://www.allaboutbirds.org/guide/assets/sound/111.mp3"
     class="jp-flat-audio" aria-label="Call - chick-a-dee"></div>
<div name="https://www.allaboutbirds.org/guide/assets/sound/222.mp3"
     class="jp-flat-audio" aria-label="Song - fee-bee"></div>
"""


def test_fetch_sounds_separates_calls_and_songs():
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response(SOUNDS_HTML)):
        result = allaboutbirds.fetch_sounds("Black-capped_Chickadee")
    assert len(result["calls"]) == 1
    assert len(result["songs"]) == 1
    assert "111.mp3" in result["calls"][0]
    assert "222.mp3" in result["songs"][0]


def test_fetch_sounds_empty_on_no_matches():
    with patch("avianki.allaboutbirds.requests.get", return_value=_mock_response("<html></html>")):
        result = allaboutbirds.fetch_sounds("Black-capped_Chickadee")
    assert result == {"calls": [], "songs": []}


def test_fetch_sounds_returns_empty_on_error():
    with patch("avianki.allaboutbirds.requests.get", side_effect=ConnectionError("down")):
        result = allaboutbirds.fetch_sounds("Black-capped_Chickadee")
    assert result == {"calls": [], "songs": []}
