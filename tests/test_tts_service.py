"""Unit and integration tests for TTS & Subtitle Synchronization Service."""

import os
import tempfile
from pathlib import Path
import pytest

from app.services.tts_service import (
    ScriptCleaner,
    SubtitleCue,
    TTSService,
    TTSOptions,
    format_srt_timestamp,
)


def test_format_srt_timestamp():
    assert format_srt_timestamp(0.0) == "00:00:00,000"
    assert format_srt_timestamp(1.234) == "00:00:01,234"
    assert format_srt_timestamp(65.5) == "00:01:05,500"
    assert format_srt_timestamp(3661.050) == "01:01:01,050"


def test_script_cleaner_preprocessing():
    raw_script = """
    # Introduction to Engine
    [Scene 1: System Overview]
    [Visual: Zoom camera in]
    Welcome to the **FastAPI** backend documentation.
    We use `__init__.py` to declare packages and connect to PostgreSQL.
    [Pause: 1.5s]
    [Scene 2: Pipeline Execution]
    Data packets flow via gRPC to the worker pool.
    """

    scenes = ScriptCleaner.parse_script_scenes(raw_script)
    assert len(scenes) == 2
    assert scenes[0]["scene_id"] == "1:_system_overview"
    assert "Fast A P I" in scenes[0]["text"]
    assert "dunder init dot py" in scenes[0]["text"]
    assert "Postgres Q L" in scenes[0]["text"]
    assert "[Visual:" not in scenes[0]["text"]
    assert "**" not in scenes[0]["text"]
    assert "`" not in scenes[0]["text"]

    assert scenes[1]["scene_id"] == "2:_pipeline_execution"
    assert "g R P C" in scenes[1]["text"]


def test_subtitle_cue_formatting():
    cue = SubtitleCue(
        index=1,
        start_time=1.5,
        end_time=4.825,
        text="Hello world from video engine.",
        scene_id="intro",
    )
    assert cue.start_srt == "00:00:01,500"
    assert cue.end_srt == "00:00:04,825"
    assert "00:00:01,500 --> 00:00:04,825" in cue.to_srt_block()
    assert "Hello world from video engine." in cue.to_srt_block()


@pytest.mark.asyncio
async def test_tts_service_synthesis_and_srt_generation():
    service = TTSService()
    script = (
        "[Scene 1: Introduction]\n"
        "Welcome to the automated codebase animation tutorial.\n"
        "[Scene 2: Architecture]\n"
        "Here we explore how microservices communicate over high speed queues."
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        options = TTSOptions(
            voice="en-US-ChristopherNeural",
            output_format="mp3",
        )
        result = await service.async_synthesize_script(script, output_dir=tmp_dir, options=options)

        assert result.audio_path.exists()
        assert result.srt_path.exists()
        assert result.file_size_bytes > 0
        assert result.duration_seconds > 1.0
        assert len(result.subtitles) >= 2
        assert "-->" in result.srt_content

        # Verify SRT format in the generated file
        file_srt = result.srt_path.read_text(encoding="utf-8")
        assert "00:00:" in file_srt
        assert "Welcome to the automated codebase" in file_srt

        # Verify scene timestamps mapping
        assert "1:_introduction" in result.scene_timestamps or len(result.scene_timestamps) > 0

        # Verify timestamp lookup helper
        found_cue = result.find_cue_at_timestamp(1.0)
        assert found_cue is not None
        assert found_cue.text != ""


def test_tts_service_wav_output_conversion():
    service = TTSService()
    script = "Testing audio format conversion."

    with tempfile.TemporaryDirectory() as tmp_dir:
        options = TTSOptions(
            voice="en-US-ChristopherNeural",
            output_format="wav",
        )
        result = service.synthesize_script(script, output_dir=tmp_dir, options=options)

        assert result.audio_format == "wav"
        assert result.audio_path.exists()
        assert result.srt_path.exists()
        assert result.file_size_bytes > 0
