import hashlib
import json
import os
import posixpath
import re
from pathlib import Path


VERSION_PATTERN = r"^v([0-9]|[1-9][0-9])(\.([1-9]|[1-9][0-9]))?$"
DATABASE_ROOT = Path(os.path.expanduser("~/pCloud Drive/(4) Database"))
CS_REFILL_ROOT = DATABASE_ROOT / "02_Execution"
MANIFEST_FILE_NAME = "manifest.json"
MANIFEST_SCHEMA_VERSION = 2
SNAPSHOT_DIR_NAME = "__snapshot"
HISTORY_DIR_NAME = "__history"
LEGACY_HISTORY_DIR_NAME = "_history"

# Paths that must never be reconstructed/refilled from snapshots.
SKIP_RESTORE_PREFIXES = (
    ".git/",
    "__install/",
    "node_modules/",
    "dist/",
    "build/",
    "target/",
    "release/",
    "out/",
    ".venv/",
    "__pycache__/",
    "frontend/src-tauri/binaries/",
    "frontend/src-tauri/target/",
    "frontend/node_modules/",
    "frontend/dist/",
    "landing/node_modules/",
    "landing/dist/",
    "backend/.venv/",
    "backend/__pycache__/",
    "backend/dist/",
    "backend/build/",
    "electron/dist/",
    "electron/out/",
    "electron/release/",
    "android/",
    "ios/",
)

SKIP_RESTORE_CONTAINS = (
    ".app/Contents/MacOS/",
    ".app/Contents/Frameworks/",
)

SKIP_RESTORE_SUFFIXES = (
    ".pyc",
    ".dmg",
    ".apk",
    ".aab",
    ".ipa",
    ".exe",
)


def is_valid_version(version):
    return bool(re.match(VERSION_PATTERN, version))


def sanitize_version_path(path):
    return path.strip().split("->", 1)[0].strip()


def normalize_snapshot_rel_path(path):
    candidate = sanitize_version_path(path)
    if not candidate or "\\x00" in candidate:
        raise ValueError("empty or invalid path")

    had_trailing_slash = candidate.endswith("/")
    normalized = posixpath.normpath(candidate.replace("\\", "/"))

    if normalized in ("", ".", ".."):
        raise ValueError("invalid relative path")
    if normalized.startswith("../") or normalized.startswith("/"):
        raise ValueError("path escapes project root")
    if "/../" in f"/{normalized}/":
        raise ValueError("path escapes project root")

    if had_trailing_slash:
        normalized += "/"
    return normalized


def safe_join_project_root(project_root, rel_path):
    normalized_rel = normalize_snapshot_rel_path(rel_path)
    rel_for_fs = normalized_rel.rstrip("/")

    abs_root = os.path.realpath(project_root)
    abs_target = os.path.realpath(os.path.join(abs_root, rel_for_fs))

    if os.path.commonpath([abs_root, abs_target]) != abs_root:
        raise ValueError("resolved path is outside project root")

    return normalized_rel, abs_target


def should_skip_restore_path(rel_path, extra_suffixes=()):
    normalized = rel_path.strip().replace("\\", "/")
    if any(normalized.startswith(prefix) for prefix in SKIP_RESTORE_PREFIXES):
        return True
    if any(token in normalized for token in SKIP_RESTORE_CONTAINS):
        return True
    if any(normalized.endswith(suffix) for suffix in SKIP_RESTORE_SUFFIXES):
        return True
    if any(normalized.endswith(suffix) for suffix in extra_suffixes):
        return True
    return False


def detect_project_name(project_root):
    root = Path(project_root).resolve()
    if re.match(r"^[0-9]{2}_.+", root.name):
        return root.name
    return root.parent.name


def default_refill_source(project_root):
    project_name = detect_project_name(project_root)
    return CS_REFILL_ROOT / project_name / "v0"


def project_snapshot_root(project_root):
    return default_refill_source(project_root).parent


def history_root(project_root):
    return project_snapshot_root(project_root) / LEGACY_HISTORY_DIR_NAME


def history_roots(project_root):
    """Return existing history roots (new + legacy)."""
    snapshot_root = project_snapshot_root(project_root)
    roots = []
    new_root = snapshot_root / HISTORY_DIR_NAME
    if new_root.is_dir():
        roots.append(new_root)
    legacy_root = snapshot_root / LEGACY_HISTORY_DIR_NAME
    if legacy_root.is_dir():
        roots.append(legacy_root)
    return roots


def manifest_path(install_folder):
    return Path(install_folder) / MANIFEST_FILE_NAME


def write_manifest(install_folder, payload):
    path = manifest_path(install_folder)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def load_manifest(install_folder):
    path = manifest_path(install_folder)
    if not path.is_file():
        raise FileNotFoundError(f"manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest_file(path):
    manifest_path_obj = Path(path)
    if not manifest_path_obj.is_file():
        raise FileNotFoundError(f"manifest not found: {manifest_path_obj}")
    return json.loads(manifest_path_obj.read_text(encoding="utf-8"))


def file_sha256(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def file_metadata(path):
    stat = os.stat(path)
    return {
        "size": stat.st_size,
        "mtime": int(stat.st_mtime),
        "sha256": file_sha256(path),
    }


def find_snapshot_source_by_label(project_root, snapshot_label):
    label = (snapshot_label or "").strip()
    if not label:
        raise ValueError("snapshot label is empty")
    if not is_valid_version(label):
        raise ValueError(f"invalid snapshot label: {label}")

    live_root = default_refill_source(project_root)
    snapshot_root = project_snapshot_root(project_root)
    candidates = [live_root]

    version_root = snapshot_root / label
    if label != "v0" and version_root.is_dir():
        candidates.append(version_root)

    for hist_root in history_roots(project_root):
        candidates.extend(
            path for path in sorted(hist_root.iterdir(), reverse=True)
            if path.is_dir() and path.name != ".DS_Store"
        )

    seen = set()
    for source_root in candidates:
        source_real = source_root.resolve()
        if source_real in seen:
            continue
        seen.add(source_real)

        manifest_file = source_root / SNAPSHOT_DIR_NAME / MANIFEST_FILE_NAME
        if not manifest_file.is_file():
            continue
        manifest = load_manifest_file(manifest_file)
        if (manifest.get("snapshot_label") or "").strip() == label:
            return source_root, manifest

    return None, None
