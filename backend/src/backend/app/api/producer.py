from __future__ import annotations

import ast
import io
import json
import logging
import re
from html import escape
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.adapters.ml_service_client import MLServiceClient, MLServiceUnavailable
from backend.app.core.config import get_settings
from backend.app.core.database import SessionLocal, get_db
from backend.app.core.security import optional_user
from backend.app.models import (
    ProducerArtifact,
    ProducerChatMessage,
    ProducerTask,
    ResourceCenter,
    User,
)
from backend.app.services.export_service import learning_resource_export_service
from backend.app.services.video_renderer import VideoRenderError, video_render_service

router = APIRouter(prefix="/producer", tags=["producer"])
logger = logging.getLogger(__name__)

DEFAULT_TYPES = ["lecture", "mind_map", "exercise", "video", "code", "dataset", "roadmap"]


class ProducerTaskRequest(BaseModel):
    topic: str = Field(default="通用学习主题", max_length=255)
    requirement: str = ""
    types: list[str] = Field(default_factory=lambda: list(DEFAULT_TYPES))
    task_type: str = Field(default="multi_agent_generation", max_length=64)

    model_config = ConfigDict(extra="allow")


class ProducerChatRequest(BaseModel):
    session_id: str | None = Field(default=None, max_length=64)
    message: str = Field(min_length=1)
    topic: str = Field(default="学习主题", max_length=255)


class ProducerRunRequest(BaseModel):
    language: str = Field(default="python", max_length=32)
    code: str


def _matching_resources(
    db: Session,
    keyword: str,
    resource_types: list[str] | None = None,
    limit: int = 8,
) -> list[ResourceCenter]:
    query = db.query(ResourceCenter).filter(ResourceCenter.status == "published")
    if resource_types:
        query = query.filter(ResourceCenter.resource_type.in_(resource_types))
    if keyword.strip():
        normalized = keyword.strip()
        simplified = re.sub(r"(入门|基础|教程|课程|学习|资源|资料|讲义|详解)", " ", normalized)
        terms = [normalized, *re.findall(r"[A-Za-z][A-Za-z0-9+-]*|[\u4e00-\u9fff]{2,}", simplified)]
        if "卷积神经网络" in normalized:
            terms.extend(["CNN", "卷积神经网络", "卷积"])
        if "反向传播" in normalized:
            terms.extend(["反向传播", "Backpropagation"])
        terms = list(dict.fromkeys(term.strip() for term in terms if len(term.strip()) >= 2))[:8]
        conditions = []
        for term in terms:
            pattern = f"%{term}%"
            conditions.extend(
                [
                    ResourceCenter.title.ilike(pattern),
                    ResourceCenter.description.ilike(pattern),
                    ResourceCenter.content.ilike(pattern),
                    ResourceCenter.knowledge_point.ilike(pattern),
                    ResourceCenter.tags.ilike(pattern),
                ]
            )
        query = query.filter(or_(*conditions))
    return query.order_by(ResourceCenter.views.desc(), ResourceCenter.id.asc()).limit(limit).all()


def _resource_reference(resource: ResourceCenter) -> dict:
    return {
        "id": resource.id,
        "title": resource.title,
        "type": resource.resource_type,
        "url": "" if resource.resource_type == "document" else (resource.url or ""),
        "detail_url": f"/resources/{resource.id}",
        "description": resource.description or resource.summary or "",
    }


def _roadmap_nodes(topic: str) -> list[dict]:
    return [
        {
            "step": 1,
            "title": "基础概念",
            "description": f"理解 {topic} 的定义、适用场景、输入输出和关键术语。",
            "estimated_minutes": 30,
        },
        {
            "step": 2,
            "title": "核心原理",
            "description": f"拆解 {topic} 的核心流程，并通过图示建立知识点之间的联系。",
            "estimated_minutes": 45,
        },
        {
            "step": 3,
            "title": "例题与练习",
            "description": f"完成 {topic} 的选择题、简答题和关键步骤推导。",
            "estimated_minutes": 40,
        },
        {
            "step": 4,
            "title": "代码实操",
            "description": f"运行一个最小 {topic} 示例，观察参数、输入和输出变化。",
            "estimated_minutes": 50,
        },
        {
            "step": 5,
            "title": "综合复盘",
            "description": f"总结 {topic} 的常见误区，形成个人复习清单并完成自测。",
            "estimated_minutes": 30,
        },
    ]


