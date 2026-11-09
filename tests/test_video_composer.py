"""Unit and integration tests for VideoComposer FFmpeg media assembly."""

import os
import subprocess
import tempfile
from pathlib import Path
import pytest

from app.services.video_composer import (
    CompositionResult,
    VideoComposer,
    VideoComposerOptions,
    VideoCompositionError,
    resolve_ffmpeg_executable,
)


@pytest.fixture
def ffmpeg_bin():
    return resolve_ffmpeg_executable()


def test_resolve_ffmpeg_executable(ffmpeg_bin):
    assert ffmpeg_bin is not None
    assert os.path.exists(ffmpeg_bin)


def test_get_media_duration_and_compose_video(ffmpeg_bin):
    composer = VideoComposer(ffmpeg_bin=ffmpeg_bin)

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # 1. Create a 1.0 second test video at 640x360
        test_video = root / "input_anim.mp4"
        cmd_v = [
            ffmpeg_bin,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=indigo:s=640x360:d=1.0",
            "-pix_fmt",
            "yuv420p",
            str(test_video),
        ]
        subprocess.run(cmd_v, capture_output=True, check=True)

        # 2. Create a 2.5 second audio file (longer than video to trigger tpad freeze)
        test_audio = root / "voiceover.mp3"
        cmd_a = [
            ffmpeg_bin,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=500:duration=2.5",
            "-c:a",
            "libmp3lame",
            str(test_audio),
        ]
        subprocess.run(cmd_a, capture_output=True, check=True)

        # 3. Create a subtitle file
        test_srt = root / "subtitles.srt"
        test_srt.write_text(
            "1\n00:00:00,100 --> 00:00:02,000\nTesting Architecture Flow\n",
            encoding="utf-8",
        )

        # Verify duration inspection
        v_dur = composer.get_media_duration(test_video)
        a_dur = composer.get_media_duration(test_audio)
        assert 0.8 <= v_dur <= 1.2
        assert 2.3 <= a_dur <= 2.7

        # 4. Compose final HD 1080p video
        out_video = root / "final_video.mp4"
        options = VideoComposerOptions(
            target_width=1920,
            target_height=1080,
            burn_subtitles=True,
            freeze_last_frame=True,
            preset="ultrafast",
        )

        result = composer.compose_video(
            video_clip=test_video,
            audio_track=test_audio,
            subtitle_file=test_srt,
            output_path=out_video,
            options=options,
        )

        assert result.output_video_path.exists()
        assert result.width == 1920
        assert result.height == 1080
        assert result.file_size_bytes > 0
        assert result.has_subtitles is True
        assert result.has_audio is True
        # Output duration should match audio duration (~2.5s)
        assert result.duration_seconds >= 2.0


def test_concatenate_video_clips(ffmpeg_bin):
    composer = VideoComposer(ffmpeg_bin=ffmpeg_bin)

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        clip1 = root / "clip1.mp4"
        clip2 = root / "clip2.mp4"
        out_concat = root / "combined.mp4"

        for p, color in [(clip1, "blue"), (clip2, "red")]:
            subprocess.run(
                [
                    ffmpeg_bin,
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    f"color=c={color}:s=320x240:d=1.0",
                    "-pix_fmt",
                    "yuv420p",
                    str(p),
                ],
                capture_output=True,
                check=True,
            )

        merged = composer.concatenate_video_clips([clip1, clip2], out_concat)
        assert merged.exists()
        dur = composer.get_media_duration(merged)
        assert dur >= 1.8


def test_multi_language_subtitles_and_resolution_scaling(ffmpeg_bin):
    """Test burning multilingual subtitles (Indian, Asian, European scripts) across resolutions."""
    composer = VideoComposer(ffmpeg_bin=ffmpeg_bin)

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        test_video = root / "base_video.mp4"
        subprocess.run(
            [
                ffmpeg_bin,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=navy:s=640x360:d=1.5",
                "-pix_fmt",
                "yuv420p",
                str(test_video),
            ],
            capture_output=True,
            check=True,
        )

        test_audio = root / "base_audio.mp3"
        subprocess.run(
            [
                ffmpeg_bin,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=1.5",
                "-c:a",
                "libmp3lame",
                str(test_audio),
            ],
            capture_output=True,
            check=True,
        )

        # Multi-language subtitle with Gujarati, Hindi, Spanish, and Japanese
        multilingual_srt = root / "multilingual.srt"
        multilingual_srt.write_text(
            "1\n00:00:00,100 --> 00:00:00,700\nગુજરાતી: આર્કિટેક્ચર વિશ્લેષણ\n\n"
            "2\n00:00:00,750 --> 00:00:01,100\nहिन्दी: आर्किटेक्चर विश्लेषण\n\n"
            "3\n00:00:01,150 --> 00:00:01,450\nEspañol: Análisis de Arquitectura\n",
            encoding="utf-8",
        )

        # Test across 1080p, 720p, 480p with auto-scaled subtitles
        for res_name, (w, h) in [("1080p", (1920, 1080)), ("720p", (1280, 720)), ("480p", (854, 480))]:
            out_v = root / f"composed_{res_name}.mp4"
            opts = VideoComposerOptions(
                target_width=w,
                target_height=h,
                burn_subtitles=True,
                auto_scale_subtitles=True,
                prevent_black_screen=True,
                preset="ultrafast",
            )
            result = composer.compose_video(
                video_clip=test_video,
                audio_track=test_audio,
                subtitle_file=multilingual_srt,
                output_path=out_v,
                options=opts,
            )
            assert result.output_video_path.exists()
            assert result.width == w
            assert result.height == h
            assert result.has_subtitles is True


