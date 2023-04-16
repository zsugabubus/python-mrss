from mrss._mixins import *
from mrss._state import *
from unittest.mock import Mock, patch
import pytest


@pytest.fixture
def easy(tmp_path):
    return EasyMaildir(str(tmp_path))


def feed_data(generation):
    from xml.etree.ElementTree import Element, SubElement, tostring

    rss = Element("rss")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = "Feed Title"
    SubElement(channel, "link").text = "http://example.com/path"

    def generate_entry(pubDate: str):
        item = SubElement(channel, "item")
        SubElement(item, "pubDate").text = pubDate
        SubElement(item, "title").text = f"Entry Title"
        SubElement(
            item, "guid", isPermaLink="true"
        ).text = f"http://example.com/entry/{pubDate}"
        SubElement(item, "description").text = "Description"

    match generation:
        case 0:
            pass
        case 1:
            generate_entry("2000-01-01")  # NEW
        case 2:
            generate_entry("2000-01-01")  # OLD
            generate_entry("2003-01-01")  # NEW
            generate_entry("2002-01-01")  # NEW
        case 3:
            generate_entry("2001-01-01")  # IGNORE
            generate_entry("2002-01-01")  # OLD
            generate_entry("2004-01-01")  # NEW
        case 4:
            generate_entry("2001-01-01")  # IGNORE
        case _:
            raise ValueError  # pragma: no cover

    return tostring(
        rss,
        encoding="utf-8",
        xml_declaration=True,
    )


@pytest.fixture
def static_feed():
    mock = Mock()
    mock.return_value = feed_data(1)
    return mock


@pytest.fixture
def dynamic_feed():
    mock = Mock(side_effect=map(feed_data, range(0, 5)))
    return mock


@pytest.mark.parametrize(
    "reply_to, expected_count",
    (
        (False, 1),
        (True, 2),
    ),
)
def test_reply_to_creates_root_email(reply_to, expected_count, easy, static_feed):
    with easy as m:
        m.parse(key="key", data=static_feed, reply_to=reply_to)

    assert len([*m.mailbox.keys()]) == expected_count


def test_expires_works(easy, static_feed):
    with easy as m:
        m.parse(key="key", data=static_feed, expires=timedelta(1))
        m.parse(key="key", data=static_feed)

        assert static_feed.call_count == 1


def test_user_agent_works(easy, monkeypatch):
    test_url = "https://0.0.0.0:0/invalid/feed.rss"

    with easy as m:
        import feedparser

        feedparser.USER_AGENT = "default"

        original = feedparser.parse

        def mock(*args, **kwargs):
            assert feedparser.USER_AGENT == expected_user_agent
            return original(*args, **kwargs)

        monkeypatch.setattr(feedparser, "parse", mock)

        expected_user_agent = "test assert"
        with pytest.raises(AssertionError):
            m.url(test_url)

        expected_user_agent = "default"
        m.url(test_url)

        expected_user_agent = "UserAgentMixin"
        m.USER_AGENT = expected_user_agent
        m.url(test_url)

        expected_user_agent = "parameter"
        m.url(test_url, user_agent=expected_user_agent)


def test_messages_are_not_updated(easy, static_feed):
    with easy as m:
        m.parse(key="key", data=static_feed)

        assert len([*m.mailbox.keys()]) == 2

        # Message-IDs are cached internally so it works.
        for key in m.mailbox.keys():
            m.mailbox.discard(key)

        m.parse(key="another-key", data=static_feed)

        assert static_feed.call_count == 2
        assert len([*m.mailbox.keys()]) == 0


@pytest.mark.parametrize("reply_to", (True, False))
def test_feed_update_works(reply_to, easy, dynamic_feed):
    for new_count in (0, 1, 2, 1, 0):
        feed_message = 1 if reply_to and new_count > 0 else 0
        expected_count = feed_message + new_count

        with easy as m:
            m.parse(key="key", data=dynamic_feed, reply_to=reply_to)

            assert len([*m.mailbox.keys()]) == expected_count

            for key, msg in m.mailbox.iteritems():
                assert msg.get_flags() == ""
                m.mailbox.discard(key)


def test_state_saved_on_exit(easy, static_feed):
    with patch.object(easy.state, "save") as save:
        with easy as m:
            m.parse(key="key", data=static_feed)

        assert save.call_count == 1


def test_state_not_saved_on_error(easy, static_feed):
    with (
        patch.object(easy.state, "save") as save,
        patch.object(easy.mailbox, "unlock") as unlock,
    ):
        with pytest.raises(RuntimeError):
            with easy as m:
                m.parse(key="key", data=Mock(side_effect=RuntimeError))

        assert unlock.called
        assert not save.called


def test_state_not_saved_when_not_changed(easy, static_feed):
    with easy as m:
        m.parse(key="key", data=static_feed, expires=timedelta(1))

    with (
        patch.object(easy.state, "save") as save,
        patch.object(easy.mailbox, "unlock") as unlock,
    ):
        with easy as m:
            m.parse(key="key", data=static_feed)

        assert unlock.called
        assert not save.called
