import pytest

from hb_align.text.transliterator import (
    TransliterationResult,
    load_pronunciation_profiles,
    transliterate_tokens,
    transliterate_word,
)


@pytest.fixture(scope="module")
def profiles():
    return load_pronunciation_profiles()


def test_transliterate_word_basic(profiles):
    result = transliterate_word("שלום", profiles=profiles)
    assert isinstance(result, TransliterationResult)
    assert result.translit.startswith("sh")
    assert result.ipa_by_profile
    assert "modern" in result.ipa_by_profile


def test_transliterate_tokens_batch(profiles):
    inputs = ["בראשית", "ברא"]
    batch = list(transliterate_tokens(inputs))
    assert len(batch) == 2
    assert all(isinstance(item, TransliterationResult) for item in batch)
    assert batch[0].normalized.startswith("בראשית")


def test_profiles_fallback(monkeypatch):
    # Force loader to read missing file to exercise fallback
    monkeypatch.setattr(
        "hb_align.text.transliterator._DEFAULT_CONF_PATH",
        "c:/does/not/exist.yml",
    )
    profiles = load_pronunciation_profiles(path="c:/does/not/exist.yml")
    assert "modern" in profiles
    assert profiles["modern"].to_ipa("shema")
