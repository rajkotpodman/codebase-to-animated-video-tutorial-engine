"""Pydantic schemas and language definitions for video generation pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Language Definitions & Voice Catalog
# -----------------------------------------------------------------------------


class LanguageInfo(BaseModel):
    """Metadata for a supported speech synthesis and translation language."""

    code: str = Field(..., description="ISO 639-1 language code or BCP-47 locale tag")
    name: str = Field(..., description="English display name of the language")
    native_name: str = Field(..., description="Endonym / native script title")
    region: Literal["Indian Languages", "World Languages"] = Field(..., description="Geographic grouping")
    default_voice: str = Field(..., description="Default high-quality Microsoft Neural TTS voice model")
    available_voices: List[str] = Field(default_factory=list, description="All verified neural voices for locale")


SUPPORTED_LANGUAGES: Dict[str, LanguageInfo] = {
    # -------------------------------------------------------------------------
    # Indian Languages
    # -------------------------------------------------------------------------
    "gu": LanguageInfo(
        code="gu",
        name="Gujarati",
        native_name="ગુજરાતી",
        region="Indian Languages",
        default_voice="gu-IN-DhwaniNeural",
        available_voices=["gu-IN-DhwaniNeural", "gu-IN-NiranjanNeural"],
    ),
    "hi": LanguageInfo(
        code="hi",
        name="Hindi",
        native_name="हिन्दी",
        region="Indian Languages",
        default_voice="hi-IN-SwaraNeural",
        available_voices=["hi-IN-SwaraNeural", "hi-IN-MadhurNeural"],
    ),
    "mr": LanguageInfo(
        code="mr",
        name="Marathi",
        native_name="मराठी",
        region="Indian Languages",
        default_voice="mr-IN-AarohiNeural",
        available_voices=["mr-IN-AarohiNeural", "mr-IN-ManoharNeural"],
    ),
    "bn": LanguageInfo(
        code="bn",
        name="Bengali",
        native_name="বাংলা",
        region="Indian Languages",
        default_voice="bn-IN-TanishaaNeural",
        available_voices=["bn-IN-TanishaaNeural", "bn-IN-BashkarNeural"],
    ),
    "ta": LanguageInfo(
        code="ta",
        name="Tamil",
        native_name="தமிழ்",
        region="Indian Languages",
        default_voice="ta-IN-PallaviNeural",
        available_voices=["ta-IN-PallaviNeural", "ta-IN-ValluvarNeural"],
    ),
    "te": LanguageInfo(
        code="te",
        name="Telugu",
        native_name="తెలుగు",
        region="Indian Languages",
        default_voice="te-IN-ShrutiNeural",
        available_voices=["te-IN-ShrutiNeural", "te-IN-MohanNeural"],
    ),
    "kn": LanguageInfo(
        code="kn",
        name="Kannada",
        native_name="ಕನ್ನಡ",
        region="Indian Languages",
        default_voice="kn-IN-SapnaNeural",
        available_voices=["kn-IN-SapnaNeural", "kn-IN-GaganNeural"],
    ),
    "ml": LanguageInfo(
        code="ml",
        name="Malayalam",
        native_name="മലയാളം",
        region="Indian Languages",
        default_voice="ml-IN-SobhanaNeural",
        available_voices=["ml-IN-SobhanaNeural", "ml-IN-MidhunNeural"],
    ),
    "pa": LanguageInfo(
        code="pa",
        name="Punjabi",
        native_name="ਪੰਜਾਬੀ",
        region="Indian Languages",
        default_voice="hi-IN-MadhurNeural",  # Shared North Indian neural phonetics in Edge-TTS
        available_voices=["hi-IN-MadhurNeural", "hi-IN-SwaraNeural"],
    ),
    "ur": LanguageInfo(
        code="ur",
        name="Urdu",
        native_name="اردو",
        region="Indian Languages",
        default_voice="ur-IN-GulNeural",
        available_voices=["ur-IN-GulNeural", "ur-IN-SalmanNeural"],
    ),
    # -------------------------------------------------------------------------
    # World Languages
    # -------------------------------------------------------------------------
    "en": LanguageInfo(
        code="en",
        name="English",
        native_name="English",
        region="World Languages",
        default_voice="en-US-ChristopherNeural",
        available_voices=[
            "en-US-ChristopherNeural",
            "en-US-GuyNeural",
            "en-US-JennyNeural",
            "en-GB-RyanNeural",
            "en-IN-PrabhatNeural",
            "en-IN-NeerjaNeural",
        ],
    ),
    "es": LanguageInfo(
        code="es",
        name="Spanish",
        native_name="Español",
        region="World Languages",
        default_voice="es-ES-AlvaroNeural",
        available_voices=["es-ES-AlvaroNeural", "es-ES-ElviraNeural", "es-MX-DaliaNeural"],
    ),
    "fr": LanguageInfo(
        code="fr",
        name="French",
        native_name="Français",
        region="World Languages",
        default_voice="fr-FR-HenriNeural",
        available_voices=["fr-FR-HenriNeural", "fr-FR-DeniseNeural"],
    ),
    "de": LanguageInfo(
        code="de",
        name="German",
        native_name="Deutsch",
        region="World Languages",
        default_voice="de-DE-ConradNeural",
        available_voices=["de-DE-ConradNeural", "de-DE-KatjaNeural"],
    ),
    "ja": LanguageInfo(
        code="ja",
        name="Japanese",
        native_name="日本語",
        region="World Languages",
        default_voice="ja-JP-KeitaNeural",
        available_voices=["ja-JP-KeitaNeural", "ja-JP-NanamiNeural"],
    ),
    "zh": LanguageInfo(
        code="zh",
        name="Chinese",
        native_name="中文",
        region="World Languages",
        default_voice="zh-CN-YunxiNeural",
        available_voices=["zh-CN-YunxiNeural", "zh-CN-XiaoxiaoNeural"],
    ),
    "ar": LanguageInfo(
        code="ar",
        name="Arabic",
        native_name="العربية",
        region="World Languages",
        default_voice="ar-SA-HamedNeural",
        available_voices=["ar-SA-HamedNeural", "ar-SA-ZariyahNeural"],
    ),
    "pt": LanguageInfo(
        code="pt",
        name="Portuguese",
        native_name="Português",
        region="World Languages",
        default_voice="pt-BR-AntonioNeural",
        available_voices=["pt-BR-AntonioNeural", "pt-BR-FranciscaNeural"],
    ),
    "ru": LanguageInfo(
        code="ru",
        name="Russian",
        native_name="Русский",
        region="World Languages",
        default_voice="ru-RU-DmitryNeural",
        available_voices=["ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural"],
    ),
    "it": LanguageInfo(
        code="it",
        name="Italian",
        native_name="Italiano",
        region="World Languages",
        default_voice="it-IT-DiegoNeural",
        available_voices=["it-IT-DiegoNeural", "it-IT-ElsaNeural"],
    ),
    "ko": LanguageInfo(
        code="ko",
        name="Korean",
        native_name="한국어",
        region="World Languages",
        default_voice="ko-KR-InJoonNeural",
        available_voices=["ko-KR-InJoonNeural", "ko-KR-SunHiNeural"],
    ),
}


def resolve_language_info(target_language: Optional[str]) -> LanguageInfo:
    """Resolve an incoming language code, name, or locale string to a verified LanguageInfo."""
    if not target_language:
        return SUPPORTED_LANGUAGES["en"]

    clean = target_language.strip().lower()

    # Direct 2-letter code check (e.g. "gu", "hi", "es")
    if clean in SUPPORTED_LANGUAGES:
        return SUPPORTED_LANGUAGES[clean]

    # Locale tag check (e.g. "gu-in" -> "gu", "en-us" -> "en")
    if "-" in clean:
        short_code = clean.split("-")[0]
        if short_code in SUPPORTED_LANGUAGES:
            return SUPPORTED_LANGUAGES[short_code]

    # Full name check (e.g. "gujarati", "hindi", "spanish", "français")
    for lang in SUPPORTED_LANGUAGES.values():
        if clean in (lang.name.lower(), lang.native_name.lower()):
            return lang

    # Default to English if not found
    return SUPPORTED_LANGUAGES["en"]


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------


class GenerateVideoRequest(BaseModel):
    """Payload for initiating tutorial video generation."""

    repo_url: str = Field(
        ...,
        description="Public GitHub repository URL (e.g. 'https://github.com/octocat/Hello-World')",
        examples=["https://github.com/octocat/Hello-World", "rajkotpodman/helper-AI"],
    )
    target_language: str = Field(
        default="en",
        description="Target narration and subtitle language. Supports all Indian languages (Gujarati 'gu', Hindi 'hi', "
        "Marathi 'mr', Bengali 'bn', Tamil 'ta', Telugu 'te', Kannada 'kn', Malayalam 'ml', Punjabi 'pa', Urdu 'ur') "
        "and world languages (Spanish 'es', French 'fr', German 'de', Japanese 'ja', Chinese 'zh', Arabic 'ar', English 'en').",
        examples=["gu", "hi", "mr", "bn", "ta", "te", "es", "fr", "de", "ja", "en"],
    )
    voice: Optional[str] = Field(
        default="en-US-ChristopherNeural",
        description="Neural TTS voice model. If left default with a non-English target_language, "
        "the system automatically selects the optimal native voice for that language.",
    )
    resolution: Literal["1080p", "720p", "480p"] = Field(
        default="1080p",
        description="Target output video resolution",
    )
    theme: Literal["midnight", "dark", "cyberpunk", "nord", "light"] = Field(
        default="midnight",
        description="Manim architecture diagram styling theme",
    )
    burn_subtitles: bool = Field(
        default=True,
        description="Whether to burn synchronized subtitles directly into the video stream",
    )
    custom_instructions: Optional[str] = Field(
        default=None,
        description="Optional custom focus prompt for Gemini script generation",
    )
    gemini_model: Optional[str] = Field(
        default="gemini-2.5-flash",
        description="Google Gemini model identifier (e.g. 'gemini-2.5-flash', 'gemini-2.5-pro')",
    )
    run_sync: bool = Field(
        default=False,
        description="If True, runs synchronously in-process (useful for local debugging or non-Celery environments)",
    )


class GenerateVideoResponse(BaseModel):
    """Immediate response confirming task enqueue."""

    job_id: str
    status: str
    status_url: str
    message: str
    target_language: str = "en"
    voice: str = "en-US-ChristopherNeural"


class JobStatusResponse(BaseModel):
    """Job status, progress percentage, and final output artifacts."""

    job_id: str
    status: str  # PENDING, PROGRESS, SUCCESS, FAILURE
    progress: int
    step: Optional[int] = None
    step_name: Optional[str] = None
    message: Optional[str] = None
    target_language: Optional[str] = "en"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    download_url: Optional[str] = None

