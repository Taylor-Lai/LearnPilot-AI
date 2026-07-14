from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

from sqlalchemy.orm import Session

from backend.app.models import CourseResource, KnowledgePoint, ResourceChunk

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
SOURCE_RELATIVE_PATH = Path("data/external/course-materials/ai-for-beginners")
UPSTREAM = "https://github.com/microsoft/AI-For-Beginners"

PATH_TO_KNOWLEDGE_POINT = {
    "1-Intro": "人工智能概述",
    "2-Symbolic": "知识图谱",
    "3-NeuralNetworks/03-Perceptron": "感知机",
    "3-NeuralNetworks/04-OwnFramework": "反向传播",
    "3-NeuralNetworks/05-Frameworks": "多层神经网络",
    "4-ComputerVision/06-IntroCV": "计算机视觉实验",
    "4-ComputerVision/07-ConvNets": "CNN",
    "4-ComputerVision/08-TransferLearning": "迁移学习",
    "4-ComputerVision/09-Autoencoders": "深度网络正则化",
    "4-ComputerVision/10-GANs": "计算机视觉实验",
    "4-ComputerVision/11-ObjectDetection": "计算机视觉实验",
    "4-ComputerVision/12-Segmentation": "计算机视觉实验",
    "5-NLP/13-TextRep": "文本表示",
    "5-NLP/14-Embeddings": "文本表示",
    "5-NLP/15-LanguageModeling": "文本表示",
    "5-NLP/16-RNN": "注意力机制",
    "5-NLP/17-GenerativeNetworks": "大模型与RAG",
    "5-NLP/18-Transformers": "Transformer",
    "5-NLP/19-NER": "文本表示",
    "5-NLP/20-LangModels": "大模型与RAG",
    "6-Other/21-GeneticAlgorithms": "机器学习基础",
    "6-Other/22-DeepRL": "智能体与环境",
    "6-Other/23-MultiagentSystems": "智能体与环境",
    "7-Ethics": "人工智能安全与伦理",
    "X-Extras/X1-MultiModal": "人工智能综合项目",
}


def ingest_ai_for_beginners(
    db: Session,
    course_id: int,
    source_root: Path | None = None,
) -> dict[str, int | str]:
    source_root = resolve_course_source_root(source_root)
    receipt = _load_receipt(source_root)
    lessons_root = source_root / "translations" / "zh-CN" / "lessons"
    points = {
        point.name: point
        for point in db.query(KnowledgePoint).filter(KnowledgePoint.course_id == course_id).all()
    }
    missing_points = set(PATH_TO_KNOWLEDGE_POINT.values()) - set(points)
    if missing_points:
        raise ValueError(f"course catalog is missing mapped knowledge points: {sorted(missing_points)}")

    documents = _discover_documents(lessons_root)
    resources_created = 0
    chunks_written = 0
    for document in documents:
        relative = document.relative_to(lessons_root).as_posix()
        mapping_key = _mapping_key(relative)
        point = points[PATH_TO_KNOWLEDGE_POINT[mapping_key]]
        content = document.read_text(encoding="utf-8").strip()
        if not content:
            continue
        source = f"ai-for-beginners:{relative}"
        resource = (
            db.query(CourseResource)
            .filter(CourseResource.course_id == course_id, CourseResource.source == source)
            .first()
        )
        if resource is None:
            resource = CourseResource(course_id=course_id, title=_document_title(document, content))
            db.add(resource)
            resources_created += 1
        resource.knowledge_point_id = point.id
        resource.title = _document_title(document, content)
        resource.resource_type = "lab" if "/lab/" in f"/{relative}" else "reading"
        resource.content = content
        resource.source = source
        resource.source_type = "markdown"
        resource.status = "published"
        resource.version = str(receipt["revision"])[:12]
        resource.resource_metadata = _resource_metadata(receipt, relative, content, point.name)
        db.flush()
        db.query(ResourceChunk).filter(ResourceChunk.resource_id == resource.id).delete()
        for index, chunk in enumerate(_split_markdown(content), start=1):
            db.add(
                ResourceChunk(
                    resource_id=resource.id,
                    course_id=course_id,
                    chunk_index=index,
                    content=chunk,
                    token_count=len(chunk),
                    keywords=_keywords(chunk),
                    embedding=None,
                )
            )
            chunks_written += 1
    return {
        "source_revision": str(receipt["revision"]),
        "documents": len(documents),
        "resources_created": resources_created,
        "chunks_written": chunks_written,
    }


