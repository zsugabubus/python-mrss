from ._maildir import Maildir
from ._state import GzipState
from datetime import timedelta
import os.path


class SitesMixin:
    def youtube(
        self,
        channel: str,
        *,
        expires=timedelta(hours=12),
        **kwargs,
    ):
        return self.url(
            url=f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}",
            expires=expires,
            **kwargs,
        )

    def gitlab_commits(
        self,
        repo: str,
        *,
        branch="master",
        name: str = None,
        expires=timedelta(3),
        reply_to=False,
        **kwargs,
    ):
        return self.url(
            name=name or f"{repo}:{branch} commits",
            url=f"https://gitlab.com/{repo}/commits/{branch}?format=atom",
            expires=expires,
            reply_to=reply_to,
            **kwargs,
        )

    def github_commits(
        self,
        repo: str,
        *,
        branch="master",
        name: str = None,
        expires=timedelta(3),
        reply_to=False,
        **kwargs,
    ):
        return self.url(
            name=name or f"{repo}:{branch} commits",
            url=f"https://github.com/{repo}/commits/{branch}.atom",
            expires=expires,
            reply_to=reply_to,
            **kwargs,
        )

    def github_releases(
        self,
        repo: str,
        *,
        name: str = None,
        expires=timedelta(7),
        reply_to=False,
        **kwargs,
    ):
        return self.url(
            name=name or f"{repo} releases",
            url=f"https://github.com/{repo}/releases.atom",
            expires=expires,
            reply_to=reply_to,
            **kwargs,
        )

    def reddit_submitted(
        self,
        user: str,
        *,
        name: str = None,
        expires=timedelta(hours=12),
        reply_to=False,
        **kwargs,
    ):
        return self.url(
            name=name or user,
            url=f"https://www.reddit.com/user/{user}/submitted.rss",
            expires=expires,
            reply_to=reply_to,
            **kwargs,
        )

    def blog(
        self,
        url: str,
        *,
        expires=timedelta(7),
        reply_to=False,
        **kwargs,
    ):
        return self.url(
            url,
            expires=expires,
            reply_to=reply_to,
            **kwargs,
        )


class UserAgentMixin:
    USER_AGENT = None

    def url(self, *args, user_agent: str | None = None, **kwargs):
        super().url(
            *args,
            user_agent=user_agent or self.USER_AGENT,
            **kwargs,
        )


class EasyMaildir(SitesMixin, UserAgentMixin, Maildir):
    def __init__(self, tilde_path: str, /, *, statefile: str = "state.gz"):
        path = os.path.expanduser(tilde_path)
        super().__init__(
            path=path,
            state=GzipState(
                filename=os.path.normpath(os.path.join(path, statefile)),
            ),
        )
