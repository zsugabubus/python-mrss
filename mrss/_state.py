from abc import ABC, abstractmethod
from operator import attrgetter
from pathlib import Path
import csv
import gzip
import os
from dataclasses import asdict, dataclass, fields

@dataclass(slots=True)
class StateItem:
	key: str
	modified: str | None = None
	expires: str | None = None
	etag: str | None = None

class State(ABC):
	@abstractmethod
	def load(self): pass

	@abstractmethod
	def save(self): pass

	@abstractmethod
	def get(self): pass

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
	FIELD_NAMES = [f.name for f in fields(StateItem)]

	class TSVDialect(csv.Dialect):
		"""Unix-y CSV format."""
		delimiter = '\t'
		quoting = csv.QUOTE_NONE
		escapechar = '\\'
		lineterminator = '\n'

	def __init__(self, filename: Path):
		super().__init__()
		self.filename = filename

	def load(self):
		super().load()
		try:
			with gzip.open(self.filename, mode='rt', newline='') as f:
				reader = csv.DictReader(
					f,
					dialect=self.TSVDialect,
				)
				self.store = {
					row['key']: StateItem(**row)
					for row in reader
				}
		except FileNotFoundError:
			pass

	def save(self):
		tmp = self.filename + '~'
		with gzip.open(tmp, mode='wt', newline='') as f:
			writer = csv.DictWriter(
				f,
				fieldnames=self.FIELD_NAMES,
				dialect=self.TSVDialect,
			)

			writer.writeheader()
			for row in sorted(
				self.store.values(),
				key=attrgetter('key'),
			):
				writer.writerow(asdict(row))
		os.rename(tmp, self.filename)
		super().save()
