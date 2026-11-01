from transcription import Note, cache_key, is_url


def test_is_url_detects_links():
    assert is_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert is_url("http://youtu.be/dQw4w9WgXcQ")


def test_is_url_rejects_plain_search_terms():
    assert not is_url("bohemian rhapsody queen")
    assert not is_url("let it be - the beatles")


def test_cache_key_is_stable_and_case_insensitive():
    assert cache_key("Let It Be") == cache_key("  let it be  ")


def test_cache_key_differs_for_different_queries():
    assert cache_key("Let It Be") != cache_key("Hey Jude")


def test_note_to_dict_rounds_and_serializes():
    note = Note(pitch=60, start=1.23456, end=1.98765, velocity=0.5)
    assert note.to_dict() == {"pitch": 60, "start": 1.235, "end": 1.988, "velocity": 0.5}
