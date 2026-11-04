from contextlib import contextmanager
from pathlib import Path


class ContainmentBusyError(Exception):
    pass


class ContainmentLock:
    def __init__(self, lock_path: str):
        self.lock_path = Path(lock_path)
        self.acquired = False

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.lock_path.mkdir()
        except FileExistsError as exc:
            raise ContainmentBusyError(
                "Another containment operation may be active. "
                "Manual inspection is required."
            ) from exc

        self.acquired = True

    def release(self) -> None:
        if not self.acquired:
            return

        self.lock_path.rmdir()
        self.acquired = False

    @contextmanager
    def hold(self):
        self.acquire()
        try:
            yield
        finally:
            self.release()
