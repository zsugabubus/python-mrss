from ._state import State
from ._utils import human_duration
from datetime import datetime, timedelta, timezone
from email.header import Header
from email.message import EmailMessage
from email.utils import formataddr, formatdate, parsedate_to_datetime
from hashlib import sha1
from time import mktime
from typing import Callable
from urllib.parse import urlparse
import feedparser
import logging
import mailbox
import re
import subprocess


class Mailbox:
    def __init__(
        self,
        *,
        mailbox: mailbox.Mailbox,
        state: State,
    ):
        self.mailbox = mailbox
        self.state = state
        self.log = logging.getLogger(type(self).__name__)

    def __enter__(self):
        self.mailbox.lock()
        self._msgid2key = None
        self._state_dirty = False
        self.state.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb, /):
        self.mailbox.flush()
        self.mailbox.unlock()
        self._msgid2key = None
        if exc_type is None and self._state_dirty:
            self.state.save()

    @staticmethod
    def _make_stable_msgid(left, right):
        left = sha1(left.encode()).hexdigest()[:10]
        return f"<{left}@{right}>"

    def url(
        self,
        url: str,
        **kwargs,
    ):
        return self.parse(
            key=url,
            data=lambda: url,
            **kwargs,
        )

    def shell(
        self,
        key: str,
        cmd: str,
        **kwargs,
    ):
        return self.parse(
            key=f"x-mrss:{key}",
            data=lambda: subprocess.check_output(
                [cmd],
                shell=True,
            ),
            **kwargs,
        )

    def parse(
        self,
        *,
        key: str,
        data: Callable[[], str],
        expires: timedelta = timedelta(),
        name: str = None,
        reply_to: bool = True,
        user_agent: str | None = None,
    ):
        now = datetime.now(timezone.utc)

        state = self.state.get(key)

        if x := state.expires:
            expires_in = (x - now).total_seconds()
            self.log.debug("%s: Expires in %s", key, human_duration(expires_in))
            if 0 < expires_in:
                return

        self._state_dirty = True

        saved_agent = feedparser.USER_AGENT
        try:
            feedparser.USER_AGENT = user_agent or saved_agent
            result = feedparser.parse(
                data(),
                etag=state.etag,
                modified=state.modified,
            )
        finally:
            feedparser.USER_AGENT = saved_agent

        if 400 <= (result.get("status") or 200):
            self.log.error("HTTP error %d: %s", result.status, key)

        feed = result.feed
        # Ensure we have some data (not a conditional GET).
        if result.entries:
            self._feed_host = urlparse(feed.link).hostname
            self._feed_msgid = self._make_stable_msgid(
                feed.get("id") or feed.link,
                self._feed_host,
            )
            self._from_hdr = formataddr(
                (name or feed.title, "feed@%s" % self._feed_host)
            )

            self._old_modified = state.modified
            self._modified = self._old_modified

            has_new = False
            for entry in result.entries:
                if msg := self._generate_entry_msg(entry, feed):
                    has_new = True
                    self._add_msg(msg)

            if has_new and reply_to:
                msg = self._generate_feed_msg(feed)
                self._add_msg(msg)

            if self._modified is not None:
                state.modified = self._modified

        state.etag = result.get("etag")

        ttl = timedelta(seconds=int(feed.get("ttl") or 0))
        state.expires = now + max(expires, ttl)
        if x := result.headers.get("expires"):
            try:
                state.expires = max(state.expires, parsedate_to_datetime(x))
            except ValueError as e:
                self.log.warn(e)

    def _generate_feed_msg(self, feed):
        msg = EmailMessage()
        msg["From"] = self._from_hdr
        msg["Message-ID"] = self._feed_msgid
        msg["Subject"] = feed.title
        msg["Link"] = feed.link
        if subtitle_detail := feed.get("subtitle_detail"):
            msg.set_content(
                subtitle_detail.value,
                subtype=subtitle_detail.type.split("/")[1],
                cte="8bit",
            )
        return msg

    def _generate_entry_msg(self, entry, feed):
        date_as_tv = mktime(
            entry.get("updated_parsed") or entry.get("published_parsed")
        )
        date = datetime.fromtimestamp(date_as_tv, tz=timezone.utc)

        if self._old_modified is not None and date <= self._old_modified:
            return

        self._modified = max(self._modified or date, date)

        msg = EmailMessage()
        msg["Received"] = "mrss; %s" % formatdate(localtime=True)
        msg["In-Reply-To"] = self._feed_msgid
        left = entry.get("id") or entry.get("link") or entry.title
        assert 5 < len(left)
        msg["Message-ID"] = self._make_stable_msgid(left, self._feed_host)
        msg["Date"] = formatdate(date_as_tv, localtime=True)
        msg["From"] = self._from_hdr
        msg["Subject"] = entry.title_detail.value.replace("\n", " ")
        if author := entry.get("author_detail") or feed.get("author_detail"):
            if href := author.get("href"):
                msg["Author"] = "%s <%s>" % (author.name, href)
            else:
                msg["Author"] = author.name
        msg["Link"] = entry.link
        if content := entry.get("content"):
            assert len(content) == 1
            content = content[0]
        else:
            content = entry.get("summary_detail") or {
                "value": entry.summary,
                "language": None,
                "type": (
                    "text/html"
                    if re.search("</[a-z]*>", entry.summary)
                    else "text/plain"
                ),
            }
        msg["Content-Language"] = content["language"] or feed.get("language")
        for tag in entry.get("tags") or []:
            msg["X-Category"] = tag.label or tag.term
        msg.set_content(
            content["value"],
            subtype=content["type"].split("/")[1],
            cte="8bit",
        )
        return msg

    def _update_msgids(self):
        self._msgid2key = {}
        for key, msg in self.mailbox.iteritems():
            self._msgid2key[msg["Message-ID"]] = key

    def _add_msg(self, msg):
        if self._msgid2key is None:
            self._update_msgids()
        msgid = msg["Message-ID"]
        if msgid not in self._msgid2key:
            self.log.debug("New: %s", msgid)
            self._msgid2key[msgid] = self.mailbox.add(msg)
