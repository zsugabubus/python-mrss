from ._mailbox import Mailbox
from pathlib import Path
import mailbox
import os


class Maildir(Mailbox):
    def __init__(self, *, path: Path, create: bool = True, **kwargs):
        if create:
            # Maildir([create=True]) creates subdirs only if path does not exist.
            for subdir in ["cur", "new", "tmp"]:
                try:
                    os.mkdir(os.path.join(path, subdir), 0o700)
                except FileExistsError:
                    pass
                except FileNotFoundError:
                    pass
        super().__init__(
            mailbox=mailbox.Maildir(path, create=create),
            **kwargs,
        )
