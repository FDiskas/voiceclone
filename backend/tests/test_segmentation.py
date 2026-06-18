from app.text.segmentation import split_into_sentences


def test_splits_on_sentence_punctuation():
    assert split_into_sentences("Hello there. How are you? I am fine!") == [
        "Hello there. How are you? I am fine!"
    ]


def test_merges_short_sentences_up_to_budget():
    chunks = split_into_sentences("One. Two. Three.", soft_max_chars=10)
    assert chunks == ["One. Two.", "Three."]


def test_long_sentences_become_separate_chunks():
    text = "A" * 200 + ". " + "B" * 200 + "."
    chunks = split_into_sentences(text, soft_max_chars=240)
    assert len(chunks) == 2


def test_newlines_are_boundaries_and_blanks_dropped():
    assert split_into_sentences("Line one\n\nLine two", soft_max_chars=5) == [
        "Line one",
        "Line two",
    ]


def test_empty_text_yields_no_chunks():
    assert split_into_sentences("   ") == []
