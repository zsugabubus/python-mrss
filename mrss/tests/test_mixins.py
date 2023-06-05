from mrss._mixins import *
import pytest


SPEC = [
    (
        "youtube",
        dict(
            channel="channel",
        ),
    ),
    (
        "gitlab_commits",
        dict(
            repo="repo",
            branch="branch",
        ),
    ),
    (
        "github_commits",
        dict(
            repo="repo",
            branch="branch",
        ),
    ),
    (
        "github_releases",
        dict(
            repo="repo",
        ),
    ),
    (
        "reddit_submitted",
        dict(
            user="user",
        ),
    ),
    (
        "blog",
        dict(
            url="url",
        ),
    ),
]


@pytest.mark.parametrize("name, args", SPEC)
@pytest.mark.parametrize(
    "reply_to",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "expires",
    [
        timedelta(days=1),
        timedelta(days=0),
    ],
)
def test_mixins(name, args, reply_to, expires):
    expected_reply_to = reply_to
    expected_expires = expires
    expected_name = "Test name"
    expected_custom_arg = "Test custom"

    class TestAll(SitesMixin):
        def url(self, url, *, expires, reply_to, custom_arg, name):
            assert url
            assert name == expected_name
            assert reply_to == expected_reply_to
            assert expires == expected_expires
            assert custom_arg == expected_custom_arg
            return "url return"

    assert (
        getattr(TestAll(), name)(
            **args,
            reply_to=expected_reply_to,
            expires=expected_expires,
            custom_arg=expected_custom_arg,
            name=expected_name
        )
        == "url return"
    )

    class TestOptional(SitesMixin):
        def url(self, url, *, expires, reply_to=None, name=None):
            pass

    getattr(TestOptional(), name)(**args)


def test_mixins_spec():
    actually_tested = set(x[0] for x in SPEC)
    to_be_testsed = set(x for x in SitesMixin.__dict__ if not x.startswith("__"))

    assert actually_tested == to_be_testsed
