from typing import Protocol


class Worker(Protocol):
    async def start(self): ...


class Cancellable(Protocol):
    def cancel(self): ...


class CancellableWorker(Worker, Cancellable): ...
