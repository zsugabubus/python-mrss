from ._easy import SitesMixin, UserAgentMixin, EasyMaildir
from ._mailbox import Mailbox
from ._maildir import Maildir
from ._state import State, DictState, GzipState

from datetime import datetime
import feedparser

feedparser.registerDateHandler(
	lambda s: datetime.strptime(s, '%d %b %Y %Z').timetuple()
)
