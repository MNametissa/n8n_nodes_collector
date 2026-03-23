"""
Starter script: bootstrap an inventory file from a manually curated list of n8n doc URLs.

This script does not scrape the web in this environment.
It creates a starter inventory JSON that a real collector can later enrich.
"""

from __future__ import annotations
import json
from pathlib import Path

SEED_URLS = [
    "https://docs.n8n.io/integrations/",
    "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
    "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-langchain.openai/",
    "https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/",
    "https://docs.n8n.io/advanced-ai/langchain/langchain-n8n/",
]


def main() -> None:
    out = Path(__file__).resolve().parent / "inventory.seed.json"
    payload = {
        "source": "manual_seed",
        "urls": SEED_URLS,
        "note": "Replace this seed with a collector that discovers all official node pages."
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
