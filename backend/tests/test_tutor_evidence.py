from backend.app.services.learning_service import LearningService


def test_evidence_excerpt_removes_markdown_images_and_formatting() -> None:
    content = """# 人工智能简介

![人工智能内容简介的涂鸦](../../images/ai-intro.png)

**人工智能**帮助计算机完成需要人类智能的任务，详见[课程主页](https://example.com)。
"""

    excerpt = LearningService._evidence_excerpt(content)

    assert "人工智能简介" in excerpt
    assert "人工智能 帮助计算机" in excerpt
    assert "课程主页" in excerpt
    assert "ai-intro.png" not in excerpt
    assert "![" not in excerpt
    assert "**" not in excerpt

