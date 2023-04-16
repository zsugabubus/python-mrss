from mrss._maildir import *
from mrss._state import *
import pytest
from mailbox import NoSuchMailboxError


def test_maildir_creates_new_directory_structure(tmp_path):
    assert Maildir(path=str(tmp_path / "x"), state=DictState())


def test_maildir_does_not_create_new_directory_structure(tmp_path):
    with pytest.raises(NoSuchMailboxError):
        Maildir(path=str(tmp_path / "x"), state=DictState(), create=False)


def test_maildir_creates_subdirectories_when_some_exists(tmp_path):
    os.mkdir(tmp_path / "x")
    os.mkdir(tmp_path / "x" / "new")
    assert Maildir(path=tmp_path / "x", state=DictState())


def test_maildir_creates_tail_directories_only(tmp_path):
    with pytest.raises(FileNotFoundError):
        Maildir(path=str(tmp_path / "no/such/dir"), state=DictState())
