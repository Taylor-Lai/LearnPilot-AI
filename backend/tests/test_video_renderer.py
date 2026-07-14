from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from backend.app.core.config import Settings
from backend.app.services.video_renderer import VideoRenderService, XfyunTTSClient


class VideoRendererTests(unittest.TestCase):
    def test_spark_credentials_can_be_reused_without_duplication(self) -> None:
        settings = Settings(
            _env_file=None,
            SPARK_API_PASSWORD="api-key:api-secret",
            XFYUN_TTS_APP_ID="app-id",
        )
        self.assertEqual(settings.xfyun_tts_credentials, ("api-key", "api-secret"))
        self.assertTrue(XfyunTTSClient(settings).configured)

    def test_authorization_url_contains_signature_but_not_secret(self) -> None:
        url = XfyunTTSClient._authorization_url("test-key", "test-secret")
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        self.assertEqual(parsed.hostname, "tts-api.xfyun.cn")
        self.assertIn("authorization", query)
        self.assertIn("date", query)
        self.assertNotIn("test-secret", url)

    def test_storyboard_normalization_and_scene_render(self) -> None:
        settings = Settings(_env_file=None)
        service = VideoRenderService(settings)
        scenes = service._normalize_scenes("卷积神经网络", [{"visual": "概念", "narration": "局部连接。"}])
        self.assertEqual(len(scenes), 5)
        self.assertEqual(scenes[0]["visual"], "概念")
        self.assertIn("卷积神经网络", scenes[1]["narration"])

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "scene.png"
            service._draw_scene(output, "卷积神经网络", scenes[0], 1, 5)
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 1000)

    def test_markdown_and_latex_are_cleaned_for_narration(self) -> None:
        source = r"**面积**为 $A = \frac{1}{2} \times \text{底} \times \text{高}$。"
        cleaned = VideoRenderService._plain_text(source)
        self.assertEqual(cleaned, "面积为 A = (1)除以(2) 乘以 底 乘以 高。")
        self.assertNotIn("\\", cleaned)


if __name__ == "__main__":
    unittest.main()
