"""Video Assembly & Composition Service.

Inspired by open-source video rendering engines (like MoneyPrinterTurbo).
Uses FFmpeg to merge Manim-generated multi-scene animations, TTS voiceover audio tracks,
and timestamped .srt subtitles into synchronized HD MP4 tutorial videos.

Handles:
  - Resolution scaling (1080p, 720p, vertical shorts) with aspect-ratio preserving letterboxing
  - Audio/video duration synchronization (freezing/cloning last video frame when audio > video via tpad,
    and padding audio with silence when video > audio via apad, preventing premature cutoffs)
  - Subtitle burn-in with customized fonts, colors, shadows, and cross-platform path escaping
  - Optional background music (BGM) mixing with audio ducking
  - Cross-platform FFmpeg auto-discovery (system PATH or imageio-ffmpeg binary)
"""

from __future__ import annotations

import dataclasses
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Literal, Optional, Sequence, Tuple, Union

logger = logging.getLogger("video_composer")


# -----------------------------------------------------------------------------
# Configuration & Data Models
# -----------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class VideoComposerOptions:
    """Settings for video rendering, scaling, subtitle styling, and audio sync."""

    target_width: int = 1920
    target_height: int = 1080
    fps: int = 30
    video_bitrate: str = "4000k"
    audio_bitrate: str = "192k"
    preset: str = "medium"  # ultrafast, superfast, fast, medium, slow
    burn_subtitles: bool = True
    subtitle_font_name: str = "Arial"
    subtitle_font_size: int = 22
    subtitle_color: str = "&H00FFFFFF"  # White in BGR ASS format
    subtitle_outline_color: str = "&H00000000"  # Black outline
    subtitle_outline_width: int = 2
    subtitle_shadow_width: int = 1
    subtitle_margin_v: int = 30  # Vertical margin from bottom
    auto_scale_subtitles: bool = True  # Dynamically scale subtitle typography across 1080p, 720p, 480p
    freeze_last_frame: bool = True  # Freeze last frame when audio is longer than video
    pad_audio: bool = True  # Pad audio with silence when video is longer than audio
    hold_buffer_sec: float = 0.5  # Extra buffer to hold the final frame
    prevent_black_screen: bool = True  # Guarantees visual content stays cleanly on screen without black screen cutoffs
    # pyvideotrans-inspired synchronization modes
    sync_mode: Literal["auto", "freeze_and_pad", "video_stretch", "audio_stretch"] = "auto"
    min_stretch_factor: float = 0.88  # Safe speed adjustment bounds without audio/video distortion
    max_stretch_factor: float = 1.15
    bgm_path: Optional[Path | str] = None  # Optional background music track
    bgm_volume: float = 0.12  # Volume multiplier for BGM (ducking under voiceover)
    fade_in_sec: float = 0.4
    fade_out_sec: float = 0.5


@dataclasses.dataclass
class CompositionResult:
    """Result artifact container for a fully assembled video."""

    output_video_path: Path
    duration_seconds: float
    width: int
    height: int
    file_size_bytes: int
    has_subtitles: bool
    has_audio: bool

    def save_to(self, destination: Path | str) -> Path:
        """Copy output video to a specified destination."""
        dest = Path(destination).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.output_video_path, dest)
        return dest


class VideoCompositionError(Exception):
    """Raised when FFmpeg video assembly fails."""

    pass


# -----------------------------------------------------------------------------
# FFmpeg Binary Resolver
# -----------------------------------------------------------------------------


def resolve_ffmpeg_executable() -> str:
    """Find system FFmpeg executable or fallback to imageio-ffmpeg static binary."""
    # 1. System PATH
    bin_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    system_ffmpeg = shutil.which(bin_name) or shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # 2. Bundled imageio-ffmpeg
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise VideoCompositionError(
            "FFmpeg executable not found in PATH or imageio-ffmpeg. "
            "Please install ffmpeg or run 'pip install imageio-ffmpeg'."
        ) from exc


