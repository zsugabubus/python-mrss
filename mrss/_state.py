from abc import ABC, abstractmethod
from operator import attrgetter
from pathlib import Path
import csv
import gzip
import os
from dataclasses import asdict, dataclass, fields
from email.utils import parsedate_to_datetime, format_datetime
from datetime import datetime
from typing import Optional


@dataclass(slots=True, kw_only=True)
class StateItem:
    key: str
    modified: Optional[str] = None
    expires: Optional[str] = None
    etag: Optional[str] = None

    @classmethod
    def from_csv(cls, key: str, modified: str, expires: str, etag: str):
        def parse_date(s: str) -> Optional[datetime]:
            if s:
                return parsedate_to_datetime(s)
            return None

        return cls(
            key=key,
            modified=parse_date(modified),
            expires=parse_date(expires),
            etag=etag or None,
        )

    def to_csv(self):
        def format_date(dt: Optional[datetime]) -> Optional[str]:
            if dt:
                return format_datetime(dt)
            return None

        return dict(
            key=self.key,
            modified=format_date(self.modified),
            expires=format_date(self.expires),
            etag=self.etag,
        )


class State(ABC):
    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def get(self):
        pass


class DictState(State):
    def load(self):
        self.store: dict[str, StateItem] = {}

    def get(self, key: str):
        row = self.store.get(key)
        if not row:
            row = StateItem(key=key)
            self.store[key] = row
        return row

    def save(self):
        pass


class GzipState(DictState):
    _FIELD_NAMES = [f.name for f in fields(StateItem)]

    class TSVDialect(csv.Dialect):
        """Unix-y CSV format."""

        delimiter = "\t"
        quoting = csv.QUOTE_NONE
        escapechar = "\\"
        lineterminator = "\n"

    def __init__(self, filename: Path):
        super().__init__()
        self.filename = filename

    def load(self):
        super().load()
        try:
            with gzip.open(self.filename, mode="rt", newline="") as f:
                reader = csv.DictReader(
                    f,
                    dialect=self.TSVDialect,
                )
                self.store = {row["key"]: StateItem.from_csv(**row) for row in reader}
        except FileNotFoundError:
            pass

    def save(self):
        tmp = self.filename + "~"
        with gzip.open(tmp, mode="wt", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=self._FIELD_NAMES,
                dialect=self.TSVDialect,
            )

            writer.writeheader()
            for item in sorted(
                self.store.values(),
                key=attrgetter("key"),
            ):
                writer.writerow(item.to_csv())
        os.rename(tmp, self.filename)
        super().save()
