from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from email.utils import formatdate
from pathlib import Path
from urllib.parse import urlencode, urlparse

from PIL import Image, ImageDraw, ImageFont

from backend.app.core.config import Settings, get_settings

TTS_ENDPOINT = "wss://tts-api.xfyun.cn/v2/tts"
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS = 25


class VideoRenderError(RuntimeError):
    """Raised when narration or MP4 rendering cannot be completed."""


@dataclass(frozen=True)
class RenderedVideo:
    path: Path
    duration_seconds: float
    narration_provider: str
    voice: str


class XfyunTTSClient:
    """Minimal authenticated client for iFlytek online streaming TTS."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def configured(self) -> bool:
        return bool(self.settings.xfyun_tts_app_id and self.settings.xfyun_tts_credentials)

    def synthesize(self, text: str, destination: Path) -> None:
        if not self.configured:
            raise VideoRenderError("iFlytek TTS credentials are not configured")
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            raise VideoRenderError("narration text is empty")
        if len(normalized.encode("utf-8")) >= 8000:
            raise VideoRenderError("narration exceeds the iFlytek 8000-byte request limit")

        try:
            import websocket
        except ImportError as exc:  # pragma: no cover - dependency contract
            raise VideoRenderError("websocket-client is required for iFlytek TTS") from exc

        api_key, api_secret = self.settings.xfyun_tts_credentials
        connection = websocket.create_connection(
            self._authorization_url(api_key, api_secret),
            timeout=self.settings.xfyun_tts_timeout_seconds,
            enable_multithread=False,
        )
        audio = bytearray()
        try:
            connection.send(
                json.dumps(
                    {
                        "common": {"app_id": self.settings.xfyun_tts_app_id},
                        "business": {
                            "aue": "lame",
                            "auf": "audio/L16;rate=16000",
                            "vcn": self.settings.xfyun_tts_voice,
                            "tte": "UTF8",
                            "speed": self.settings.xfyun_tts_speed,
                            "volume": self.settings.xfyun_tts_volume,
                            "pitch": 50,
                        },
                        "data": {
                            "status": 2,
                            "text": base64.b64encode(normalized.encode("utf-8")).decode("ascii"),
                        },
                    },
                    ensure_ascii=False,
                )
            )
            while True:
                response = json.loads(connection.recv())
                code = int(response.get("code", -1))
                if code != 0:
                    message = str(response.get("message") or "unknown TTS error")
                    raise VideoRenderError(f"iFlytek TTS failed ({code}): {message}")
                data = response.get("data") or {}
                chunk = data.get("audio")
                if chunk:
                    audio.extend(base64.b64decode(chunk))
                if int(data.get("status", 0)) == 2:
                    break
        finally:
            connection.close()
        if not audio:
            raise VideoRenderError("iFlytek TTS returned no audio")
        destination.write_bytes(audio)

    @staticmethod
    def _authorization_url(api_key: str, api_secret: str) -> str:
        parsed = urlparse(TTS_ENDPOINT)
        date = formatdate(usegmt=True)
        signature_origin = f"host: {parsed.hostname}\ndate: {date}\nGET {parsed.path} HTTP/1.1"
        signature = base64.b64encode(
            hmac.new(api_secret.encode(), signature_origin.encode(), hashlib.sha256).digest()
        ).decode()
        authorization_origin = (
            f'api_key="{api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        query = urlencode(
            {
                "authorization": base64.b64encode(authorization_origin.encode()).decode(),
                "date": date,
                "host": parsed.hostname,
            }
        )
        return f"{TTS_ENDPOINT}?{query}"


class VideoRenderService:
    """Render a storyboard into a self-contained narrated MP4 micro-lesson."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.tts = XfyunTTSClient(self.settings)

    def render(
        self,
        task_id: str,
        topic: str,
        scenes: list[dict],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> RenderedVideo:
        safe_task_id = re.sub(r"[^a-zA-Z0-9_-]", "", task_id)
        if not safe_task_id or safe_task_id != task_id:
            raise VideoRenderError("invalid video task identifier")
        normalized = self._normalize_scenes(topic, scenes)
        output_dir = self.settings.video_output_path
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / f"{safe_task_id}.mp4"

        with tempfile.TemporaryDirectory(prefix=f"learnpilot-video-{safe_task_id}-") as temporary:
            workdir = Path(temporary)
            segments: list[Path] = []
            total_duration = 0.0
            for index, scene in enumerate(normalized, start=1):
                image_path = workdir / f"scene-{index:02d}.png"
                audio_path = workdir / f"scene-{index:02d}.mp3"
                segment_path = workdir / f"segment-{index:02d}.mp4"
                self._draw_scene(image_path, topic, scene, index, len(normalized))
                self.tts.synthesize(scene["narration"], audio_path)
                duration = max(5.0, self._audio_duration(audio_path) + 0.8)
                self._render_segment(image_path, audio_path, segment_path, duration)
                segments.append(segment_path)
                total_duration += duration
                if progress_callback:
                    progress_callback(index, len(normalized))
            self._concatenate(segments, destination, workdir)
        return RenderedVideo(
            path=destination,
            duration_seconds=round(total_duration, 1),
            narration_provider="iFlytek online TTS",
            voice=self.settings.xfyun_tts_voice,
        )

    @staticmethod
    def _normalize_scenes(topic: str, scenes: list[dict]) -> list[dict[str, str]]:
        defaults = [
            ("学习目标", f"本节聚焦{topic}，先明确问题边界、输入输出与学习目标。"),
            ("核心概念", f"把{topic}拆成定义、关键步骤和前后依赖，建立完整知识结构。"),
            ("案例推演", f"通过一个最小案例观察{topic}中参数、过程与结果之间的关系。"),
            ("易错点对比", "对照错误做法与正确做法，解释错误产生的原因。"),
            ("练习与复盘", f"请暂停并用自己的话解释{topic}，再完成一道迁移练习。"),
        ]
        normalized: list[dict[str, str]] = []
        for index in range(5):
            source = scenes[index] if index < len(scenes) and isinstance(scenes[index], dict) else {}
            visual = VideoRenderService._plain_text(source.get("visual") or defaults[index][0])[:80]
            narration = VideoRenderService._plain_text(
                source.get("narration") or source.get("content") or defaults[index][1]
            )[:360]
            normalized.append({"visual": visual, "narration": narration})
        return normalized

    @staticmethod
    def _plain_text(value: object) -> str:
        text = str(value or "")
        substitutions = (
            (r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)除以(\2)"),
            (r"\\text\{([^{}]+)\}", r"\1"),
            (r"\\(?:times|cdot)", "乘以"),
            (r"\\(?:left|right)", ""),
            (r"https?://\S+", ""),
            (r"[`*_>#]", ""),
            (r"[$]", ""),
            (r"\\([A-Za-z]+)", r"\1"),
        )
        for pattern, replacement in substitutions:
            text = re.sub(pattern, replacement, text)
        return re.sub(r"\s+", " ", text).strip()

    def _draw_scene(self, destination: Path, topic: str, scene: dict[str, str], index: int, total: int) -> None:
        image = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), "#07111f")
        draw = ImageDraw.Draw(image)
        title_font = self._font(52)
        body_font = self._font(30)
        small_font = self._font(20)

        draw.ellipse((900, -170, 1350, 280), fill="#123f5a")
        draw.ellipse((1040, 400, 1370, 730), fill="#29275f")
        draw.rounded_rectangle((54, 52, 1226, 668), radius=34, fill="#101d32", outline="#23566f", width=2)
        draw.text((150, 82), "LEARNPILOT · AI 微课", font=small_font, fill="#67e8f9")
        draw.text((88, 124), self._fit_text(draw, topic, title_font, 850, 1), font=title_font, fill="#f8fafc")
        draw.text((1080, 92), f"{index:02d}/{total:02d}", font=small_font, fill="#67e8f9")

        draw.rounded_rectangle((88, 230, 1192, 565), radius=28, fill="#14243d")
        draw.text((124, 266), scene["visual"], font=self._font(38), fill="#a5f3fc")
        lines = self._wrap_text(draw, scene["narration"], body_font, 980, max_lines=5)
        draw.multiline_text((124, 340), "\n".join(lines), font=body_font, fill="#dbeafe", spacing=16)

        progress_width = int(1104 * index / total)
        draw.rounded_rectangle((88, 620, 1192, 630), radius=5, fill="#26364f")
        draw.rounded_rectangle((88, 620, 88 + progress_width, 630), radius=5, fill="#22d3ee")
        image.save(destination, format="PNG", optimize=True)

    def _font(self, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        for candidate in self.settings.video_font_candidates:
            if candidate.is_file():
                return ImageFont.truetype(str(candidate), size=size)
        return ImageFont.load_default(size=size)

    @staticmethod
    def _wrap_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont,
        max_width: int,
        *,
        max_lines: int,
    ) -> list[str]:
        lines: list[str] = []
        current = ""
        for character in re.sub(r"\s+", " ", text).strip():
            candidate = current + character
            if current and draw.textlength(candidate, font=font) > max_width:
                lines.append(current)
                current = character
                if len(lines) == max_lines:
                    lines[-1] = lines[-1][:-1] + "…"
                    return lines
            else:
                current = candidate
        if current and len(lines) < max_lines:
            lines.append(current)
        return lines or [""]

    def _fit_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont,
        max_width: int,
        max_lines: int,
    ) -> str:
        return "\n".join(self._wrap_text(draw, text, font, max_width, max_lines=max_lines))

    def _render_segment(self, image: Path, audio: Path, output: Path, duration: float) -> None:
        frames = math.ceil(duration * VIDEO_FPS)
        zoom_filter = (
            "scale=1408:792,"
            f"zoompan=z='min(zoom+0.00018,1.06)':d={frames}:"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720:fps=25,format=yuv420p"
        )
        self._run_ffmpeg(
            "-loop",
            "1",
            "-framerate",
            str(VIDEO_FPS),
            "-i",
            str(image),
            "-i",
            str(audio),
            "-vf",
            zoom_filter,
            "-af",
            "apad",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "21",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output),
        )

    def _concatenate(self, segments: list[Path], destination: Path, workdir: Path) -> None:
        concat_file = workdir / "segments.txt"
        concat_file.write_text(
            "\n".join(f"file '{path.as_posix()}'" for path in segments) + "\n",
            encoding="utf-8",
        )
        temporary_output = destination.with_suffix(".tmp.mp4")
        self._run_ffmpeg(
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(temporary_output),
        )
        temporary_output.replace(destination)

    @staticmethod
    def _ffmpeg_executable() -> str:
        system = shutil.which("ffmpeg")
        if system:
            return system
        raise VideoRenderError("FFmpeg is unavailable; install it or use the project Docker stack")

    @staticmethod
    def _ffprobe_executable() -> str:
        system = shutil.which("ffprobe")
        if system:
            return system
        raise VideoRenderError("FFprobe is unavailable; install FFmpeg or use the project Docker stack")

    def _audio_duration(self, audio: Path) -> float:
        result = subprocess.run(
            [
                self._ffprobe_executable(),
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        try:
            duration = float(result.stdout.strip())
        except ValueError as exc:
            raise VideoRenderError(f"Unable to determine narration duration: {result.stderr.strip()}") from exc
        if result.returncode != 0 or duration <= 0:
            raise VideoRenderError(f"Invalid narration duration: {result.stderr.strip()}")
        return duration

    def _run_ffmpeg(self, *arguments: str) -> None:
        command = [self._ffmpeg_executable(), "-hide_banner", "-loglevel", "error", "-y", *arguments]
        result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
        if result.returncode != 0:
            error = (result.stderr or result.stdout or "unknown FFmpeg error").strip()
            raise VideoRenderError(f"FFmpeg failed: {error[-800:]}")


video_render_service = VideoRenderService()
