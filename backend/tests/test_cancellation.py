"""Cooperative cancellation: tokens, service stop-between-units, the watcher."""

import asyncio
import time

import pytest

from app.api.cancellation import run_cancelling_on_disconnect
from app.cancellation import CancellationToken, OperationCancelled, raise_if_cancelled
from app.engine.base import SynthesisResult
from app.services.synthesis_service import SynthesisService


def test_raise_if_cancelled_is_a_noop_until_cancelled():
    token = CancellationToken()
    raise_if_cancelled(token)  # not cancelled: no raise
    raise_if_cancelled(None)  # no token: no raise

    token.cancel()
    assert token.cancelled
    with pytest.raises(OperationCancelled):
        raise_if_cancelled(token)


def _create_profile(profile_service):
    return profile_service.create(
        name="My Voice",
        language="en",
        transcript="This is a reference recording.",
        audio_bytes=b"fake-audio-bytes",
        original_filename="recording.webm",
    )


# Two sentences long enough to stay separate after segmentation.
_TWO_SENTENCES = ("word " * 40).strip() + ". " + ("alpha " * 40).strip() + "."


class _CancelAfterFirstEngine:
    """Cancels its token on the first call, to prove rendering stops between
    sentences rather than running them all."""

    def __init__(self, token: CancellationToken) -> None:
        self._token = token
        self.calls = 0

    def synthesize(self, request) -> SynthesisResult:
        import numpy as np

        self.calls += 1
        self._token.cancel()
        return SynthesisResult(samples=np.zeros(8, dtype=np.float32), sample_rate=24_000)


def test_whole_synthesis_stops_between_sentences_when_cancelled(profile_service):
    profile = _create_profile(profile_service)
    token = CancellationToken()
    engine = _CancelAfterFirstEngine(token)
    service = SynthesisService(profile_service, engine)

    with pytest.raises(OperationCancelled):
        service.synthesize(profile.id.value, _TWO_SENTENCES, cancel=token)

    # The second sentence was never sent to the engine.
    assert engine.calls == 1


def test_transcription_honours_a_cancelled_token(transcription_service):
    token = CancellationToken()
    token.cancel()
    with pytest.raises(OperationCancelled):
        transcription_service.transcribe(b"bytes", original_filename="clip.wav", cancel=token)


class _FakeRequest:
    """Reports connected for the first `connected_polls`, then disconnected."""

    def __init__(self, connected_polls: int) -> None:
        self._remaining = connected_polls

    async def is_disconnected(self) -> bool:
        if self._remaining > 0:
            self._remaining -= 1
            return False
        return True


def test_watcher_returns_result_when_client_stays():
    result = asyncio.run(
        run_cancelling_on_disconnect(_FakeRequest(connected_polls=10_000), lambda token: "done")
    )
    assert result == "done"


def test_watcher_cancels_work_when_client_disconnects():
    def work(token: CancellationToken) -> str:
        # Long-running work that polls the token at a tight loop boundary.
        for _ in range(10_000):
            raise_if_cancelled(token)
            time.sleep(0.01)
        return "done"

    with pytest.raises(OperationCancelled):
        asyncio.run(run_cancelling_on_disconnect(_FakeRequest(connected_polls=0), work))