def _exercise_items(topic: str) -> list[dict]:
    return [
        {
            "type": "single_choice",
            "question": f"学习 {topic} 时，最合理的第一步是什么？",
            "options": ["明确问题与输入输出", "直接背诵结论", "跳过基础概念", "只复制代码"],
            "answer": "A",
            "analysis": "先明确问题边界、输入输出和目标，后续原理分析与实践才有清晰依据。",
        },
        {
            "type": "single_choice",
            "question": f"检验自己是否真正理解 {topic} 的有效方法是？",
            "options": ["只看答案", "用自己的话解释并完成新例题", "重复阅读标题", "忽略错误"],
            "answer": "B",
            "analysis": "能够解释原理并迁移到新问题，说明知识已经从记忆转化为理解。",
        },
        {
            "type": "short_answer",
            "question": f"请用三到五句话说明 {topic} 的核心原理和一个典型应用。",
            "options": [],
            "answer": f"答案应包含 {topic} 的定义、关键处理流程、输入输出以及一个具体应用场景。",
            "analysis": "回答时应建立完整因果关系，避免只罗列关键词。",
        },
    ]


def _video_items(db: Session, topic: str) -> list[dict]:
    resources = _matching_resources(db, topic, ["video"], limit=6)
    items = [
        {
            "title": resource.title,
            "url": resource.url or "",
            "description": resource.description or resource.summary or f"{topic} 视频资源",
        }
        for resource in resources
        if resource.url
    ]
    if items:
        return items
    return [
        {
            "title": f"{topic} 基础公开视频",
            "url": "https://www.youtube.com/watch?v=aircAruvnKk",
            "description": "通过动画和直观示例理解神经网络的基本工作方式。",
        },
        {
            "title": f"{topic} 深度学习公开课",
            "url": "https://www.youtube.com/watch?v=IHZwWFHWa-w",
            "description": "适合结合课程讲义进行拓展学习的公开视频。",
        },
    ]


def _generated_animation(topic: str, scenes: list[dict] | None = None) -> dict:
    """Build a self-contained, sandbox-friendly animated micro-lesson."""
    default_scenes = [
        {
            "visual": "学习目标",
            "narration": f"先明确 {topic} 的问题边界、输入输出与学习目标。",
        },
        {
            "visual": "核心概念",
            "narration": f"把 {topic} 拆成定义、关键步骤和前后依赖，建立完整知识结构。",
        },
        {
            "visual": "案例推演",
            "narration": f"通过一个最小案例逐步观察 {topic} 中参数、过程与结果之间的关系。",
        },
        {
            "visual": "易错点对比",
            "narration": "对照错误做法与正确做法，解释错误产生的原因，而不只是记住答案。",
        },
        {
            "visual": "练习与复盘",
            "narration": f"暂停并用自己的话解释 {topic}，再完成一道迁移练习和复习清单。",
        },
    ]
    source_scenes = list(scenes or [])[:5]
    if len(source_scenes) < 5:
        source_scenes.extend(default_scenes[len(source_scenes) :])
    normalized_scenes = []
    for index, item in enumerate(source_scenes, start=1):
        normalized_scenes.append(
            {
                "index": index,
                "visual": str(item.get("visual") or f"场景 {index}")[:80],
                "narration": str(item.get("narration") or item.get("content") or "")[:260],
            }
        )
    scene_markup = "".join(
        (
            f'<section class="scene scene-{item["index"]}">'
            f'<span class="step">0{item["index"]} / 05</span>'
            f'<div class="orb orb-{item["index"]}"></div>'
            f'<h2>{escape(item["visual"])}</h2>'
            f'<p>{escape(item["narration"])}</p>'
            "</section>"
        )
        for item in normalized_scenes
    )
    safe_topic = escape(topic)
    animation_html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_topic} 动画微课</title>
