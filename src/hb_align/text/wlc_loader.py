"""Westminster Leningrad Codex loader utilities (T007).

Parses the normalized JSONL bundle into `TextChapter` structures that downstream
alignment code can consume. The bundle is too large to ship in this repository,
so this loader also works against the bundled sample file to keep CI green.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Mapping, Tuple

from hb_align.text import transliterator as _transliterator

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_WLC_ROOT = _REPO_ROOT / "resources" / "wlc"
_DEFAULT_VERSION = "wlc-2023.09"

_PROFILES = None


@dataclass(frozen=True)
class WordToken:
    index: int
    hebrew: str
    translit: str
    ipa_modern: str
    ipa_ashkenazi: str
    ipa_sephardi: str


@dataclass(frozen=True)
class VerseTokens:
    verse: str
    tokens: Tuple[WordToken, ...]


@dataclass(frozen=True)
class TextChapter:
    book: str
    chapter: int
    verses: Tuple[VerseTokens, ...]
    text_version: str = _DEFAULT_VERSION

    @property
    def word_count(self) -> int:
        return sum(len(verse.tokens) for verse in self.verses)

    def iter_words(self) -> Iterator[WordToken]:
        for verse in self.verses:
            yield from verse.tokens


def load_chapter(
    book: str,
    chapter: int,
    *,
    root: Path | str | None = None,
    text_version: str | None = None,
) -> TextChapter:
    """Load a single chapter from the WLC bundle as a TextChapter."""

    root_path = Path(root) if root else _DEFAULT_WLC_ROOT
    chapter_path = _resolve_chapter_path(book, chapter, root_path)
    verses = list(_parse_chapter_file(chapter_path))
    if not verses:
        raise ValueError(f"No verses found in {chapter_path}")
    actual_book = verses[0][0]
    actual_chapter = verses[0][1]
    verse_payloads = [entry[2] for entry in verses]
    verse_objs = tuple(
        VerseTokens(
            verse=payload["verse"],
            tokens=tuple(_build_word_token(token) for token in payload.get("tokens", [])),
        )
        for payload in verse_payloads
    )
    version = text_version or _DEFAULT_VERSION
    return TextChapter(
        book=actual_book or book,
        chapter=int(actual_chapter or chapter),
        verses=verse_objs,
        text_version=version,
    )


def iter_chapters(root: Path | str | None = None) -> Iterator[TextChapter]:
    """Yield every chapter found under the given WLC root directory."""

    root_path = Path(root) if root else _DEFAULT_WLC_ROOT
    for path in sorted(root_path.glob("*.jsonl")):
        book, chapter = _infer_book_chapter_from_filename(path.name)
        if book and chapter:
            yield load_chapter(book, chapter, root=root_path)


def _resolve_chapter_path(book: str, chapter: int, root: Path) -> Path:
    slug = book.lower().replace(" ", "-")
    candidates = [
        root / f"{slug}-{chapter:03}.jsonl",
        root / f"sample_{slug}-{chapter:03}.jsonl",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Could not locate WLC chapter for {book} {chapter} under {root}. "
        "Run scripts/verify_wlc.py after installing the bundle."
    )


def _parse_chapter_file(path: Path) -> Iterator[Tuple[str, int, Mapping[str, object]]]:
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)
            yield payload.get("book"), int(payload.get("chapter", 0)), payload


def _build_word_token(token_payload: Mapping[str, object]) -> WordToken:
    translit = token_payload.get("translit")
    ipa_modern = token_payload.get("ipa_modern")
    ipa_ashkenazi = token_payload.get("ipa_ashkenazi")
    ipa_sephardi = token_payload.get("ipa_sephardi")
    if not (translit and ipa_modern and ipa_ashkenazi and ipa_sephardi):
        translit, ipa_modern, ipa_ashkenazi, ipa_sephardi = _transliterate_token(
            token_payload.get("hebrew", ""), translit
        )
    return WordToken(
        index=int(token_payload.get("index", 0)),
        hebrew=str(token_payload.get("hebrew", "")),
        translit=str(translit),
        ipa_modern=str(ipa_modern),
        ipa_ashkenazi=str(ipa_ashkenazi),
        ipa_sephardi=str(ipa_sephardi),
    )


def _transliterate_token(hebrew: str, existing_translit: str | None) -> Tuple[str, str, str, str]:
    global _PROFILES
    if _PROFILES is None:
        _PROFILES = _transliterator.load_pronunciation_profiles()
    result = _transliterator.transliterate_word(hebrew, profiles=_PROFILES)
    translit = existing_translit or result.translit
    return (
        translit,
        result.ipa_by_profile.get("modern", ""),
        result.ipa_by_profile.get("ashkenazi", ""),
        result.ipa_by_profile.get("sephardi", ""),
    )


def _infer_book_chapter_from_filename(name: str) -> Tuple[str | None, int | None]:
    slug = name.replace("sample_", "").replace(".jsonl", "")
    if "-" not in slug:
        return None, None
    book_slug, chapter_str = slug.rsplit("-", 1)
    try:
        chapter = int(chapter_str)
    except ValueError:
        return None, None
    book = book_slug.replace("-", " ").title()
    return book, chapter


__all__ = [
    "WordToken",
    "VerseTokens",
    "TextChapter",
    "load_chapter",
    "iter_chapters",
]
