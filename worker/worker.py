from typing import Protocol


class Worker(Protocol):
    async def start(self): ...


class Cancellable(Protocol):
    def cancel(self): ...

    @property
    def is_cancelled(self) -> bool: ...


class CancellableWorker(Worker, Cancellable): ...
