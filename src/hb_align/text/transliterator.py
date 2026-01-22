"""Transliteration and pronunciation helpers (T006).

The implementation intentionally keeps the rules lightweight so Phase 2 work can
progress without the final linguistic heuristics. Rules can be refined later by
extending the mapping tables or reading richer data from research artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Mapping
import unicodedata

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CONF_PATH = _REPO_ROOT / "resources" / "confidence.yml"

# Consonant → ISO-259-ish transliteration fragments.
_CONSONANT_MAP: Mapping[str, str] = {
    "א": "e",
    "ב": "be",
    "ג": "g",
    "ד": "d",
    "ה": "h",
    "ו": "v",
    "ז": "z",
    "ח": "kh",
    "ט": "t",
    "י": "i",
    "כ": "k",
    "ך": "k",
    "ל": "l",
    "מ": "m",
    "ם": "m",
    "נ": "n",
    "ן": "n",
    "ס": "s",
    "ע": "a",
    "פ": "p",
    "ף": "p",
    "צ": "ts",
    "ץ": "ts",
    "ק": "q",
    "ר": "r",
    "ש": "sh",
    "ת": "t",
}

# Characters to drop entirely (cantillation, punctuation, etc.).
_IGNORE_CHARS = {"\u200f", "\u200e", "'", '"', "`", "-", "־"}


@dataclass(frozen=True)
class PronunciationProfile:
    name: str
    ipa_map: Mapping[str, str]
    calibration_a: float
    calibration_b: float

    def to_ipa(self, transliteration: str) -> str:
        """Convert a transliteration string to IPA using the profile map."""

        ipa = transliteration
        for token in sorted(self.ipa_map, key=len, reverse=True):
            ipa = ipa.replace(token, self.ipa_map[token])
        return ipa


@dataclass(frozen=True)
class TransliterationResult:
    hebrew: str
    normalized: str
    translit: str
    ipa_by_profile: Mapping[str, str]


@lru_cache(maxsize=None)
def load_pronunciation_profiles(path: str | Path | None = None) -> Mapping[str, PronunciationProfile]:
    """Load pronunciation profiles from resources/confidence.yml (or fallback)."""

    conf_path = Path(path) if path else _DEFAULT_CONF_PATH
    data: Dict[str, PronunciationProfile] = {}
    if conf_path.exists():
        payload = yaml.safe_load(conf_path.read_text(encoding="utf-8")) or {}
        for name, section in (payload.get("profiles") or {}).items():
            ipa_map = section.get("ipa_map") or {}
            calib = section.get("calibration") or {}
            data[name] = PronunciationProfile(
                name=name,
                ipa_map=ipa_map,
                calibration_a=float(calib.get("a", 0.045)),
                calibration_b=float(calib.get("b", 2.8)),
            )
    if not data:
        data = {
            "modern": PronunciationProfile(
                name="modern",
                ipa_map={"sh": "ʃ", "kh": "x"},
                calibration_a=0.045,
                calibration_b=2.8,
            )
        }
    return data


def transliterate_word(word: str, *, profiles: Mapping[str, PronunciationProfile] | None = None) -> TransliterationResult:
    profiles = profiles or load_pronunciation_profiles()
    normalized = _normalize_hebrew(word)
    translit = _to_transliteration(normalized)
    ipa = {name: profile.to_ipa(translit) for name, profile in profiles.items()}
    return TransliterationResult(
        hebrew=word,
        normalized=normalized,
        translit=translit,
        ipa_by_profile=ipa,
    )


def transliterate_tokens(words: Iterable[str]) -> Iterable[TransliterationResult]:
    profiles = load_pronunciation_profiles()
    for word in words:
        yield transliterate_word(word, profiles=profiles)


def _normalize_hebrew(word: str) -> str:
    nfkd = unicodedata.normalize("NFKD", word)
    stripped = "".join(ch for ch in nfkd if not _is_diacritic(ch))
    cleaned = stripped.replace("\u05f3", "").replace("\u05f4", "")
    cleaned = "".join(ch for ch in cleaned if ch not in _IGNORE_CHARS)
    return cleaned


def _is_diacritic(ch: str) -> bool:
    return unicodedata.category(ch) in {"Mn", "Sk"}


def _to_transliteration(word: str) -> str:
    result: list[str] = []
    for idx, ch in enumerate(word):
        mapped = _CONSONANT_MAP.get(ch)
        if mapped:
            result.append(mapped)
        else:
            result.append(ch)
        if idx == 0 and ch in {"ב", "כ", "ל", "מ", "ש", "ו", "ה"}:
            result.append("e")
    translit = "".join(result)
    return translit.replace("ee", "e").replace("aa", "a")


__all__ = [
    "PronunciationProfile",
    "TransliterationResult",
    "load_pronunciation_profiles",
    "transliterate_word",
    "transliterate_tokens",
]