<style>
*{{box-sizing:border-box}}html,body{{height:100%;margin:0}}body{{overflow:hidden;background:#07111f;color:#f8fafc;font-family:Inter,"Microsoft YaHei",sans-serif}}
.stage{{position:relative;height:100%;min-height:280px;background:radial-gradient(circle at 80% 15%,#164e63 0,transparent 34%),linear-gradient(135deg,#07111f,#172554)}}
.brand{{position:absolute;z-index:8;top:22px;left:26px;font-size:12px;letter-spacing:.18em;color:#67e8f9}}.topic{{position:absolute;z-index:8;top:42px;left:26px;right:26px;margin:0;font-size:clamp(18px,3vw,32px)}}
.scene{{position:absolute;inset:92px 24px 34px;padding:clamp(18px,4vw,42px);border:1px solid rgba(165,243,252,.22);border-radius:24px;background:rgba(15,23,42,.72);opacity:0;transform:translateY(18px) scale(.98);animation:scene 40s infinite}}
.scene-2{{animation-delay:8s}}.scene-3{{animation-delay:16s}}.scene-4{{animation-delay:24s}}.scene-5{{animation-delay:32s}}
.step{{color:#67e8f9;font-size:12px;letter-spacing:.12em}}h2{{margin:18px 0 12px;font-size:clamp(24px,5vw,50px)}}p{{max-width:760px;margin:0;font-size:clamp(15px,2.1vw,22px);line-height:1.75;color:#dbeafe}}
.orb{{position:absolute;right:8%;top:18%;width:clamp(70px,16vw,150px);aspect-ratio:1;border-radius:38% 62% 65% 35%;background:linear-gradient(135deg,#22d3ee,#6366f1);filter:drop-shadow(0 0 28px rgba(34,211,238,.4));animation:float 4s ease-in-out infinite alternate}}
.orb-2{{border-radius:50%;background:conic-gradient(#22d3ee,#818cf8,#22d3ee)}}.orb-3{{border-radius:18%;transform:rotate(18deg)}}.orb-4{{background:linear-gradient(135deg,#fb7185,#f59e0b)}}.orb-5{{background:linear-gradient(135deg,#34d399,#22d3ee)}}
.progress{{position:absolute;z-index:9;left:0;bottom:0;height:5px;background:#22d3ee;animation:progress 40s linear infinite}}
@keyframes scene{{0%,19%{{opacity:1;transform:none}}20%,100%{{opacity:0;transform:translateY(-14px) scale(.985)}}}}@keyframes progress{{from{{width:0}}to{{width:100%}}}}@keyframes float{{to{{transform:translateY(18px) rotate(8deg)}}}}
@media(prefers-reduced-motion:reduce){{.scene{{animation:none;opacity:0}}.scene:first-of-type{{opacity:1}}.orb,.progress{{animation:none}}}}
</style></head><body><main class="stage" aria-label="{safe_topic} 动画微课"><span class="brand">LEARNPILOT · GENERATED</span><h1 class="topic">{safe_topic}</h1>{scene_markup}<div class="progress"></div></main></body></html>"""
    transcript = "\n".join(item["narration"] for item in normalized_scenes)
    return {
        "id": "generated-animation",
        "title": f"{topic} 个性化动画微课",
        "description": "依据学习目标与知识点生成的五幕 HTML 动画预览；正式视频渲染与配音接口已预留。",
        "duration": "40 秒",
        "level": "个性化",
        "type": "生成动画",
        "url": "",
        "generated": True,
        "media_status": "preview",
        "rendering_mode": "html_animation",
        "mp4_available": False,
        "extension_point": "tts_ffmpeg_pipeline",
        "animation_html": animation_html,
        "scenes": normalized_scenes,
        "transcript": transcript,
    }
def _python_code(topic: str) -> str:
    topic_literal = repr(topic)
    steps_literal = repr(["明确输入与输出", "拆解核心原理", "运行最小案例", "记录结果并复盘"])
    return f"""topic = {topic_literal}
steps = {steps_literal}

# 在线环境采用安全模式，因此直接输出可验证的结构化结果。
print({{"topic": {topic_literal}, "steps": {steps_literal}}})
"""


def _code_items(topic: str, language: str) -> list[dict]:
    normalized = language.lower()
    if normalized in {"javascript", "js"}:
        code = (
            f"const topic = {json.dumps(topic, ensure_ascii=False)};\n"
            'const steps = ["明确输入输出", "理解核心原理", "完成最小案例", "复盘结果"];\n'
            "console.log({ topic, steps });\n"
        )
        language_name = "javascript"
    else:
        code = _python_code(topic)
        language_name = "python"
    return [
        {
            "title": f"{topic} 最小示例",
            "code": code,
            "explanation": f"该 {language_name} 示例用可运行的最小结构展示 {topic} 的学习与验证流程，可继续替换为具体算法实现。",
        }
    ]


def _dataset_items(keyword: str) -> list[dict]:
    return [
        {
            "title": "MNIST",
            "description": f"适合进行 {keyword} 入门实验的手写数字图像数据集。",
            "url": "https://www.kaggle.com/datasets/hojjatk/mnist-dataset",
        },
        {
            "title": "CIFAR-10",
            "description": f"包含十类彩色图像，可用于 {keyword} 分类与模型对比实验。",
            "url": "https://www.cs.toronto.edu/~kriz/cifar.html",
        },
        {
            "title": "UCI Machine Learning Repository",
            "description": f"可按任务类型选择适合 {keyword} 实践的公开结构化数据集。",
            "url": "https://archive.ics.uci.edu/",
        },
    ]


def _lecture(topic: str, requirement: str, references: list[dict]) -> dict:
    reference_text = "、".join(item["title"] for item in references[:3]) or "暂无匹配资源"
    content = f"""# {topic} 知识点讲解

## 学习目标
理解 {topic} 的基本定义、核心流程与典型应用，并能根据一个具体问题说明输入、处理过程和输出结果。

## 核心原理
学习 {topic} 时应先确定问题边界，再拆分关键步骤，最后用最小案例验证每一步。不要只记忆结论，要说明每个步骤为什么成立、参数变化会造成什么影响。

## 学习重点
1. 建立术语与实际问题之间的对应关系。
2. 掌握关键流程及其前后依赖。
3. 通过例题和代码验证理解。
4. 记录错误原因并形成复习清单。

## 个性化要求
{requirement or "面向课程学习与复习，兼顾概念理解和实践应用。"}

## 资源库参考
{reference_text}
"""
    return {"title": f"{topic} 知识点讲解", "content": content, "references": references}


def _mind_map(topic: str) -> dict:
    content = f"""# {topic}
- 基础概念
  - 定义与背景
  - 输入与输出
  - 适用场景
- 核心原理
  - 关键步骤
  - 参数与结果
  - 常见变体
- 实践应用
  - 典型例题
  - 代码案例
  - 数据集实验
- 评估复盘
  - 常见误区
  - 自测问题
  - 后续学习路线
"""
    return {"title": f"{topic} 思维导图", "content": content}


def _reading(topic: str, references: list[dict]) -> dict:
    return {
        "title": f"{topic} 拓展阅读",
        "content": (
            f"围绕 {topic}，建议按“概念定义、核心原理、典型案例、工程实践、复盘总结”的顺序阅读。"
            "每完成一份资料，提炼五个关键词、两个仍不清楚的问题和一个可运行实验，避免停留在被动浏览。"
        ),
        "references": references,
    }


def _normalize_types(types: list[str]) -> list[str]:
    aliases = {
        "exercises": "exercise",
        "code_example": "code",
        "code_examples": "code",
        "videos": "video",
        "datasets": "dataset",
    }
    normalized = []
    for item in types or DEFAULT_TYPES:
        value = aliases.get(str(item).strip().lower(), str(item).strip().lower())
        if value and value not in normalized:
            normalized.append(value)
    return normalized or list(DEFAULT_TYPES)


def _build_task_result(db: Session, topic: str, requirement: str, requested_types: list[str]) -> dict:
    references = [
        _resource_reference(item) for item in _matching_resources(db, topic, ["document", "ppt", "video"], limit=8)
    ]
    result = {
        "topic": topic,
        "requirement": requirement,
        "requested_types": requested_types,
        "lecture": _lecture(topic, requirement, references),
        "mind_map": _mind_map(topic),
        "exercises": _exercise_items(topic),
        "reading": _reading(topic, references),
        "videos": [_generated_animation(topic), *_video_items(db, topic)],
        "code_examples": _code_items(topic, "python"),
        "datasets": _dataset_items(topic),
        "roadmap": {"topic": topic, "nodes": _roadmap_nodes(topic)},
        "reused_resources": references,
        "agent_traces": [
            {
                "agent": "需求分析Agent",
                "action": "解析主题、生成要求和资源类型",
                "output": f"主题为 {topic}，计划生成 {len(requested_types)} 类学习产物。",
            },
            {
                "agent": "资源生成Agent",
                "action": "生成讲解、思维导图、阅读材料并检索资源库",
                "output": f"复用资源库匹配项 {len(references)} 条，并完成结构化学习材料。",
            },
            {
                "agent": "练习题Agent",
                "action": "围绕核心概念生成分层练习",
                "output": f"已生成 {len(_exercise_items(topic))} 道选择与简答练习。",
            },
            {
                "agent": "代码案例Agent",
                "action": "生成安全、可阅读的最小代码案例",
                "output": "已生成 Python 最小案例，运行接口采用模拟执行模式。",
            },
            {
                "agent": "质量评估Agent",
                "action": "检查内容完整性、类型覆盖和链接可用字段",
                "output": "结果包含路线、讲解、练习、视频、代码和数据集，结构检查通过。",
            },
        ],
    }
    return result


def _ml_resource_payload(resource: ResourceCenter, topic: str) -> dict:
    style = "video" if resource.resource_type == "video" else "text"
    return {
        "resource_id": f"resource_center:{resource.id}",
        "title": resource.title,
        "knowledge_points": [resource.knowledge_point or topic],
        "difficulty": 0.55,
        "style": style,
        "estimated_minutes": 25,
        "quality": 0.85,
        "url": resource.url,
        "content": resource.content or resource.description or resource.summary or "",
        "tags": [item.strip() for item in (resource.tags or "").split(",") if item.strip()],
    }


def _ml_generation_payload(
    db: Session,
    topic: str,
    requirement: str,
    student_id: str,
) -> dict:
    resources = _matching_resources(db, topic, limit=12)
    return {
        "student": {
            "student_id": student_id,
            "diagnostics": {topic: 0.35},
            "goals": [requirement or f"系统学习 {topic}"],
            "preferred_styles": ["text", "example", "quiz"],
        },
        "resources": [_ml_resource_payload(resource, topic) for resource in resources] or None,
        "knowledge_graph": [{"name": topic, "prerequisites": [], "importance": 1.0}],
        "course_context": {"requirement": requirement or f"系统学习 {topic}"},
    }


def _merge_ml_generation(result: dict, ml_result: dict) -> dict:
    cards = ml_result.get("generated_cards") or []
    if not cards:
        return result
    card = cards[0]
    bundle = card.get("resource_bundle") or {}
    formats = bundle.get("formats") or {}

    lecture = formats.get("lecture") or {}
    if lecture.get("markdown"):
        result["lecture"] = {
            "title": bundle.get("title") or result["lecture"]["title"],
            "content": lecture["markdown"],
            "references": card.get("rag_context") or [],
        }

    mind_map = formats.get("mind_map") or {}
    if mind_map:
        result["mind_map"] = {
            "title": f"{result['topic']} 思维导图",
            "content": mind_map.get("mermaid") or mind_map.get("summary") or "",
            "nodes": mind_map.get("nodes") or [],
            "edges": mind_map.get("edges") or [],
            "svg": mind_map.get("svg") or "",
        }

    quiz = formats.get("quiz_bank") or {}
    if quiz.get("questions"):
        result["exercises"] = [
            {
                "id": item.get("id"),
                "type": item.get("type", "short_answer"),
                "question": item.get("prompt", ""),
                "options": item.get("options") or [],
                "answer": item.get("answer", ""),
                "analysis": "；".join(item.get("rubric") or []),
            }
            for item in quiz["questions"]
        ]

    storyboard = formats.get("video_storyboard") or {}
    if storyboard.get("scenes"):
        generated_video = _generated_animation(result["topic"], storyboard["scenes"])
        existing_videos = result.get("videos") or []
        result["videos"] = [generated_video, *[item for item in existing_videos if not item.get("generated")]]

    result["resource_bundle"] = bundle
    result["generation_quality"] = card.get("quality_check") or {}
    result["review_cycle"] = card.get("review_cycle") or {}
    result["safety_meta"] = card.get("safety_meta") or {}
    result["retrieval_evidence"] = card.get("rag_context") or []
    result["agent_traces"].extend(ml_result.get("agent_traces") or [])
    return result


def _enrich_with_ml(
    db: Session,
    result: dict,
    topic: str,
    requirement: str,
    student_id: str,
) -> dict:
    try:
        ml_result = MLServiceClient().generate(_ml_generation_payload(db, topic, requirement, student_id))
        return _merge_ml_generation(result, ml_result)
    except MLServiceUnavailable as exc:
        result["agent_traces"].append(
            {
                "agent": "ML 服务适配器",
                "action": "请求个性化 RAG 与多形态资源包",
                "output": f"ML 服务不可用，已保留确定性本地生成结果：{exc}",
            }
        )
        result["generation_fallback"] = True
        return result


def _artifact_rows(task_id: str, result: dict, requested_types: list[str]) -> list[ProducerArtifact]:
    artifacts = []
    mapping = {
        "lecture": ("lecture", result["lecture"]["title"], result["lecture"]["content"], ""),
        "mind_map": ("mind_map", result["mind_map"]["title"], result["mind_map"]["content"], ""),
        "exercise": (
            "exercise",
            f"{result['topic']} 练习题",
            json.dumps(result["exercises"], ensure_ascii=False),
            "",
        ),
        "reading": ("reading", result["reading"]["title"], result["reading"]["content"], ""),
        "roadmap": (
            "roadmap",
            f"{result['topic']} 学习路线图",
            json.dumps(result["roadmap"], ensure_ascii=False),
            "",
        ),
        "code": (
            "code",
            result["code_examples"][0]["title"],
            result["code_examples"][0]["code"],
            "",
        ),
        "video": (
            "video",
            result["videos"][0]["title"],
            result["videos"][0]["description"],
            result["videos"][0]["url"],
        ),
        "dataset": (
            "dataset",
            result["datasets"][0]["title"],
            result["datasets"][0]["description"],
            result["datasets"][0]["url"],
        ),
    }
    for requested_type in requested_types:
        artifact_data = mapping.get(requested_type)
        if artifact_data is None:
            continue
        artifact_type, title, content, url = artifact_data
        artifacts.append(
            ProducerArtifact(
                task_id=task_id,
                artifact_type=artifact_type,
                title=title,
                content=content,
                url=url,
                metadata_json={"topic": result["topic"], "source": "producer_multi_agent"},
            )
        )
    return artifacts


def _task_or_404(db: Session, task_id: str) -> ProducerTask:
    task = db.query(ProducerTask).filter(ProducerTask.task_id == task_id).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producer task not found")
    return task


class ProducerTaskCancelled(Exception):
    pass


def _stop_if_cancelled(db: Session, task: ProducerTask) -> None:
    db.refresh(task)
    if task.status == "cancelled":
        raise ProducerTaskCancelled


def _execute_producer_task(db: Session, task_id: str) -> None:
    task = _task_or_404(db, task_id)
    if task.status in {"completed", "cancelled"}:
        return
    seed_payload = task.result_json if isinstance(task.result_json, dict) else {}
    requested_types = _normalize_types(seed_payload.get("requested_types") or DEFAULT_TYPES)
    try:
        task.status = "running"
        task.progress = 10
        task.error_message = None
        db.commit()

        result = _build_task_result(db, task.topic, task.requirement or "", requested_types)
        task.result_json = result
        task.progress = 45
        db.commit()
        _stop_if_cancelled(db, task)

        result = _enrich_with_ml(
            db,
            result,
            task.topic,
            task.requirement or "",
            str(task.user_id) if task.user_id else f"producer-{task_id}",
        )
        task.result_json = result
        task.progress = 80
        db.commit()
        _stop_if_cancelled(db, task)

        if "video" in requested_types and get_settings().video_render_enabled:
            generated_video = next((item for item in result.get("videos", []) if item.get("generated")), None)
            if generated_video:
                try:
                    def update_video_progress(completed: int, total: int) -> None:
                        task.progress = min(95, 80 + round(15 * completed / max(1, total)))
                        db.commit()
                        _stop_if_cancelled(db, task)

                    rendered = video_render_service.render(
                        task_id,
                        result["topic"],
                        list(generated_video.get("scenes") or []),
                        progress_callback=update_video_progress,
                    )
                    generated_video.update(
                        {
                            "description": "依据个性化分镜生成的讯飞配音 MP4 微课。",
                            "duration": _format_duration(rendered.duration_seconds),
                            "url": f"/producer/video/{task_id}",
                            "media_status": "ready",
                            "rendering_mode": "mp4_tts_ffmpeg",
                            "mp4_available": True,
                            "narration_provider": rendered.narration_provider,
                            "voice": rendered.voice,
                        }
                    )
                except VideoRenderError as exc:
                    logger.warning("Video rendering failed for task %s: %s", task_id, exc)
                    generated_video["render_error"] = str(exc)
            task.result_json = result
            task.progress = max(95, task.progress)
            db.commit()
            _stop_if_cancelled(db, task)

        db.query(ProducerArtifact).filter(ProducerArtifact.task_id == task_id).delete()
        db.add_all(_artifact_rows(task_id, result, requested_types))
        task.result_json = result
        task.status = "completed"
        task.progress = 100
        task.error_message = None
        db.commit()
    except ProducerTaskCancelled:
        db.rollback()
        cancelled_task = _task_or_404(db, task_id)
        cancelled_task.status = "cancelled"
        cancelled_task.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        failed_task = _task_or_404(db, task_id)
        failed_task.status = "failed"
        failed_task.error_message = str(exc)
        db.commit()
        raise


def run_producer_task(task_id: str) -> None:
    """RQ-compatible producer job with persisted progress and deterministic fallback."""
    with SessionLocal() as db:
        _execute_producer_task(db, task_id)


def _producer_job_id(task_id: str) -> str:
    """Build an RQ-compatible ID (RQ rejects IDs containing colons)."""
    return f"producer-{task_id}"


def _format_duration(seconds: float) -> str:
    rounded = max(0, int(round(seconds)))
    minutes, remaining = divmod(rounded, 60)
    return f"{minutes} 分 {remaining:02d} 秒" if minutes else f"{remaining} 秒"


def _enqueue_producer_task(task_id: str) -> bool:
    settings = get_settings()
    if not settings.producer_async_enabled:
        return False
    try:
        from redis import Redis
        from rq import Queue

        connection = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=0.35,
            socket_timeout=0.35,
        )
        connection.ping()
        Queue("default", connection=connection).enqueue(
            run_producer_task,
            task_id,
            job_id=_producer_job_id(task_id),
            job_timeout=settings.producer_job_timeout_seconds,
            result_ttl=3600,
            failure_ttl=86400,
        )
        return True
    except Exception as exc:
        logger.warning("Producer queue unavailable; using synchronous execution: %s", exc)
        return False


def _cancel_queued_job(task_id: str) -> None:
    settings = get_settings()
    try:
        from redis import Redis
        from rq.job import Job

        connection = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=0.35,
            socket_timeout=0.35,
        )
        Job.fetch(_producer_job_id(task_id), connection=connection).cancel()
    except Exception as exc:
        logger.warning("Unable to cancel queued producer job %s: %s", task_id, exc)
        return


@router.post("/task")
def create_task(
    payload: ProducerTaskRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_user),
) -> dict:
    task_id = uuid4().hex
    topic = payload.topic.strip() or "通用学习主题"
    requested_types = _normalize_types(payload.types)
    task = ProducerTask(
        task_id=task_id,
        user_id=current_user.id if current_user else None,
        topic=topic,
        requirement=payload.requirement,
        task_type=payload.task_type,
        status="pending",
        progress=0,
        result_json={"requested_types": requested_types},
    )
    db.add(task)
    db.commit()

    queued = _enqueue_producer_task(task_id)
    if not queued:
        try:
            _execute_producer_task(db, task_id)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Producer task failed"
            ) from exc
    db.expire_all()
    task = _task_or_404(db, task_id)

    return {
        "task_id": task_id,
        "status": task.status,
        "progress": task.progress,
        "message": "任务已进入生成队列" if queued else "任务已完成（同步降级模式）",
        "execution_mode": "async" if queued else "sync_fallback",
    }


@router.get("/tasks")
def list_student_tasks(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_user),
) -> dict:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    rows = (
        db.query(ProducerTask)
        .filter(ProducerTask.user_id == current_user.id)
        .order_by(ProducerTask.id.desc())
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "task_id": task.task_id,
                "topic": task.topic,
                "requirement": task.requirement or "",
                "status": task.status,
                "progress": int(task.progress or 0),
                "task_type": task.task_type,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "error_message": task.error_message,
            }
            for task in rows
        ],
        "total": len(rows),
    }


def _authorize_task(task: ProducerTask, current_user: User | None) -> None:
    if task.user_id is None and current_user is None:
        return
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if task.user_id != current_user.id and not (bool(current_user.is_admin) or current_user.role == "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Task access denied")


@router.get("/task/{task_id}")
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_user),
) -> dict:
    task = _task_or_404(db, task_id)
    _authorize_task(task, current_user)
    return {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "error_message": task.error_message,
    }


@router.post("/task/{task_id}/cancel")
def cancel_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_user),
) -> dict:
    task = _task_or_404(db, task_id)
    _authorize_task(task, current_user)
    if task.status == "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed task cannot be cancelled")
    if task.status == "cancelled":
        return {"task_id": task_id, "status": task.status, "progress": int(task.progress or 0)}
    if task.status == "failed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Failed task should be retried")
    task.status = "cancelled"
    task.error_message = None
    db.commit()
    _cancel_queued_job(task_id)
    return {"task_id": task_id, "status": "cancelled", "progress": int(task.progress or 0)}


@router.post("/task/{task_id}/retry")
def retry_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_user),
) -> dict:
    task = _task_or_404(db, task_id)
    _authorize_task(task, current_user)
    if task.status not in {"failed", "cancelled"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only failed or cancelled tasks can be retried",
        )
    existing = task.result_json if isinstance(task.result_json, dict) else {}
    requested_types = _normalize_types(existing.get("requested_types") or DEFAULT_TYPES)
    task.status = "pending"
    task.progress = 0
    task.error_message = None
    task.result_json = {"requested_types": requested_types}
    db.commit()

    queued = _enqueue_producer_task(task_id)
    if not queued:
        try:
            _execute_producer_task(db, task_id)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Producer retry failed") from exc
    db.expire_all()
    task = _task_or_404(db, task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "progress": int(task.progress or 0),
        "execution_mode": "async" if queued else "sync_fallback",
    }


@router.get("/result/{task_id}")
def get_task_result(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_user),
) -> dict:
    task = _task_or_404(db, task_id)
    _authorize_task(task, current_user)
    return {
        "task_id": task.task_id,
        "status": task.status,
        "result": task.result_json or {},
    }


@router.get("/export/{task_id}")
def export_task_result(
    task_id: str,
    format: str = Query(default="docx", pattern="^(docx|pptx|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_user),
) -> StreamingResponse:
    task = _task_or_404(db, task_id)
    _authorize_task(task, current_user)
    if task.status != "completed" or not task.result_json:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task result is not ready for export")
    try:
        exported = learning_resource_export_service.export(task.result_json, format)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    disposition = f"attachment; filename*=UTF-8''{quote(exported.filename)}"
    return StreamingResponse(
        io.BytesIO(exported.content),
        media_type=exported.media_type,
        headers={
            "Content-Disposition": disposition,
            "Content-Length": str(len(exported.content)),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/video/{task_id}")
def stream_task_video(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_user),
) -> FileResponse:
    task = _task_or_404(db, task_id)
    _authorize_task(task, current_user)
    result = task.result_json if isinstance(task.result_json, dict) else {}
    video = next((item for item in result.get("videos", []) if item.get("mp4_available")), None)
    if task.status != "completed" or video is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task video is not ready")
    path = (get_settings().video_output_path / f"{task_id}.mp4").resolve()
    if path.parent != get_settings().video_output_path or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task video file is missing")
    filename = f"{re.sub(r'[^A-Za-z0-9_-]+', '-', task.topic).strip('-') or 'learnpilot'}-{task_id[:8]}.mp4"
    return FileResponse(
        Path(path),
        media_type="video/mp4",
        filename=filename,
        content_disposition_type="inline",
        headers={"Cache-Control": "private, max-age=3600", "X-Content-Type-Options": "nosniff"},
    )


@router.post("/chat")
def producer_chat(payload: ProducerChatRequest, db: Session = Depends(get_db)) -> dict:
    session_id = payload.session_id or uuid4().hex
    message = payload.message.strip()
    reply = (
        f"{payload.topic} 可以从基础概念、核心原理、例题验证和代码实践四个层次理解。"
        f"针对“{message}”，建议先明确相关术语和输入输出，再用一个最小案例逐步验证。"
        "如果某一步无法解释原因，就把它记录为薄弱点，并配合练习题和路线图继续学习。"
    )
    db.add_all(
        [
            ProducerChatMessage(session_id=session_id, role="user", content=message),
            ProducerChatMessage(session_id=session_id, role="assistant", content=reply),
        ]
    )
    db.commit()
    return {"session_id": session_id, "reply": reply}


@router.get("/roadmap")
def get_roadmap(topic: str = Query(min_length=1, max_length=255)) -> dict:
    return {"topic": topic, "nodes": _roadmap_nodes(topic)}


@router.get("/exercises")
def get_exercises(topic: str = Query(min_length=1, max_length=255)) -> dict:
    return {"topic": topic, "items": _exercise_items(topic)}


@router.get("/videos")
def get_videos(
    topic: str = Query(min_length=1, max_length=255),
    db: Session = Depends(get_db),
) -> dict:
    return {"topic": topic, "items": _video_items(db, topic)}


@router.get("/code")
def get_code(
    topic: str = Query(min_length=1, max_length=255),
    language: str = Query(default="python", max_length=32),
) -> dict:
    return {"topic": topic, "language": language.lower(), "items": _code_items(topic, language)}


def _simulate_python_output(code: str) -> tuple[bool, str, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, "", f"语法检查失败：{exc.msg}"

    output_lines = []
    for node in tree.body:
        if not (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "print"
        ):
            continue
        values = []
        for argument in node.value.args:
            try:
                values.append(str(ast.literal_eval(argument)))
            except (ValueError, TypeError):
                values.append("<表达式结果>")
        output_lines.append(" ".join(values))
    output = "\n".join(output_lines) or "模拟运行完成（安全模式未执行用户代码）"
    return True, output, ""


@router.post("/run")
def run_code(payload: ProducerRunRequest) -> dict:
    language = payload.language.lower()
    if language == "python":
        success, output, error = _simulate_python_output(payload.code)
    else:
        literal = re.search(r"console\.log\(\s*(['\"])(.*?)\1\s*\)", payload.code, re.DOTALL)
        success, output, error = True, literal.group(2) if literal else "模拟运行完成（安全模式未执行用户代码）", ""
    return {"success": success, "output": output, "error": error}


@router.get("/datasets")
def get_datasets(keyword: str = Query(min_length=1, max_length=255)) -> dict:
    return {"keyword": keyword, "items": _dataset_items(keyword)}
