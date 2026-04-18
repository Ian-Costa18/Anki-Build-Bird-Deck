import pytest


@pytest.fixture()
def tmp_media_dir(tmp_path):
    d = tmp_path / "media"
    d.mkdir()
    return str(d)


@pytest.fixture()
def sample_sounds_dict():
    return {
        "calls": ["http://example.com/call.mp3"],
        "songs": ["http://example.com/song.mp3"],
    }
