"""Static collector configuration."""

from __future__ import annotations

from pathlib import Path

OFFICIAL_DOCS_BASE = "https://docs.n8n.io"
BUILTIN_PREFIX = f"{OFFICIAL_DOCS_BASE}/integrations/builtin/"

DISCOVERY_SEED_URLS = [
    f"{OFFICIAL_DOCS_BASE}/integrations/",
]

DISCOVERY_LIBRARY_URLS = [
    f"{OFFICIAL_DOCS_BASE}/integrations/builtin/app-nodes/",
    f"{OFFICIAL_DOCS_BASE}/integrations/builtin/core-nodes/",
    f"{OFFICIAL_DOCS_BASE}/integrations/builtin/trigger-nodes/",
    f"{OFFICIAL_DOCS_BASE}/integrations/builtin/cluster-nodes/root-nodes/",
    f"{OFFICIAL_DOCS_BASE}/integrations/builtin/cluster-nodes/sub-nodes/",
]

REPO_ROOT = Path(__file__).resolve().parents[3]
CACHE_ROOT = REPO_ROOT / ".cache" / "n8n-nodes"
RAW_CACHE_DIR = CACHE_ROOT / "raw"
INTERMEDIATE_CACHE_DIR = CACHE_ROOT / "intermediate"
PACKAGE_DIR = REPO_ROOT / "package"
DEFAULT_FETCH_CONCURRENCY = 12

LIBRARY_PATH_HINTS = {
    "app-nodes",
    "core-nodes",
    "trigger-nodes",
    "cluster-nodes",
    "root-nodes",
    "sub-nodes",
}
