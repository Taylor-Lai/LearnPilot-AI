"""Verify and synchronize allowlisted external project inputs.

External files remain outside Git. The committed ``data/sources.yaml`` is the
single source of truth for origin, revision, checksum, license and local path.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import http.client
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPOSITORY_ROOT / "data" / "sources.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage allowlisted LearnPilot external sources.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify_parser = subparsers.add_parser("verify", help="verify local source revisions and checksums")
    verify_parser.add_argument("source_id", nargs="?", default="all")
    sync_parser = subparsers.add_parser("sync", help="synchronize a pinned course source")
    sync_parser.add_argument("source_id")
    sync_parser.add_argument("--proxy", help="HTTP(S) proxy URL used for source downloads")
    args = parser.parse_args()

    sources = _load_sources()
    selected = sources if args.source_id == "all" else [_source_by_id(sources, args.source_id)]
    if args.command == "sync":
        _sync_course_source(selected[0], proxy=args.proxy)
    results = [_verify_source(source) for source in selected]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(result["status"] in {"ok", "reference-only"} for result in results) else 1


def _load_sources() -> list[dict]:
    document = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if document.get("schema_version") != "1.0" or not isinstance(document.get("sources"), list):
        raise ValueError("data/sources.yaml has an unsupported schema")
    return document["sources"]


def _source_by_id(sources: list[dict], source_id: str) -> dict:
    for source in sources:
        if source.get("id") == source_id:
            return source
    raise ValueError(f"unknown source id: {source_id}")


def _local_path(source: dict) -> Path:
    raw = source.get("local_path")
    if not raw:
        raise ValueError(f"source {source['id']} has no local_path")
    path = (REPOSITORY_ROOT / str(raw)).resolve()
    if REPOSITORY_ROOT not in path.parents:
        raise ValueError(f"source path escapes repository: {path}")
    return path


def _sync_course_source(source: dict, *, proxy: str | None = None) -> None:
    if source.get("kind") != "course-material" or source.get("distribution") != "ignored":
        raise ValueError("only ignored course-material sources can be synchronized")
    if source.get("sync_strategy") == "github-files":
        _sync_github_files(source, proxy=proxy)
        return
    _sync_git_source(source)


def _sync_git_source(source: dict) -> None:
    upstream = str(source["upstream"])
    revision = str(source["revision"])
    destination = _local_path(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not (destination / ".git").is_dir():
        if destination.exists() and any(destination.iterdir()):
            raise ValueError(f"refusing to clone into non-empty directory: {destination}")
        _run("git", "clone", "--filter=blob:none", "--no-checkout", upstream, str(destination))
    origin = _git(destination, "remote", "get-url", "origin", capture=True).strip()
    if origin.rstrip("/").removesuffix(".git").lower() != upstream.rstrip("/").removesuffix(".git").lower():
        raise ValueError(f"unexpected origin for {source['id']}: {origin}")
    _git(destination, "fetch", "--depth", "1", "origin", revision)
    patterns = [f"/{item.rstrip('/')}" + ("/" if item.endswith("/") else "") for item in source["sparse_paths"]]
    _git(destination, "sparse-checkout", "init", "--no-cone")
    _git(destination, "sparse-checkout", "set", "--no-cone", *patterns)
    _git(destination, "checkout", "--detach", revision)
    receipt = {
        "source_id": source["id"],
        "upstream": upstream,
        "revision": revision,
        "license": source["license"],
    }
    (destination / ".learnpilot-source.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _sync_github_files(source: dict, *, proxy: str | None) -> None:
    upstream = str(source["upstream"])
    revision = str(source["revision"])
    destination = _local_path(source)
    repository = upstream.removesuffix(".git").removeprefix("https://github.com/")
    if "/" not in repository or repository.startswith("http"):
        raise ValueError(f"unsupported GitHub upstream: {upstream}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not (destination / ".git").is_dir():
        _run(
            "git",
            *_git_network_options(proxy),
            "clone",
            "--filter=blob:none",
            "--no-checkout",
            "--depth",
            "1",
            upstream,
            str(destination),
        )
    _git_with_network(destination, proxy, "fetch", "--depth", "1", "--filter=blob:none", "origin", revision)
    tree = _git(destination, "ls-tree", "-r", revision, capture=True)
    entries = _select_course_files(tree, source)
    if not entries:
        raise ValueError(f"no allowlisted files found for {source['id']}")
    completed = 0

    def synchronize(entry: tuple[str, str]) -> str:
        path, blob_sha = entry
        target = (destination / path).resolve()
        if destination.resolve() not in target.parents:
            raise ValueError(f"source path escapes destination: {path}")
        if target.is_file() and _git_blob_sha(target.read_bytes()) == blob_sha:
            return path
        url_path = urllib.parse.quote(path, safe="/")
        url = f"https://raw.githubusercontent.com/{repository}/{revision}/{url_path}"
        _download(url, target, proxy=proxy, expected_blob_sha=blob_sha)
        return path

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(synchronize, entry) for entry in entries]
        for future in concurrent.futures.as_completed(futures):
            future.result()
            completed += 1
            if completed % 25 == 0 or completed == len(entries):
                print(f"synchronized {completed}/{len(entries)} files", flush=True)
    manifest_digest = hashlib.sha256(
        "\n".join(f"{path}:{blob_sha}" for path, blob_sha in entries).encode()
    ).hexdigest()
    receipt = {
        "source_id": source["id"],
        "upstream": upstream,
        "revision": revision,
        "license": source["license"],
        "file_count": len(entries),
        "file_manifest_sha256": manifest_digest,
        "included_paths": source["sparse_paths"],
    }
    (destination / ".learnpilot-source.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    destination.with_suffix(".zip").unlink(missing_ok=True)
    destination.with_suffix(".zip.part").unlink(missing_ok=True)


def _download(url: str, destination: Path, *, proxy: str | None, expected_blob_sha: str) -> None:
    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    opener = urllib.request.build_opener(*handlers)
    temporary = destination.with_suffix(destination.suffix + ".part")
    destination.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, 6):
        existing = temporary.stat().st_size if temporary.exists() else 0
        headers = {"User-Agent": "LearnPilot-source-manager/1.0"}
        if existing:
            headers["Range"] = f"bytes={existing}-"
        request = urllib.request.Request(url, headers=headers)
        try:
            with opener.open(request, timeout=120) as response:
                append = existing > 0 and response.status == 206
                with temporary.open("ab" if append else "wb") as output:
                    while chunk := response.read(256 * 1024):
                        output.write(chunk)
            content = temporary.read_bytes()
            if _git_blob_sha(content) != expected_blob_sha:
                raise ValueError(f"Git blob checksum mismatch for {destination}")
            temporary.replace(destination)
            return
        except (OSError, http.client.IncompleteRead, urllib.error.URLError, ValueError):
            if attempt == 5:
                raise
            time.sleep(attempt * 2)


def _select_course_files(tree: str, source: dict) -> list[tuple[str, str]]:
    allowed_files = {item.strip("/") for item in source["sparse_paths"] if not item.endswith("/")}
    allowed_directories = tuple(
        item.strip("/") + "/" for item in source["sparse_paths"] if item.endswith("/")
    )
    extensions = {str(extension).lower() for extension in source["include_extensions"]}
    selected: list[tuple[str, str]] = []
    for line in tree.splitlines():
        metadata, path = line.split("\t", 1)
        _, kind, blob_sha = metadata.split()
        if kind != "blob":
            continue
        included = path in allowed_files or path.startswith(allowed_directories)
        if included and (path in allowed_files or Path(path).suffix.lower() in extensions):
            selected.append((path, blob_sha))
    return sorted(selected)


def _git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def _git_network_options(proxy: str | None) -> tuple[str, ...]:
    options = ["-c", "http.sslBackend=openssl", "-c", "http.version=HTTP/1.1", "-c", "credential.helper="]
    if proxy:
        options.extend(("-c", f"http.proxy={proxy}"))
    return tuple(options)


def _git_with_network(repository: Path, proxy: str | None, *arguments: str) -> None:
    _run(
        "git",
        "-c",
        f"safe.directory={repository.as_posix()}",
        *_git_network_options(proxy),
        "-C",
        str(repository),
        *arguments,
    )


def _verify_source(source: dict) -> dict[str, str]:
    if source.get("distribution") == "link-only":
        return {"id": source["id"], "status": "reference-only"}
    path = _local_path(source)
    if not path.exists():
        return {"id": source["id"], "status": "missing", "path": str(path)}
    if source.get("kind") == "dataset":
        actual = _sha256(path)
        status = "ok" if actual == source.get("sha256") else "checksum-mismatch"
        return {"id": source["id"], "status": status, "sha256": actual}
    if source.get("kind") == "course-material":
        receipt_path = path / ".learnpilot-source.json"
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            revision = str(receipt.get("revision", ""))
        elif (path / ".git").is_dir():
            revision = _git(path, "rev-parse", "HEAD", capture=True).strip()
        else:
            return {"id": source["id"], "status": "invalid-course-source"}
        required = (path / "LICENSE").is_file() and (path / "lessons").is_dir()
        result: dict[str, str | int] = {"id": source["id"], "revision": revision}
        if source.get("sync_strategy") == "github-files" and (path / ".git").is_dir():
            tree = _git(path, "ls-tree", "-r", revision, capture=True)
            entries = _select_course_files(tree, source)
            invalid = [
                relative
                for relative, blob_sha in entries
                if not (path / relative).is_file()
                or _git_blob_sha((path / relative).read_bytes()) != blob_sha
            ]
            result["files_verified"] = len(entries) - len(invalid)
            if invalid:
                result.update(status="checksum-mismatch", invalid_files=len(invalid))
                return result
        result["status"] = "ok" if revision == source.get("revision") and required else "incomplete"
        return result
    return {"id": source["id"], "status": "unsupported-kind"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(*command: str, capture: bool = False) -> str:
    completed = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        check=True,
        text=True,
        capture_output=capture,
    )
    return completed.stdout if capture else ""


def _git(repository: Path, *arguments: str, capture: bool = False) -> str:
    return _run(
        "git",
        "-c",
        f"safe.directory={repository.as_posix()}",
        "-C",
        str(repository),
        *arguments,
        capture=capture,
    )


if __name__ == "__main__":
    raise SystemExit(main())
