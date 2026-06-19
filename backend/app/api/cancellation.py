"""Run blocking work in a worker thread, cancelling it if the client leaves.

FastAPI's synchronous-style endpoints offload blocking work to a threadpool,
but a client that aborts its request (the user clicked "Stop") doesn't stop
that work — it runs to completion and the result is discarded, holding the
model/GPU the whole time. This helper bridges that gap: it watches the request
for disconnect and flips a `CancellationToken` the work polls, so the work
unwinds at its next loop boundary and frees resources promptly.
"""

from __future__ import annotations

import asyncio
from typing import Callable, TypeVar

from fastapi import Request
from starlette.concurrency import run_in_threadpool

from ..cancellation import CancellationToken

T = TypeVar("T")

# How often to check whether the client has gone away. Cancellation latency is
# bounded by this plus the time to reach the work's next loop boundary.
_POLL_SECONDS = 0.25


async def run_cancelling_on_disconnect(
    request: Request, work: Callable[[CancellationToken], T]
) -> T:
    """Run `work(token)` in a thread; cancel the token if the client disconnects.

    `work` must poll the token at its loop boundaries (see `raise_if_cancelled`)
    — the thread can't be killed, only asked to stop. Returns the work's result,
    or propagates whatever it raises (including `OperationCancelled` once it
    observes the cancellation).
    """
    token = CancellationToken()
    task = asyncio.ensure_future(run_in_threadpool(work, token))
    try:
        while not task.done():
            if await request.is_disconnected():
                token.cancel()
                break
            await asyncio.sleep(_POLL_SECONDS)
        return await task
    except BaseException:
        # The surrounding request was cancelled (e.g. shutdown). Signal the
        # worker and let it unwind so we don't orphan a running thread.
        token.cancel()
        await asyncio.gather(task, return_exceptions=True)
        raise
