import json
from pathlib import Path

import pytest

from hb_align.text.wlc_loader import (
    TextChapter,
    iter_chapters,
    load_chapter,
)


TEST_ROOT = Path(__file__).resolve().parents[3]
WLC_SAMPLE_ROOT = TEST_ROOT / "resources" / "wlc"


def test_load_chapter_from_sample_bundle():
    chapter = load_chapter("Genesis", 1)
    assert isinstance(chapter, TextChapter)
    assert chapter.book == "Genesis"
    assert chapter.chapter == 1
    assert chapter.word_count == 5
    verses = list(chapter.verses)
    assert verses[0].verse == "1:1"
    assert verses[1].tokens[0].hebrew == "והארץ"


def test_iter_chapters_detects_files():
    chapters = list(iter_chapters(root=WLC_SAMPLE_ROOT))
    assert len(chapters) == 1
    assert chapters[0].book == "Genesis"


def test_loader_transliterates_when_fields_missing(tmp_path):
    payload = {
        "book": "Exodus",
        "chapter": 2,
        "verse": "2:1",
        "tokens": [{"index": 0, "hebrew": "שלום"}],
    }
    file_path = tmp_path / "exodus-002.jsonl"
    file_path.write_text(json.dumps(payload), encoding="utf-8")
    chapter = load_chapter("Exodus", 2, root=tmp_path)
    token = next(chapter.iter_words())
    assert token.translit
    assert token.ipa_modern
    assert token.ipa_ashkenazi
    assert token.ipa_sephardi


def test_missing_chapter_raises():
    with pytest.raises(FileNotFoundError):
        load_chapter("Exodus", 99, root=WLC_SAMPLE_ROOT)
