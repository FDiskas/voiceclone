"""The MPS memory cap must set both watermark ratios.

PyTorch's MPS allocator requires low <= high and defaults the low watermark to
1.4. Capping only the high ratio below 1.4 makes PyTorch abort with
"invalid low watermark ratio 1.4" before the model can load.
"""

import os

import pytest

from app.engine.omnivoice_engine import OmniVoiceEngine

_HIGH = "PYTORCH_MPS_HIGH_WATERMARK_RATIO"
_LOW = "PYTORCH_MPS_LOW_WATERMARK_RATIO"


@pytest.fixture(autouse=True)
def _clean_env():
    saved = {k: os.environ.get(k) for k in (_HIGH, _LOW)}
    for k in (_HIGH, _LOW):
        os.environ.pop(k, None)
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _engine(*, device_map="mps", ratio=0.8):
    return OmniVoiceEngine(
        model_id="x",
        device_map=device_map,
        dtype="auto",
        mps_high_watermark_ratio=ratio,
    )


def test_cap_pins_low_watermark_to_high():
    _engine(ratio=0.8)._apply_mps_memory_cap()
    assert os.environ[_HIGH] == "0.8"
    # Low must be <= high, never the 1.4 default that triggers the abort.
    assert float(os.environ[_LOW]) <= float(os.environ[_HIGH])


def test_low_follows_user_high_override():
    os.environ[_HIGH] = "0.5"  # explicit user override wins for high
    _engine(ratio=0.8)._apply_mps_memory_cap()
    assert os.environ[_HIGH] == "0.5"
    assert os.environ[_LOW] == "0.5"


def test_no_op_off_mps():
    _engine(device_map="cpu")._apply_mps_memory_cap()
    assert _HIGH not in os.environ
    assert _LOW not in os.environ


def test_no_op_when_disabled():
    _engine(ratio=0.0)._apply_mps_memory_cap()
    assert _HIGH not in os.environ
    assert _LOW not in os.environ
