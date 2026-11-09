"""Text Normalization & Preprocessing Utility for Speech Synthesis (TTS).

Preprocesses technical and AI-generated script narration text prior to speech synthesis.
Performs intelligent normalization to make code artifacts sound natural when spoken:
  1. Identifier formatting: Transforms camelCase, PascalCase, snake_case, and SCREAMING_CASE
     into natural spoken words (e.g. 'auth_middleware' -> 'auth middleware',
     'OrderProcessor' -> 'Order Processor', 'getUserById' -> 'get User By Id').
  2. File extension stripping: Strips technical extensions like .py, .ts, .tsx, .json, .yaml,
     .html, .css, .md, .go, .rs so TTS engines pronounce the file name naturally.
  3. Path normalization: Replaces directory slashes with natural pauses or spoken separators.
  4. Underscore normalization: Replaces underscores with spaces while preserving dunder
     pronunciations (e.g. '__init__' -> 'dunder init').
  5. Code artifact & symbol removal: Strips backticks, markdown markers, syntax symbols
     ({}, [], <>, #, @, $, |, *, ~), and emojis while preserving full Unicode scripts
     (Latin, Devanagari, Gujarati, Bengali, Tamil, Telugu, Kannada, Malayalam, Arabic,
     Chinese, Japanese, etc.) and speech punctuation (. , ? ! : - ').
  6. Multilingual phonetic expansion: Expands common technical acronyms (FastAPI, SQL, JSON,
     API, gRPC, JWT, CLI, UUID) for fluid playback across English, Indian, and world languages.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("text_cleaner")


# -----------------------------------------------------------------------------
# Regex Patterns
# -----------------------------------------------------------------------------

# File extensions commonly found in code tutorial scripts
FILE_EXTENSIONS = (
    r"py|tsx?|jsx?|json|ya?ml|html?|css|scss|sass|less|md|markdown|"
    r"rs|go|java|cpp|cxx|c|h|hpp|sql|sh|bash|zsh|bat|cmd|ps1|"
    r"toml|xml|env|lock|mod|sum|gradle|properties|ini|conf|cfg"
)

# Matches filename.ext (e.g., "order_service.py", "OrderList.tsx", "package.json")
FILE_EXT_REGEX = re.compile(
    rf"\b([a-zA-Z0-9_\u0900-\u0D7F\-]+)\.({FILE_EXTENSIONS})\b",
    re.IGNORECASE,
)

# Scene headings (e.g., "[Scene 1: Repository Overview]", "[Scene 2]")
SCENE_TAG_REGEX = re.compile(
    r"^\s*\[(?:Scene|Act|दृश्य|સીન|अध्याय|Capítulo|Scène|Szene|シーン|场景|المشهد)\s*([0-9a-zA-Z_\-:\s\u0900-\u0D7F]+)\]\s*$",
    re.IGNORECASE,
)

# Inline director notes (e.g., "[Visual: zoom into diagram]", "[Pause: 2s]")
DIRECTOR_NOTE_REGEX = re.compile(
    r"\[(?:Visual|Action|Camera|Note|Cut to|Music|Pause|Wait|Audio)[^\]]*\]",
    re.IGNORECASE,
)

# Markdown formatting
MARKDOWN_HEADER_REGEX = re.compile(r"^#+\s*", re.MULTILINE)
MARKDOWN_BOLD_ITALIC_REGEX = re.compile(r"(\*{1,3}|_{1,3})([^\*_]+)\1")
MARKDOWN_INLINE_CODE_REGEX = re.compile(r"`([^`]+)`")
MARKDOWN_BLOCKQUOTE_REGEX = re.compile(r"^>\s*", re.MULTILINE)
MARKDOWN_BULLET_REGEX = re.compile(r"^[\*\-\+]\s+", re.MULTILINE)

# Programming syntax & brackets (excluding standard grammatical punctuation)
SYNTAX_SYMBOLS_REGEX = re.compile(r"[\{\}\[\]\<\>\(\)\;\=\+\*\#\@\$\%\^\|\~\\]")

# URL pattern
URL_REGEX = re.compile(r"https?://[^\s/$.?#].[^\s]*", re.IGNORECASE)

# Common technical acronym phonetic pronunciations for clean audio
PHONETIC_EXPANSIONS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b__init__\.py\b", re.I), "dunder init dot py"),
    (re.compile(r"\b__init__\b", re.I), "dunder init"),
    (re.compile(r"\b__main__\b", re.I), "dunder main"),
    (re.compile(r"\b__pycache__\b", re.I), "dunder pycache"),
    (re.compile(r"\b\.__([a-zA-Z0-9_]+)__\b"), r" dunder \1 dunder "),
    (re.compile(r"\bFastAPI\b"), "Fast A P I"),
    (re.compile(r"\bPostgreSQL\b", re.I), "Postgres Q L"),
    (re.compile(r"\bPostgres\b", re.I), "Postgres"),
    (re.compile(r"\bgRPC\b"), "g R P C"),
    (re.compile(r"\bSQL\b"), "S Q L"),
    (re.compile(r"\bNoSQL\b", re.I), "No S Q L"),
    (re.compile(r"\bJSON\b", re.I), "Jason"),
    (re.compile(r"\bYAML\b", re.I), "yam-el"),
    (re.compile(r"\bAPI\b"), "A P I"),
    (re.compile(r"\bAPIs\b"), "A P I's"),
    (re.compile(r"\bRESTful\b", re.I), "Rest-ful"),
    (re.compile(r"\bCLI\b"), "C L I"),
    (re.compile(r"\bTTS\b"), "T T S"),
    (re.compile(r"\bUUID\b"), "U U I D"),
    (re.compile(r"\bJWT\b"), "J W T"),
    (re.compile(r"\bOAuth\b", re.I), "O-Auth"),
    (re.compile(r"\bCRUD\b"), "Crud"),
    (re.compile(r"\bAST\b"), "A S T"),
    (re.compile(r"\bGUI\b", re.I), "gooey"),
    (re.compile(r"\bCSS\b"), "C S S"),
    (re.compile(r"\bHTML\b"), "H T M L"),
    (re.compile(r"\bSDK\b"), "S D K"),
    (re.compile(r"\bSDKs\b"), "S D K's"),
    (re.compile(r"\bLLM\b"), "L L M"),
    (re.compile(r"\bLLMs\b"), "L L M's"),
    (re.compile(r"\bv([0-9]+)\.([0-9]+)\b"), r"version \1 point \2"),
]


# -----------------------------------------------------------------------------
# Text Normalization Implementation
# -----------------------------------------------------------------------------


class TextCleaner:
    """Enterprise text normalization service tailored for multilingual speech synthesis."""

    @classmethod
    def clean_for_tts(cls, text: str, language: Optional[str] = "en") -> str:
        """Execute the complete multi-stage cleaning pipeline on input script text.

        Args:
            text: Raw narration text, markdown script, or technical tutorial prose.
            language: Optional target language code (e.g. 'en', 'gu', 'hi', 'mr', 'es', 'fr').

        Returns:
            Pristine, natural spoken text ready for speech synthesis.
        """
        if not text or not text.strip():
            return ""

        s = text

        # 1. Strip visual director notes (e.g. [Visual: ...], [Pause: 2s])
        s = cls.strip_director_notes(s)

        # 2. Format scene headers so they read naturally as section titles
        s = cls.normalize_scene_headers(s)

        # 3. Strip URLs or normalize to spoken domain
        s = cls.normalize_urls(s)

        # 4. Strip file extensions from identifiers (e.g. "order_service.py" -> "order_service")
        s = cls.strip_file_extensions(s)

        # 5. Normalize file paths (e.g. "app/services/auth" -> "app services auth")
        s = cls.normalize_paths(s)

        # 6. Apply phonetic pronunciation normalizers for code acronyms
        s = cls.apply_phonetic_expansions(s)

        # 7. Split technical identifiers (camelCase, PascalCase, snake_case)
        s = cls.split_technical_identifiers(s)

        # 8. Clean markdown formatting and stray backticks
        s = cls.strip_markdown(s)

        # 9. Strip code syntax symbols while preserving speech punctuation & Unicode alphabets
        s = cls.remove_syntax_symbols(s)

        # 10. Normalize whitespace, dashes, and ellipses
        s = cls.normalize_whitespace_and_punctuation(s)

        return s.strip()

    # -------------------------------------------------------------------------
    # Modular Cleaning Stages
    # -------------------------------------------------------------------------

    @staticmethod
    def strip_director_notes(text: str) -> str:
        """Remove bracketed visual instructions, camera angles, and production cues."""
        return DIRECTOR_NOTE_REGEX.sub("", text)

    @staticmethod
    def normalize_scene_headers(text: str) -> str:
        """Convert bracketed scene headers like [Scene 1: Overview] into spoken titles."""
        lines = text.splitlines()
        cleaned_lines: List[str] = []
        for line in lines:
            match = SCENE_TAG_REGEX.match(line.strip())
            if match:
                # Retain as natural sentence: "Scene 1: Repository Overview."
                cleaned_lines.append(f"{match.group(0).strip('[]')}.")
            else:
                cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    @staticmethod
    def normalize_urls(text: str) -> str:
        """Replace URLs with clean verbalized text or domain names."""
        def _replace_url(match: re.Match) -> str:
            raw_url = match.group(0)
            # If it's a GitHub URL, say "GitHub repository"
            if "github.com" in raw_url:
                parts = raw_url.split("github.com/")[-1].strip("/").split("/")
                if len(parts) >= 2:
                    return f"GitHub repository {parts[0]} slash {parts[1]}"
                return "GitHub"
            return "web link"

        return URL_REGEX.sub(_replace_url, text)

    @staticmethod
    def strip_file_extensions(text: str) -> str:
        """Strip file extensions while leaving filename words intact."""
        return FILE_EXT_REGEX.sub(r"\1", text)

    @staticmethod
    def normalize_paths(text: str) -> str:
        """Convert directory path slashes (e.g. app/api/orders) into natural spoken pauses."""
        # Replace slashes between alphanumeric words with comma pauses
        s = re.sub(r"([a-zA-Z0-9_\u0900-\u0D7F])\/([a-zA-Z0-9_\u0900-\u0D7F])", r"\1, \2", text)
        return s

    @staticmethod
    def apply_phonetic_expansions(text: str) -> str:
        """Expand developer acronyms (FastAPI, PostgreSQL, gRPC, JWT, etc.) into phonetic speech."""
        s = text
        for pattern, replacement in PHONETIC_EXPANSIONS:
            s = pattern.sub(replacement, s)
        return s

    @staticmethod
    def split_technical_identifiers(text: str) -> str:
        """Format camelCase, PascalCase, and snake_case into natural words."""
        # 1. Handle camelCase and PascalCase
        # XMLHTTPRequest -> XML HTTP Request
        s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)
        # OrderProcessor -> Order Processor, getUserById -> get User By Id
        s = re.sub(r"([a-z0-9\u0900-\u0D7F])([A-Z])", r"\1 \2", s)

        # 2. Handle snake_case and kebab-case
        # Replace underscores with spaces (except where part of standard word)
        s = re.sub(r"_+", " ", s)

        # Replace hyphens between words that aren't compound adjectives (e.g. user-management-service)
        s = re.sub(r"([a-zA-Z0-9])-([a-zA-Z0-9])", r"\1 \2", s)
        return s

    @staticmethod
    def strip_markdown(text: str) -> str:
        """Strip markdown syntax (bold, italic, inline code, headings, blockquotes)."""
        s = MARKDOWN_HEADER_REGEX.sub("", text)
        s = MARKDOWN_INLINE_CODE_REGEX.sub(r"\1", s)
        s = MARKDOWN_BOLD_ITALIC_REGEX.sub(r"\2", s)
        s = MARKDOWN_BLOCKQUOTE_REGEX.sub("", s)
        s = MARKDOWN_BULLET_REGEX.sub("", s)
        s = s.replace("`", "")
        return s

    @staticmethod
    def remove_syntax_symbols(text: str) -> str:
        """Remove programming braces, operators, and emojis while preserving full Unicode scripts."""
        # Remove programming operators and syntax braces
        s = SYNTAX_SYMBOLS_REGEX.sub(" ", text)

        # Remove arrows and programming connectors (->, =>, ::)
        s = re.sub(r"\s*(\-\>|\=\>|\:\:)\s*", " to ", s)
        s = re.sub(r"\s*(\&\&|\&)\s*", " and ", s)

        # Strip emojis and pictographs (Unicode So and Cs categories)
        cleaned_chars = []
        for ch in s:
            cat = unicodedata.category(ch)
            # Keep letters (L*), numbers (N*), spaces (Z*), and punctuation (P*)
            # Exclude symbols (So, Sc, Sk, Sm) like emojis and currency glyphs where inappropriate
            if cat.startswith("S") and ch not in ("+", "=", "%", "$", "£", "€", "₹"):
                cleaned_chars.append(" ")
            else:
                cleaned_chars.append(ch)
        return "".join(cleaned_chars)

    @staticmethod
    def normalize_whitespace_and_punctuation(text: str) -> str:
        """Normalize punctuation and whitespace for clean TTS cadence."""
        s = text
        # Collapse multiple dots into standard pause
        s = re.sub(r"\.{3,}", " ... ", s)
        # Remove stray colons or semicolons left at word ends
        s = re.sub(r"\s*:\s*", ": ", s)
        # Collapse multiple commas
        s = re.sub(r",\s*,+", ", ", s)
        # Ensure single spaces
        s = re.sub(r"[ \t]+", " ", s)
        # Collapse excessive newlines
        s = re.sub(r"\n\s*\n+", "\n\n", s)
        return s.strip()

    # -------------------------------------------------------------------------
    # Scene Splitting & Script Parsing
    # -------------------------------------------------------------------------

    @classmethod
    def parse_script_into_scenes(cls, script_text: str, language: Optional[str] = "en") -> List[Dict[str, str]]:
        """Parse structured narration into scene-demarcated segments for synchronized TTS and subtitles.

        Args:
            script_text: Full technical narration script with [Scene 1: ...] markers.
            language: Target language code for language-aware cleaning.

        Returns:
            List of dictionaries with 'scene_id', 'title', and 'narration'.
        """
        lines = script_text.splitlines()
        scenes: List[Dict[str, str]] = []
        current_scene_id: Optional[str] = None
        current_title: Optional[str] = None
        current_lines: List[str] = []

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            match = SCENE_TAG_REGEX.match(trimmed)
            if match:
                if current_lines:
                    cleaned = cls.clean_for_tts(" ".join(current_lines), language=language)
                    if cleaned:
                        scenes.append({
                            "scene_id": current_scene_id or f"scene_{len(scenes) + 1}",
                            "title": current_title or f"Scene {len(scenes) + 1}",
                            "narration": cleaned,
                            "text": cleaned,
                        })
                    current_lines = []
                raw_tag = match.group(1).strip()
                current_scene_id = f"scene_{len(scenes) + 1}"
                current_title = raw_tag
                continue

            # Accumulate narration lines
            current_lines.append(trimmed)

        if current_lines:
            cleaned = cls.clean_for_tts(" ".join(current_lines), language=language)
            if cleaned:
                scenes.append({
                    "scene_id": current_scene_id or f"scene_{len(scenes) + 1}",
                    "title": current_title or f"Scene {len(scenes) + 1}",
                    "narration": cleaned,
                    "text": cleaned,
                })

        if not scenes:
            # Fallback if no scene markers
            cleaned_full = cls.clean_for_tts(script_text, language=language)
            scenes.append({
                "scene_id": "scene_1",
                "title": "Full Tutorial Narration",
                "narration": cleaned_full,
                "text": cleaned_full,
            })

        return scenes


# -----------------------------------------------------------------------------
# Convenience Functions
# -----------------------------------------------------------------------------


def normalize_text_for_tts(text: str, language: Optional[str] = "en") -> str:
    """Convenience functional wrapper for TextCleaner.clean_for_tts."""
    return TextCleaner.clean_for_tts(text, language=language)


def normalize_identifier(identifier: str) -> str:
    """Convenience helper to normalize a single code identifier into spoken words."""
    cleaned = TextCleaner.strip_file_extensions(identifier)
    return TextCleaner.split_technical_identifiers(cleaned).strip()


def strip_file_extensions(text: str) -> str:
    """Convenience helper to strip technical file extensions from text."""
    return TextCleaner.strip_file_extensions(text)


def remove_syntax_symbols(text: str) -> str:
    """Convenience helper to strip code syntax punctuation."""
    return TextCleaner.remove_syntax_symbols(text)


def split_technical_identifiers(text: str) -> str:
    """Convenience helper to split camelCase and snake_case identifiers."""
    return TextCleaner.split_technical_identifiers(text)


def parse_script_into_scenes(script_text: str, language: Optional[str] = "en") -> List[Dict[str, str]]:
    """Convenience helper to parse a multi-scene script into cleaned scene segments."""
    return TextCleaner.parse_script_into_scenes(script_text, language=language)
