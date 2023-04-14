# python-mrss

`python-mrss` is a Python library to manage RSS feeds and convert them to
email messages. Uses `feedparser` under the hood.

```py
from mrss import EasyMaildir

# State will be stored at ~/Mail/feeds/state.gz.
with EasyMaildir('~/Mail/feeds') as m:
    m.url('http://example.com/feed.rss')
    m.shell(
        # Identifier.
        key='bla',
        # Shell command.
        cmd='./my/feed/generator',
    )
    m.url(
        # Custom From header.
        name='GitHub',
        # URL to use.
        url='https://github.com/me.private.atom?token=xxx',
        # Override server returned expiration date.
        expires=timedelta(hours=12),
        # Disable threading.
        reply_to=False,
        # User-Agent can be overriden here or with `EasyMaildir.USER_AGENT` globally.
        user_agent="..."
    )

    # `EasyMaildir` extends `SitesMixin` that provides some common sources.
    m.github_commits('user/repo')
    m.youtube('UCr6FkKB3PzACAysFy0RVrzg')
```