def test_prevent_black_screen_tpad_hold(ffmpeg_bin):
    """Verify smart tpad frame freeze keeps content visible when audio is longer than video."""
    composer = VideoComposer(ffmpeg_bin=ffmpeg_bin)

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        video_p = root / "short_anim.mp4"
        subprocess.run(
            [ffmpeg_bin, "-y", "-f", "lavfi", "-i", "color=c=darkgreen:s=640x360:d=1.0", "-pix_fmt", "yuv420p", str(video_p)],
            capture_output=True,
            check=True,
        )
        audio_p = root / "long_audio.mp3"
        subprocess.run(
            [ffmpeg_bin, "-y", "-f", "lavfi", "-i", "sine=frequency=600:duration=3.0", "-c:a", "libmp3lame", str(audio_p)],
            capture_output=True,
            check=True,
        )

        out_p = root / "tpad_hold.mp4"
        opts = VideoComposerOptions(
            target_width=1280,
            target_height=720,
            freeze_last_frame=True,
            prevent_black_screen=True,
            hold_buffer_sec=0.5,
            preset="ultrafast",
        )
        res = composer.compose_video(video_clip=video_p, audio_track=audio_p, output_path=out_p, options=opts)
        assert res.output_video_path.exists()
        # Duration must match 3.0s audio + 0.5s hold buffer = ~3.5s
        assert res.duration_seconds >= 3.4


def test_pyvideotrans_audio_time_stretch(ffmpeg_bin):
    """Test audio time-stretching with atempo filter."""
    composer = VideoComposer(ffmpeg_bin=ffmpeg_bin)

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        in_a = root / "orig_audio.wav"
        subprocess.run(
            [ffmpeg_bin, "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2.0", str(in_a)],
            capture_output=True,
            check=True,
        )

        out_faster = root / "faster_audio.wav"
        # Speed up by 1.25x -> duration should be 2.0 / 1.25 = ~1.6s
        composer.time_stretch_audio(in_a, out_faster, speed_factor=1.25)
        dur_faster = composer.get_media_duration(out_faster)
        assert 1.4 <= dur_faster <= 1.8


def test_pyvideotrans_video_retiming(ffmpeg_bin):
    """Test video retiming using setpts filter."""
    composer = VideoComposer(ffmpeg_bin=ffmpeg_bin)

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        in_v = root / "orig_video.mp4"
        subprocess.run(
            [ffmpeg_bin, "-y", "-f", "lavfi", "-i", "color=c=purple:s=320x240:d=2.0", "-pix_fmt", "yuv420p", str(in_v)],
            capture_output=True,
            check=True,
        )

        out_retimed = root / "retimed_video.mp4"
        # Speed factor 0.8 -> duration becomes 2.0 / 0.8 = ~2.5s
        composer.retime_video(in_v, out_retimed, speed_factor=0.8, fps=30)
        dur_retimed = composer.get_media_duration(out_retimed)
        assert 2.3 <= dur_retimed <= 2.7


def test_adjust_subtitle_timestamps(ffmpeg_bin):
    """Test scaling subtitle timestamps for speed adjustments."""
    composer = VideoComposer(ffmpeg_bin=ffmpeg_bin)

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        in_srt = root / "sample.srt"
        in_srt.write_text(
            "1\n00:00:02,000 --> 00:00:04,000\nHello World\n",
            encoding="utf-8",
        )

        out_srt = root / "scaled.srt"
        # Speed factor 2.0 -> timestamps halved (00:00:01,000 --> 00:00:02,000)
        composer.adjust_subtitle_timestamps(in_srt, out_srt, speed_factor=2.0)
        content = out_srt.read_text(encoding="utf-8")
        assert "00:00:01,000 --> 00:00:02,000" in content


def test_manim_dynamic_duration_scaling_helpers():
    """Test scaling of Manim script and architecture diagram durations."""
    from manim_engine.base_template import (
        scale_manim_script_duration,
        scale_architecture_diagram_duration,
    )
    from manim_engine.models import ArchitectureDiagramData, SceneConfig

    # 1. Manim script duration scaling
    raw_script = """
    class TestScene(Scene):
        def construct(self):
            self.play(FadeIn(card), run_time=2.0)
            self.wait(3.0)
            self.play(FadeOut(card), run_time=1.5)
            self.wait(1.0)
    """
    # Target duration 20.0s -> script wait should be scaled up
    scaled = scale_manim_script_duration(raw_script, target_duration=20.0)
    assert "FadeOut" not in scaled or "prevent black screen" in scaled
    assert "self.wait(" in scaled

    # 2. ArchitectureDiagramData outro scaling
    diagram = ArchitectureDiagramData(
        config=SceneConfig(title="Test Architecture", duration_per_flow=2.0, outro_duration=2.0)
    )
    scaled_diag = scale_architecture_diagram_duration(diagram, target_duration=35.0)
    assert scaled_diag.config.outro_duration >= 20.0
