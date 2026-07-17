"""Build and verify the distributable Microsoft AI for Beginners course subset."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SOURCE = REPOSITORY_ROOT / "backend" / "src"
if str(BACKEND_SOURCE) not in sys.path:
    sys.path.insert(0, str(BACKEND_SOURCE))

from backend.app.services.course_materials import PATH_TO_KNOWLEDGE_POINT  # noqa: E402

DEFAULT_SOURCE = REPOSITORY_ROOT / "data" / "external" / "course-materials" / "ai-for-beginners"
DEFAULT_DESTINATION = REPOSITORY_ROOT / "backend" / "data" / "course_materials" / "ai-for-beginners"
LESSONS_RELATIVE = Path("translations/zh-CN/lessons")
RECEIPT_NAME = ".learnpilot-source.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mapping_key(relative: str) -> str:
    normalized = relative.removesuffix("/README.md").removesuffix("/lab")
    if normalized not in PATH_TO_KNOWLEDGE_POINT:
        raise ValueError(f"unmapped course document: {relative}")
    return normalized


def discover_documents(source_root: Path) -> list[tuple[Path, str, str]]:
    lessons_root = source_root / LESSONS_RELATIVE
    if not lessons_root.is_dir():
        raise FileNotFoundError(f"Chinese lessons directory is missing: {lessons_root}")
    documents: list[tuple[Path, str, str]] = []
    for path in sorted(lessons_root.rglob("README.md")):
        relative = path.relative_to(lessons_root).as_posix()
        try:
            key = mapping_key(relative)
        except ValueError:
            continue
        if not path.read_text(encoding="utf-8").strip():
            raise ValueError(f"course document is empty: {relative}")
        documents.append((path, relative, PATH_TO_KNOWLEDGE_POINT[key]))
    if len(documents) != 37:
        raise ValueError(f"expected 37 mapped course documents, found {len(documents)}")
    return documents


def build_bundle(source_root: Path, destination: Path) -> dict:
    source_root = source_root.resolve()
    destination = destination.resolve()
    allowed_parent = (REPOSITORY_ROOT / "backend" / "data" / "course_materials").resolve()
    if destination.parent != allowed_parent:
        raise ValueError(f"bundle destination must be directly under {allowed_parent}")

    source_receipt_path = source_root / RECEIPT_NAME
    license_path = source_root / "LICENSE"
    if not source_receipt_path.is_file() or not license_path.is_file():
        raise FileNotFoundError("source receipt or MIT license is missing; synchronize the external source first")
    source_receipt = json.loads(source_receipt_path.read_text(encoding="utf-8"))
    if source_receipt.get("source_id") != "microsoft-ai-for-beginners":
        raise ValueError("unexpected source receipt")

    documents = discover_documents(source_root)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    shutil.copyfile(license_path, destination / "LICENSE")

    manifest_documents = []
    for source_path, relative, knowledge_point in documents:
        bundled_relative = LESSONS_RELATIVE / Path(relative)
        target = destination / bundled_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target)
        manifest_documents.append(
            {
                "path": bundled_relative.as_posix(),
                "sha256": sha256_file(target),
                "knowledge_point": knowledge_point,
            }
        )

    receipt = {
        "schema_version": "1.0",
        "source_id": "microsoft-ai-for-beginners",
        "upstream": source_receipt["upstream"],
        "revision": source_receipt["revision"],
        "license": "MIT",
        "bundle_type": "curated-runtime-course-materials",
        "document_count": len(manifest_documents),
        "license_sha256": sha256_file(destination / "LICENSE"),
        "documents": manifest_documents,
    }
    canonical = json.dumps(manifest_documents, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    receipt["document_manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    (destination / RECEIPT_NAME).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    verify_bundle(destination)
    return receipt


def verify_bundle(destination: Path) -> dict:
    destination = destination.resolve()
    receipt_path = destination / RECEIPT_NAME
    if not receipt_path.is_file():
        raise FileNotFoundError(f"bundle receipt is missing: {receipt_path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    documents = receipt.get("documents") or []
    if receipt.get("source_id") != "microsoft-ai-for-beginners" or len(documents) != 37:
        raise ValueError("course bundle receipt is invalid")
    if sha256_file(destination / "LICENSE") != receipt.get("license_sha256"):
        raise ValueError("course bundle license hash mismatch")
    for document in documents:
        relative = Path(str(document["path"]))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe course bundle path: {relative}")
        path = destination / relative
        if not path.is_file() or sha256_file(path) != document["sha256"]:
            raise ValueError(f"course bundle document hash mismatch: {document['path']}")
    canonical = json.dumps(documents, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != receipt.get("document_manifest_sha256"):
        raise ValueError("course bundle manifest hash mismatch")
    expected = {RECEIPT_NAME, "LICENSE", *(str(item["path"]) for item in documents)}
    actual = {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    }
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unexpected or missing:
        raise ValueError(f"course bundle file set mismatch; missing={missing}, unexpected={unexpected}")
    return {
        "status": "ok",
        "documents": len(documents),
        "revision": receipt["revision"],
        "document_manifest_sha256": receipt["document_manifest_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    result = (
        build_bundle(args.source, args.destination)
        if args.command == "build"
        else verify_bundle(args.destination)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
