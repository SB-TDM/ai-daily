"""Atomic local storage and a process-scoped generation lock."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile


class GenerationBusy(RuntimeError):
    pass


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as file:
            temporary = Path(file.name)
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_json(path, value):
    atomic_write(path, json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8"))


@contextmanager
def generation_lock(root):
    path = Path(root) / "data" / "generation.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Leave the lock file in place: deleting it could let processes lock different files.
    with open(path, "a+b") as file:
        if os.fstat(file.fileno()).st_size == 0:
            file.write(b"0")
            file.flush()
        file.seek(0)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise GenerationBusy("Generation in progress") from None
            try:
                yield
            finally:
                file.seek(0)
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try:
                fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise GenerationBusy("Generation in progress") from None
            try:
                yield
            finally:
                fcntl.flock(file.fileno(), fcntl.LOCK_UN)
