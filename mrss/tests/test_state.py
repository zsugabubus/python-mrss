from mrss._state import *
import pytest


@pytest.fixture
def dict_state():
    s = DictState()
    s.load()
    return s


@pytest.fixture
def gzip_state(tmp_path):
    from dataclasses import fields
    from datetime import datetime

    s = GzipState(str(tmp_path / "test.gz"))
    s.load()

    some_date = datetime(2000, 1, 1, 0, 0, 0)

    i = 0
    for expires in [None, some_date]:
        for modified in [None, some_date]:
            for etag in [None, "etag"]:
                e = s.get(f"key{i}")
                e.expires = expires
                e.modified = modified
                e.etag = etag
                i = i + 1

    s.save()
    return s


def test_get_creates_new_item_if_missing(dict_state):
    assert dict_state.get("new")


def test_get_retrives_existing_item(dict_state):
    expected = dict_state.get("key")

    assert dict_state.get("key") == expected


def test_gzip_load_with_nonexistent_file_loads_empty(tmp_path):
    s = GzipState(str(tmp_path / "nonexistent.gz"))

    s.load()

    assert s.store == {}


def test_gzip_load_works(gzip_state):
    expected = gzip_state.store
    gzip_state.store = {}
    gzip_state.load()

    assert expected
    assert gzip_state.store == expected


def test_gzip_save_is_atomic(gzip_state, monkeypatch):
    gzip_state.store = "invalid thing"
    with pytest.raises(AttributeError):
        gzip_state.save()

    gzip_state.load()
    assert gzip_state.store


def test_malformed_date_is_sound():
    with pytest.raises(ValueError):
        StateItem.from_csv(
            key="",
            expires="invalid date",
            modified="invalid date",
            etag="",
        )
