import os
from unittest.mock import MagicMock, patch

import build_bird_deck


# ── _safe_name ────────────────────────────────────────────────────────────────

def test_safe_name_preserves_normal_name():
    assert build_bird_deck._safe_name("Robin") == "Robin"


def test_safe_name_replaces_spaces():
    assert build_bird_deck._safe_name("American Robin") == "American_Robin"


def test_safe_name_replaces_special_chars():
    assert build_bird_deck._safe_name("A/B:C*D?E") == "A_B_C_D_E"


def test_safe_name_allows_hyphens_via_regex():
    # hyphens are NOT in [^A-Za-z0-9_] so they become underscores
    result = build_bird_deck._safe_name("Black-capped Chickadee")
    assert " " not in result
    assert "/" not in result


# ── _get_audio ────────────────────────────────────────────────────────────────

def test_get_audio_uses_cache_when_available(tmp_media_dir, sample_sounds_dict):
    with patch("build_bird_deck.media.find_cached_audio", return_value="bird_Robin_call.mp3") as mock_cache, \
         patch("build_bird_deck.media.download_file") as mock_dl:
        field, paths = build_bird_deck._get_audio(sample_sounds_dict, "call", "Robin", tmp_media_dir)

    mock_cache.assert_called_once()
    mock_dl.assert_not_called()
    assert field == "[sound:bird_Robin_call.mp3]"
    assert len(paths) == 1
    assert paths[0].endswith("bird_Robin_call.mp3")


def test_get_audio_downloads_when_not_cached(tmp_media_dir, sample_sounds_dict):
    with patch("build_bird_deck.media.find_cached_audio", return_value=None), \
         patch("build_bird_deck.media.download_file", return_value=True) as mock_dl, \
         patch("build_bird_deck.media.trim_to_mp3", return_value=True), \
         patch("build_bird_deck.os.remove"), \
         patch("build_bird_deck.os.path.getsize", return_value=1024):
        field, paths = build_bird_deck._get_audio(sample_sounds_dict, "call", "Robin", tmp_media_dir)

    mock_dl.assert_called_once()
    assert field == "[sound:bird_Robin_call.mp3]"
    assert len(paths) == 1


def test_get_audio_returns_empty_when_no_urls(tmp_media_dir):
    empty_sounds = {"calls": [], "songs": []}
    with patch("build_bird_deck.media.find_cached_audio", return_value=None):
        field, paths = build_bird_deck._get_audio(empty_sounds, "call", "Robin", tmp_media_dir)

    assert field == ""
    assert paths == []


def test_get_audio_returns_empty_when_download_fails(tmp_media_dir, sample_sounds_dict):
    with patch("build_bird_deck.media.find_cached_audio", return_value=None), \
         patch("build_bird_deck.media.download_file", return_value=False):
        field, paths = build_bird_deck._get_audio(sample_sounds_dict, "call", "Robin", tmp_media_dir)

    assert field == ""
    assert paths == []


# ── _get_images ───────────────────────────────────────────────────────────────

def test_get_images_uses_cache_when_available(tmp_media_dir):
    urls = ["http://example.com/bird.jpg", "http://example.com/bird2.jpg"]
    with patch("build_bird_deck.media.find_cached_image", return_value="bird_Robin_img1.jpg"), \
         patch("build_bird_deck.media.download_file") as mock_dl, \
         patch("build_bird_deck.time.sleep"):
        fields, paths = build_bird_deck._get_images(urls, "Robin", tmp_media_dir)

    mock_dl.assert_not_called()
    assert all(f.startswith("<img") for f in fields if f)


def test_get_images_downloads_when_not_cached(tmp_media_dir):
    urls = ["http://example.com/bird.jpg", "http://example.com/bird2.jpg"]
    with patch("build_bird_deck.media.find_cached_image", return_value=None), \
         patch("build_bird_deck.media.download_file", return_value=True) as mock_dl, \
         patch("build_bird_deck.os.path.getsize", return_value=2048), \
         patch("build_bird_deck.time.sleep"):
        fields, paths = build_bird_deck._get_images(urls, "Robin", tmp_media_dir)

    assert mock_dl.call_count == 2
    assert len(fields) == 2


def test_get_images_pads_to_two_entries_when_empty(tmp_media_dir):
    with patch("build_bird_deck.time.sleep"):
        fields, paths = build_bird_deck._get_images([], "Robin", tmp_media_dir)

    assert fields == ["", ""]
    assert paths == []


def test_get_images_pads_to_two_entries_when_one_url(tmp_media_dir):
    urls = ["http://example.com/bird.jpg"]
    with patch("build_bird_deck.media.find_cached_image", return_value=None), \
         patch("build_bird_deck.media.download_file", return_value=True), \
         patch("build_bird_deck.os.path.getsize", return_value=1024), \
         patch("build_bird_deck.time.sleep"):
        fields, paths = build_bird_deck._get_images(urls, "Robin", tmp_media_dir)

    assert len(fields) == 2
    assert fields[0].startswith("<img")
    assert fields[1] == ""
