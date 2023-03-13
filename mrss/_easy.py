from ._maildir import Maildir
from ._state import GzipState
from datetime import datetime, timedelta
import os.path

class SitesMixin:
	def youtube(
		self,
		channel: str,
		*,
		name: str,
	):
		self.url(
			name=name,
			url=f'https://www.youtube.com/feeds/videos.xml?channel_id={channel}',
			expires=timedelta(hours=12),
		)

	def gitlab_commits(
		self,
		repo: str,
		*,
		branch: str = 'master',
	):
		self.url(
			name=f'{repo}:{branch} commits',
			url=f'https://gitlab.com/{repo}/commits/{branch}?format=atom',
			expires=timedelta(3),
			reply_to=False,
		)

	def github_commits(
		self,
		repo: str,
		*,
		branch: str = 'master',
	):
		self.url(
			name=f'{repo}:{branch} commits',
			url=f'https://github.com/{repo}/commits/{branch}.atom',
			expires=timedelta(3),
			reply_to=False,
		)

	def github_releases(self, repo: str):
		self.url(
			name=f'{repo} releases',
			url=f'https://github.com/{repo}/releases.atom',
			expires=timedelta(7),
			reply_to=False,
		)

	def reddit_submitted(
		self,
		user: str,
		*,
		expires: timedelta = timedelta(hours=12),
	):
		self.url(
			name=user,
			url=f'https://www.reddit.com/user/{user}/submitted.rss',
			expires=expires,
			reply_to=False,
		)

	def blog(
		self,
		url: str,
		*,
		name: str = None,
	):
		self.url(
			url,
			name=name,
			expires=timedelta(7),
			reply_to=False,
		)

class UserAgentMixin:
	USER_AGENT = None

	def url(self, *args, **kwargs):
		super().url(
			user_agent=self.USER_AGENT,
			*args,
			**kwargs,
		)

class EasyMaildir(SitesMixin, UserAgentMixin, Maildir):
	def __init__(
		self,
		tilde_path: str,
		/,
		*,
		statefile: str = 'state.gz'
	):
		path = os.path.expanduser(tilde_path)
		super().__init__(
			path=path,
			state=GzipState(
				filename=os.path.normpath(os.path.join(path, statefile)),
			),
		)
