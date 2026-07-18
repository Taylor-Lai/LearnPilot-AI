from __future__ import annotations

import ast
import json
from html import escape
from typing import Any

from ..domain.models import LearningStep, StudentProfile


class ResourceBundleBuilder:
    """Build export-ready teaching assets without external models or binary renderers."""

    FORMAT_VERSION = "learning-resource-bundle-v1"

    @staticmethod
    def _structured_practice(value: Any) -> list[dict[str, Any]]:
        """Normalize model practice output without exposing serialized data to users."""
        parsed = value
        if isinstance(value, str):
            candidate = value.strip()
            if candidate.startswith(("[", "{")):
                for loader in (json.loads, ast.literal_eval):
                    try:
                        parsed = loader(candidate)
                        break
                    except (ValueError, SyntaxError, TypeError, json.JSONDecodeError):
                        continue
        if isinstance(parsed, dict):
            parsed = parsed.get("questions") or parsed.get("items") or [parsed]
        if not isinstance(parsed, list):
            return []
        return [item for item in parsed if isinstance(item, dict) and (item.get("question") or item.get("prompt"))]

    def _practice_markdown(self, card: dict[str, Any]) -> str:
        items = self._structured_practice(card.get("practice"))
        if not items:
            return str(card.get("practice") or "")
        return "\n".join(
            f"{index}. {item.get('question') or item.get('prompt')}"
            for index, item in enumerate(items, start=1)
        )

    def build(self, card: dict[str, Any], step: LearningStep, profile: StudentProfile) -> dict[str, Any]:
        point = step.knowledge_point
        title = str(card.get("title") or f"{point} 个性化学习资源")
        evidence_refs = str(card.get("evidence_refs") or "template")
        formats = {
            "lecture": self._lecture(card, point),
            "slide_deck": self._slide_deck(card, point),
            "mind_map": self._mind_map(card, point, step),
            "quiz_bank": self._quiz_bank(card, point),
            "video_storyboard": self._video_storyboard(card, point),
            "lab": self._lab(card, point, step),
            "project": self._project(point, step, profile),
        }
        return {
            "version": self.FORMAT_VERSION,
            "title": title,
            "knowledge_point": point,
            "evidence_refs": evidence_refs,
            "formats": formats,
            "manifest": [
                {
                    "type": name,
                    "content_type": value["content_type"],
                    "export_ready": True,
                }
                for name, value in formats.items()
            ],
        }

    def _lecture(self, card: dict, point: str) -> dict:
        sections = [
            {"heading": "学习目标", "content": f"理解并能够应用 {point}"},
            {"heading": "核心讲解", "content": card.get("explanation", "")},
            {"heading": "示例", "content": card.get("example", "")},
            {"heading": "常见错误", "content": card.get("mistake_analysis", "")},
            {"heading": "课后练习", "content": self._practice_markdown(card)},
        ]
        markdown = "\n\n".join(f"## {item['heading']}\n\n{item['content']}" for item in sections)
        return {
            "content_type": "application/vnd.learnpilot.lecture+json",
            "sections": sections,
            "markdown": f"# {point} 个性化讲义\n\n{markdown}\n",
        }

    def _slide_deck(self, card: dict, point: str) -> dict:
        slides = [
            {"layout": "title", "title": f"{point} 个性化微课", "speaker_notes": "说明学习目标与路径。"},
            {"layout": "concept", "title": "核心概念", "body": card.get("explanation", "")},
            {"layout": "example", "title": "案例拆解", "body": card.get("example", "")},
            {"layout": "warning", "title": "易错点", "body": card.get("mistake_analysis", "")},
            {"layout": "practice", "title": "课堂练习", "body": card.get("practice", "")},
            {"layout": "summary", "title": "复习与行动", "body": card.get("review_tip", "")},
        ]
        sections = "".join(
            f'<section class="slide {escape(item["layout"])}"><h2>{escape(item["title"])}</h2>'
            f"<p>{escape(str(item.get('body') or item.get('speaker_notes') or ''))}</p></section>"
            for item in slides
        )
        return {
            "content_type": "application/vnd.learnpilot.slides+json",
            "theme": "academic-blue",
            "slides": slides,
            "html": (
                '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                f"<title>LearnPilot Slides</title><body>{sections}</body></html>"
            ),
        }

    def _mind_map(self, card: dict, point: str, step: LearningStep) -> dict:
        prerequisites = list(step.prerequisites)
        nodes = [{"id": "root", "label": point, "kind": "topic"}]
        edges = []
        for index, prerequisite in enumerate(prerequisites, start=1):
            node_id = f"prerequisite-{index}"
            nodes.append({"id": node_id, "label": prerequisite, "kind": "prerequisite"})
            edges.append({"from": node_id, "to": "root", "relation": "precedes"})
        nodes.extend(
            [
                {"id": "concept", "label": "核心概念", "kind": "concept"},
                {"id": "example", "label": "示例", "kind": "example"},
                {"id": "mistake", "label": "易错点", "kind": "warning"},
                {"id": "practice", "label": "练习", "kind": "practice"},
            ]
        )
        edges.extend(
            {"from": "root", "to": node, "relation": "contains"}
            for node in ("concept", "example", "mistake", "practice")
        )
        mermaid_lines = ["mindmap", f"  root(({point}))", "    核心概念", "    示例", "    易错点", "    练习"]
        safe_point = escape(point)
        return {
            "content_type": "application/vnd.learnpilot.mind-map+json",
            "nodes": nodes,
            "edges": edges,
            "mermaid": "\n".join(mermaid_lines),
            "svg": (
                '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="420" role="img" '
                f'aria-label="{safe_point} 思维导图"><rect width="100%" height="100%" fill="#f8fafc"/>'
                '<rect x="360" y="165" width="240" height="90" rx="20" fill="#2563eb"/>'
                f'<text x="480" y="215" text-anchor="middle" fill="white" font-size="26">{safe_point}</text>'
                '<text x="160" y="90" text-anchor="middle">核心概念</text>'
                '<text x="800" y="90" text-anchor="middle">示例</text>'
                '<text x="160" y="350" text-anchor="middle">易错点</text>'
                '<text x="800" y="350" text-anchor="middle">练习</text>'
                '<path d="M360 190 L190 105 M600 190 L770 105 M360 230 L190 330 M600 230 L770 330" '
                'stroke="#64748b" fill="none" stroke-width="3"/></svg>'
            ),
            "summary": card.get("explanation", ""),
        }

    def _quiz_bank(self, card: dict, point: str) -> dict:
        generated_items = self._structured_practice(card.get("practice"))
        if generated_items:
            questions = []
            for index, item in enumerate(generated_items, start=1):
                options = item.get("options") if isinstance(item.get("options"), list) else []
                question_type = item.get("type") or ("single_choice" if options else "short_answer")
                questions.append(
                    {
                        "id": str(item.get("id") or f"q{index}"),
                        "type": question_type,
                        "prompt": str(item.get("question") or item.get("prompt") or ""),
                        "options": options,
                        "answer": item.get("answer") or card.get("answer", ""),
                        "rubric": item.get("rubric") or ["概念准确", "推理清晰", "回答完整"],
                        "evidence_refs": item.get("evidence_refs") or card.get("evidence_refs", ""),
                    }
                )
            return {
                "content_type": "application/vnd.learnpilot.quiz-bank+json",
                "questions": questions,
            }
        return {
            "content_type": "application/vnd.learnpilot.quiz-bank+json",
            "questions": [
                {
                    "id": "q1",
                    "type": "short_answer",
                    "prompt": self._practice_markdown(card) or f"解释 {point} 的核心概念。",
                    "answer": card.get("answer", ""),
                    "rubric": ["概念准确", "步骤完整", "能够解释原因"],
                },
                {
                    "id": "q2",
                    "type": "error_analysis",
                    "prompt": f"给出一个 {point} 的常见错误并说明如何修正。",
                    "answer": card.get("mistake_analysis", ""),
                    "rubric": ["识别错误", "说明原因", "给出修正方案"],
                },
            ],
        }

    def _video_storyboard(self, card: dict, point: str) -> dict:
        scenes = [
            {"start": 0, "duration": 25, "visual": f"标题与学习目标：{point}", "narration": f"本节聚焦 {point}。"},
            {"start": 25, "duration": 90, "visual": "概念关键词逐步出现", "narration": card.get("explanation", "")},
            {"start": 115, "duration": 65, "visual": "案例步骤动画", "narration": card.get("example", "")},
            {
                "start": 180,
                "duration": 35,
                "visual": "错误与正确做法对比",
                "narration": card.get("mistake_analysis", ""),
            },
            {"start": 215, "duration": 25, "visual": "暂停作答卡", "narration": card.get("practice", "")},
        ]
        subtitles = "\n\n".join(
            f"{index}\n{self._srt_time(item['start'])} --> {self._srt_time(item['start'] + item['duration'])}\n"
            f"{item['narration']}"
            for index, item in enumerate(scenes, start=1)
        )
        return {
            "content_type": "application/vnd.learnpilot.video-storyboard+json",
            "estimated_seconds": 240,
            "scenes": scenes,
            "subtitles_srt": f"{subtitles}\n",
            "transcript": "\n".join(str(item["narration"]) for item in scenes),
            "accessibility": {"captions_required": True, "transcript_included": True},
        }

    def _srt_time(self, seconds: int) -> str:
        minutes, second = divmod(seconds, 60)
        hour, minute = divmod(minutes, 60)
        return f"{hour:02d}:{minute:02d}:{second:02d},000"

    def _lab(self, card: dict, point: str, step: LearningStep) -> dict:
        steps = [
            "阅读实验目标并记录假设",
            card.get("practice", "完成指定练习"),
            "保存结果并解释差异",
            "根据参考答案完成自检",
        ]
        return {
            "content_type": "application/vnd.learnpilot.lab+json",
            "objective": f"通过可复现实验验证 {point} 的关键步骤。",
            "prerequisites": list(step.prerequisites),
            "steps": steps,
            "deliverables": ["实验过程记录", "结果或代码", "误差分析", "自评"],
            "rubric": {"过程正确": 40, "结果可复现": 30, "解释清晰": 20, "反思完整": 10},
            "markdown": "\n".join(
                [f"# {point} 实验", "", *[f"{index}. {item}" for index, item in enumerate(steps, start=1)]]
            ),
        }

    def _project(self, point: str, step: LearningStep, profile: StudentProfile) -> dict:
        milestones = ["明确输入、输出与约束", "完成最小可运行版本", "加入边界测试", "复盘并说明设计取舍"]
        return {
            "content_type": "application/vnd.learnpilot.project+json",
            "brief": f"设计一个能够展示 {point} 实际用途的最小项目。",
            "milestones": milestones,
            "estimated_minutes": max(45, step.estimated_minutes),
            "difficulty": profile.learning_stage,
            "acceptance_criteria": [f"正确使用 {point}", "结果可验证", "包含至少一个边界场景", "能够口头解释实现"],
            "markdown": "\n".join(
                [
                    f"# {point} 项目任务书",
                    "",
                    f"## 项目目标\n\n设计一个能够展示 {point} 实际用途的最小项目。",
                    "",
                    "## 里程碑",
                    *[f"- {item}" for item in milestones],
                ]
            ),
        }