# -----------------------------------------------------------------------------
# Video Composer Service
# -----------------------------------------------------------------------------


class VideoComposer:
    """High-performance media processing engine using FFmpeg."""

    def __init__(self, ffmpeg_bin: Optional[str] = None) -> None:
        self.ffmpeg_bin = ffmpeg_bin or resolve_ffmpeg_executable()

    def get_media_duration(self, file_path: Path | str) -> float:
        """Inspect media file and return its duration in seconds."""
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Media file not found: {path}")

        cmd = [self.ffmpeg_bin, "-i", str(path)]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = proc.stderr or proc.stdout

        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", output)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)

        # Fallback default duration
        logger.warning("Could not determine exact duration for %s; defaulting to 0.0s", path)
        return 0.0

    def compose_video(
        self,
        video_clip: Path | str,
        audio_track: Path | str,
        subtitle_file: Optional[Path | str] = None,
        output_path: Optional[Path | str] = None,
        options: Optional[VideoComposerOptions] = None,
    ) -> CompositionResult:
        """Merge video, voiceover, and subtitles into a synchronized HD MP4.

        Ensures duration synchronization without cutoff:
          - If audio > video: freeze/clone the last video frame with tpad
          - If video > audio: pad audio stream with silence via apad
          - Set exact target duration (-t) to prevent premature truncation

        Args:
            video_clip: Manim-generated intermediate video file (.mp4)
            audio_track: TTS voiceover audio file (.mp3 or .wav)
            subtitle_file: Optional .srt subtitle file for burn-in
            output_path: Destination path for final assembled .mp4 video
            options: Video composer settings (resolution, scaling, styling, audio sync)

        Returns:
            CompositionResult container with video metadata and final file path.
        """
        opts = options or VideoComposerOptions()
        video_p = Path(video_clip).resolve()
        audio_p = Path(audio_track).resolve()

        if not video_p.exists():
            raise VideoCompositionError(f"Input video file not found: {video_p}")
        if not audio_p.exists():
            raise VideoCompositionError(f"Input audio file not found: {audio_p}")

        sub_p = Path(subtitle_file).resolve() if subtitle_file else None

        # 1. Inspect input durations
        video_dur = self.get_media_duration(video_p)
        audio_dur = self.get_media_duration(audio_p)
        target_dur = max(video_dur, audio_dur)

        logger.info(
            "Composing video: video_dur=%.2fs, audio_dur=%.2fs -> target_dur=%.2fs",
            video_dur,
            audio_dur,
            target_dur,
        )

        # 2. Determine output destination
        if output_path:
            final_dest = Path(output_path).resolve()
        else:
            temp_dir = tempfile.mkdtemp(prefix="final_video_")
            final_dest = Path(temp_dir) / "final_tutorial.mp4"

        final_dest.parent.mkdir(parents=True, exist_ok=True)

        # 3. Construct Video Filterchain
        vf_filters: List[str] = []

        # Resolution scaling with aspect-ratio preservation and black letterbox padding
        w, h = opts.target_width, opts.target_height
        scale_pad = (
            f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black"
        )
        vf_filters.append(scale_pad)

        # Video/Audio synchronization inspired by pyvideotrans:
        ratio = (audio_dur / video_dur) if video_dur > 0 else 1.0

        # Check if video retiming is requested or auto-activated within safe bounds
        if opts.sync_mode == "video_stretch" and (opts.min_stretch_factor <= ratio <= opts.max_stretch_factor):
            # Retime video frames to match exact audio duration without freezing
            vf_filters.append(f"setpts={ratio:.5f}*PTS")
            vf_filters.append(f"fps={opts.fps}")
            target_dur = audio_dur
            logger.info("Applied pyvideotrans-style video retiming: setpts=%.5f*PTS (duration: %.2fs)", ratio, target_dur)
        elif opts.freeze_last_frame and audio_dur > (video_dur + 0.05):
            # Anti-black-screen smart frame freezing:
            # Clones the final visual frame so architecture elements stay cleanly on screen
            freeze_dur = (audio_dur - video_dur) + opts.hold_buffer_sec
            target_dur = audio_dur + opts.hold_buffer_sec
            vf_filters.append(f"tpad=stop_mode=clone:stop_duration={freeze_dur:.3f}")
            logger.info("Applied anti-black-screen tpad freeze: %.3fs on last video frame", freeze_dur)

        # Subtitle burn-in with resolution-aware dynamic scaling & robust cross-platform path escaping
        has_subtitles_applied = False
        if opts.burn_subtitles and sub_p and sub_p.exists():
            # Dynamically compute typography based on target resolution height
            if opts.auto_scale_subtitles:
                scale_ratio = h / 1080.0
                effective_font_size = max(13, int(round(opts.subtitle_font_size * scale_ratio)))
                effective_margin_v = max(12, int(round(opts.subtitle_margin_v * scale_ratio)))
                effective_outline = max(1, int(round(opts.subtitle_outline_width * scale_ratio)))
                effective_shadow = max(1, int(round(opts.subtitle_shadow_width * scale_ratio)))
            else:
                effective_font_size = opts.subtitle_font_size
                effective_margin_v = opts.subtitle_margin_v
                effective_outline = opts.subtitle_outline_width
                effective_shadow = opts.subtitle_shadow_width

            # Escape colons and single quotes for FFmpeg filter on Windows and Linux
            escaped_srt = sub_p.as_posix().replace(":", "\\:").replace("'", "\\'")
            style_str = (
                f"FontName={opts.subtitle_font_name},"
                f"FontSize={effective_font_size},"
                f"PrimaryColour={opts.subtitle_color},"
                f"OutlineColour={opts.subtitle_outline_color},"
                f"Outline={effective_outline},"
                f"Shadow={effective_shadow},"
                f"MarginV={effective_margin_v},"
                "Alignment=2"  # Bottom center
            )
            # Appending after tpad ensures subtitles render dynamically on top of the frozen card
            sub_filter = f"subtitles='{escaped_srt}':force_style='{style_str}'"
            vf_filters.append(sub_filter)
            has_subtitles_applied = True

        video_filter_arg = ",".join(vf_filters)

        # 4. Construct Audio Filterchain
        af_filters: List[str] = []
        if opts.sync_mode == "audio_stretch" and (opts.min_stretch_factor <= (1.0 / ratio) <= opts.max_stretch_factor):
            speed = audio_dur / video_dur
            af_filters.append(f"atempo={speed:.5f}")
            target_dur = video_dur
            logger.info("Applied pyvideotrans-style audio time-stretching: atempo=%.5f (duration: %.2fs)", speed, target_dur)
        elif opts.pad_audio and video_dur > (audio_dur + 0.05):
            af_filters.append(f"apad=whole_dur={target_dur:.3f}")
            logger.info("Applied apad filter to extend audio to match video: %.3fs", target_dur)

        # 5. Construct complete FFmpeg execution arguments
        cmd: List[str] = [
            self.ffmpeg_bin,
            "-y",
            "-i",
            str(video_p),
            "-i",
            str(audio_p),
        ]

        # Handle optional background music (BGM)
        has_bgm = opts.bgm_path and Path(opts.bgm_path).exists()
        if has_bgm:
            cmd.extend(["-i", str(Path(opts.bgm_path).resolve())])
            audio_pad_str = f",apad=whole_dur={target_dur:.3f}" if opts.pad_audio and video_dur > audio_dur else ""
            filter_complex = (
                f"[0:v]{video_filter_arg}[v_out];"
                f"[2:a]volume={opts.bgm_volume}[bgm];"
                f"[1:a]{audio_pad_str}[voice];"
                f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[a_out]"
            )
            cmd.extend(
                [
                    "-filter_complex",
                    filter_complex,
                    "-map",
                    "[v_out]",
                    "-map",
                    "[a_out]",
                ]
            )
        else:
            cmd.extend(
                [
                    "-vf",
                    video_filter_arg,
                ]
            )
            if af_filters:
                cmd.extend(["-af", ",".join(af_filters)])
            cmd.extend(
                [
                    "-map",
                    "0:v",
                    "-map",
                    "1:a",
                ]
            )

        # Video & Audio codecs, quality presets, and explicit target duration
        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                opts.preset,
                "-b:v",
                opts.video_bitrate,
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(opts.fps),
                "-c:a",
                "aac",
                "-b:a",
                opts.audio_bitrate,
                "-ar",
                "44100",
                "-movflags",
                "+faststart",
                "-t",
                f"{target_dur:.3f}",  # Explicit target duration prevents premature cutoffs
                str(final_dest),
            ]
        )

        logger.info("Executing FFmpeg video assembly: %s", " ".join(cmd))

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )

        if proc.returncode != 0:
            error_msg = proc.stderr or proc.stdout
            logger.error("FFmpeg composition failed: %s", error_msg)
            raise VideoCompositionError(f"FFmpeg assembly failed with exit code {proc.returncode}:\n{error_msg}")

        if not final_dest.exists() or final_dest.stat().st_size == 0:
            raise VideoCompositionError("FFmpeg reported success but output video file was not created or is empty.")

        actual_duration = self.get_media_duration(final_dest)
        file_size = final_dest.stat().st_size

        return CompositionResult(
            output_video_path=final_dest,
            duration_seconds=actual_duration,
            width=w,
            height=h,
            file_size_bytes=file_size,
            has_subtitles=has_subtitles_applied,
            has_audio=True,
        )

    def concatenate_video_clips(
        self,
        clip_paths: Sequence[Path | str],
        output_path: Path | str,
    ) -> Path:
        """Concatenate multiple scene clips seamlessly using the FFmpeg concat demuxer."""
        valid_paths = [Path(p).resolve() for p in clip_paths if Path(p).exists()]
        if not valid_paths:
            raise VideoCompositionError("No valid video clip paths provided for concatenation.")

        if len(valid_paths) == 1:
            shutil.copyfile(valid_paths[0], output_path)
            return Path(output_path).resolve()

        dest = Path(output_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as list_f:
            list_file_path = list_f.name
            for cp in valid_paths:
                # FFmpeg concat file requires paths escaped
                escaped = cp.as_posix().replace("'", "'\\''")
                list_f.write(f"file '{escaped}'\n")

        try:
            cmd = [
                self.ffmpeg_bin,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_file_path,
                "-c",
                "copy",
                str(dest),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.returncode != 0:
                raise VideoCompositionError(f"Video concatenation failed: {res.stderr}")
            return dest
        finally:
            if os.path.exists(list_file_path):
                os.remove(list_file_path)

    # -------------------------------------------------------------------------
    # pyvideotrans-Inspired Synchronization & Subtitle Utilities
    # -------------------------------------------------------------------------

    def time_stretch_audio(
        self,
        input_path: Path | str,
        output_path: Path | str,
        speed_factor: float,
    ) -> Path:
        """Time-stretch an audio track using FFmpeg's atempo filter without altering pitch."""
        in_p = Path(input_path).resolve()
        out_p = Path(output_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)

        if not in_p.exists():
            raise FileNotFoundError(f"Audio file not found: {in_p}")

        # Build chained atempo filters if speed is outside 0.5 - 2.0 range
        factors: List[float] = []
        curr = max(0.2, min(5.0, float(speed_factor)))
        while curr > 2.0:
            factors.append(2.0)
            curr /= 2.0
        while curr < 0.5:
            factors.append(0.5)
            curr /= 0.5
        factors.append(curr)

        atempo_filter = ",".join(f"atempo={f:.4f}" for f in factors)
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i",
            str(in_p),
            "-filter:a",
            atempo_filter,
            "-vn",
            str(out_p),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise VideoCompositionError(f"Audio time-stretching failed: {res.stderr}")
        return out_p

    def retime_video(
        self,
        input_path: Path | str,
        output_path: Path | str,
        speed_factor: float,
        fps: int = 30,
    ) -> Path:
        """Retime video playback speed using FFmpeg's setpts filter."""
        in_p = Path(input_path).resolve()
        out_p = Path(output_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)

        if not in_p.exists():
            raise FileNotFoundError(f"Video file not found: {in_p}")

        pts_mult = 1.0 / max(0.01, float(speed_factor))
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i",
            str(in_p),
            "-vf",
            f"setpts={pts_mult:.5f}*PTS,fps={fps}",
            "-an",
            str(out_p),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise VideoCompositionError(f"Video retiming failed: {res.stderr}")
        return out_p

    def adjust_subtitle_timestamps(
        self,
        srt_path: Path | str,
        output_path: Path | str,
        speed_factor: float,
    ) -> Path:
        """Scale all subtitle start and end timestamps in an SRT file by speed_factor."""
        in_p = Path(srt_path).resolve()
        out_p = Path(output_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)

        if not in_p.exists():
            raise FileNotFoundError(f"Subtitle file not found: {in_p}")

        speed = max(0.05, float(speed_factor))
        content = in_p.read_text(encoding="utf-8", errors="replace")
        time_pattern = re.compile(
            r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
        )

        def _to_sec(h: str, m: str, s: str, ms: str) -> float:
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

        def _from_sec(sec: float) -> str:
            total_ms = max(0, int(round(sec * 1000)))
            h = total_ms // 3600000
            total_ms %= 3600000
            m = total_ms // 60000
            total_ms %= 60000
            s = total_ms // 1000
            ms = total_ms % 1000
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        def _replace_match(m: re.Match) -> str:
            start_s = _to_sec(m.group(1), m.group(2), m.group(3), m.group(4))
            end_s = _to_sec(m.group(5), m.group(6), m.group(7), m.group(8))
            new_start = start_s / speed
            new_end = end_s / speed
            return f"{_from_sec(new_start)} --> {_from_sec(new_end)}"

        new_content = time_pattern.sub(_replace_match, content)
        out_p.write_text(new_content, encoding="utf-8")
        return out_p

    def burn_subtitles_to_video(
        self,
        video_path: Path | str,
        subtitle_path: Path | str,
        output_path: Path | str,
        options: Optional[VideoComposerOptions] = None,
    ) -> Path:
        """Standalone helper to burn ASS/SRT subtitles into a video file with customized styling."""
        opts = options or VideoComposerOptions()
        in_v = Path(video_path).resolve()
        in_sub = Path(subtitle_path).resolve()
        out_v = Path(output_path).resolve()
        out_v.parent.mkdir(parents=True, exist_ok=True)

        if not in_v.exists():
            raise FileNotFoundError(f"Video file not found: {in_v}")
        if not in_sub.exists():
            raise FileNotFoundError(f"Subtitle file not found: {in_sub}")

        h = opts.target_height
        scale = h / 1080.0 if opts.auto_scale_subtitles else 1.0
        font_size = max(13, int(round(opts.subtitle_font_size * scale)))
        margin_v = max(12, int(round(opts.subtitle_margin_v * scale)))
        outline = max(1, int(round(opts.subtitle_outline_width * scale)))
        shadow = max(1, int(round(opts.subtitle_shadow_width * scale)))

        escaped_srt = in_sub.as_posix().replace(":", "\\:").replace("'", "\\'")
        style = (
            f"FontName={opts.subtitle_font_name},"
            f"FontSize={font_size},"
            f"PrimaryColour={opts.subtitle_color},"
            f"OutlineColour={opts.subtitle_outline_color},"
            f"Outline={outline},"
            f"Shadow={shadow},"
            f"MarginV={margin_v},"
            "Alignment=2"
        )
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i",
            str(in_v),
            "-vf",
            f"subtitles='{escaped_srt}':force_style='{style}'",
            "-c:a",
            "copy",
            str(out_v),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise VideoCompositionError(f"Subtitle burn-in failed: {res.stderr}")
        return out_v