def resolve_course_source_root(source_root: Path | None = None) -> Path:
    """Resolve the external course source consistently in local and container runs."""
    if source_root is not None:
        return Path(source_root).expanduser().resolve()
    override = os.getenv("LEARNPILOT_COURSE_SOURCE_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    candidates = [Path.cwd() / SOURCE_RELATIVE_PATH, REPOSITORY_ROOT / SOURCE_RELATIVE_PATH]
    for candidate in candidates:
        if (candidate / ".learnpilot-source.json").is_file():
            return candidate.resolve()
    return candidates[0].resolve()


def course_materials_available(source_root: Path | None = None) -> bool:
    root = resolve_course_source_root(source_root)
    return (root / ".learnpilot-source.json").is_file() and (
        root / "translations" / "zh-CN" / "lessons"
    ).is_dir()


def _load_receipt(source_root: Path) -> dict[str, Any]:
    receipt_path = source_root / ".learnpilot-source.json"
    if not receipt_path.is_file():
        raise FileNotFoundError(
            "Microsoft AI for Beginners is not synchronized; run tools/manage_sources.py sync first"
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("source_id") != "microsoft-ai-for-beginners" or not receipt.get("revision"):
        raise ValueError("invalid Microsoft AI for Beginners source receipt")
    return receipt


def _discover_documents(lessons_root: Path) -> list[Path]:
    if not lessons_root.is_dir():
        raise FileNotFoundError(f"Chinese course lessons are missing: {lessons_root}")
    documents = []
    for path in lessons_root.rglob("README.md"):
        relative = path.relative_to(lessons_root).as_posix()
        try:
            _mapping_key(relative)
        except ValueError:
            continue
        documents.append(path)
    return sorted(documents)


def _mapping_key(relative: str) -> str:
    normalized = relative.removesuffix("/README.md").removesuffix("/lab")
    if normalized in PATH_TO_KNOWLEDGE_POINT:
        return normalized
    raise ValueError(f"unmapped course document: {relative}")


def _document_title(path: Path, content: str) -> str:
    for line in content.splitlines():
        match = re.match(r"^#{1,3}\s+(.+)$", line.strip())
        if match:
            return re.sub(r"[*_`]", "", match.group(1)).strip()[:200]
    return path.parent.name.replace("-", " ")[:200]


def _resource_metadata(receipt: dict[str, Any], relative: str, content: str, point: str) -> dict[str, Any]:
    revision = str(receipt["revision"])
    source_path = f"translations/zh-CN/lessons/{relative}"
    return {
        "content_author": "Microsoft and AI for Beginners contributors",
        "content_license": "MIT",
        "source_name": "Microsoft AI for Beginners",
        "source_revision": revision,
        "source_path": source_path,
        "source_url": f"{UPSTREAM}/blob/{revision}/{quote(source_path, safe='/')}",
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "knowledge_point": point,
        "language": "zh-CN",
    }


def _split_markdown(content: str, chunk_size: int = 1200, overlap: int = 120) -> list[str]:
    sections = re.split(r"(?=^#{1,4}\s)", content, flags=re.MULTILINE)
    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        start = 0
        while start < len(section):
            end = min(len(section), start + chunk_size)
            if end < len(section):
                boundary = max(section.rfind("\n\n", start, end), section.rfind("。", start, end))
                if boundary > start + chunk_size // 2:
                    end = boundary + 1
            chunks.append(section[start:end].strip())
            if end >= len(section):
                break
            start = max(start + 1, end - overlap)
    return [chunk for chunk in chunks if chunk]


def _keywords(content: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]+|[\u4e00-\u9fff]{2,}", content)
    return list(dict.fromkeys(word.casefold() for word in words))[:24]
