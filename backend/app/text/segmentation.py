"""Split text into sentence-sized chunks for streaming synthesis.

Each chunk is synthesized independently so the first one can start playing
while later chunks are still rendering. Sentences are merged up to a soft
character budget to avoid tiny, unnatural fragments.
"""

from __future__ import annotations

import re

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?。！？])\s+|\n+")
_SOFT_MAX_CHARS = 240


def split_into_sentences(text: str, soft_max_chars: int = _SOFT_MAX_CHARS) -> list[str]:
    """Break `text` into ordered, non-empty chunks at sentence boundaries."""
    pieces = (piece.strip() for piece in _SENTENCE_BOUNDARY.split(text))
    sentences = [piece for piece in pieces if piece]

    chunks: list[str] = []
    for sentence in sentences:
        if chunks and len(chunks[-1]) + len(sentence) + 1 <= soft_max_chars:
            chunks[-1] = f"{chunks[-1]} {sentence}"
        else:
            chunks.append(sentence)
    return chunks
