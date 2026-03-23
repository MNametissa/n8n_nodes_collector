"""Shared collector models."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Family(StrEnum):
    CORE = "core"
    ACTION = "action"
    TRIGGER = "trigger"
    CLUSTER_ROOT = "cluster_root"
    CLUSTER_SUB = "cluster_sub"


class SourceType(StrEnum):
    INDEX = "index"
    NODE_PAGE = "node_page"
    SUPPORTING_PAGE = "supporting_page"
    CONCEPT_PAGE = "concept_page"


class DiscoveryCandidate(BaseModel):
    """A discovered node page candidate."""

    model_config = ConfigDict(extra="forbid")

    url: str
    title: str
    family: Family
    source_url: str
    source_type: SourceType = SourceType.NODE_PAGE
    context: list[str] = Field(default_factory=list)


class DiscoveryReport(BaseModel):
    """Serializable discovery result."""

    model_config = ConfigDict(extra="forbid")

    source_urls: list[str] = Field(default_factory=list)
    candidates: list[DiscoveryCandidate] = Field(default_factory=list)

    def as_sorted_payload(self) -> dict[str, Any]:
        return {
            "source_urls": sorted(self.source_urls),
            "candidates": [
                candidate.model_dump(mode="json")
                for candidate in sorted(self.candidates, key=lambda item: (item.family, item.url))
            ],
        }

    @classmethod
    def from_path(cls, path: Path) -> "DiscoveryReport":
        """Load a discovery report from JSON."""

        return cls.model_validate_json(path.read_text(encoding="utf-8"))


class FetchRecord(BaseModel):
    """A fetched HTML source and its cache metadata."""

    model_config = ConfigDict(extra="forbid")

    url: str
    source_type: SourceType
    family: Family | None = None
    source_url: str | None = None
    http_status: int
    content_hash: str
    cache_path: str
    changed: bool


class FetchReport(BaseModel):
    """Serializable fetch output."""

    model_config = ConfigDict(extra="forbid")

    records: list[FetchRecord] = Field(default_factory=list)

    def as_sorted_payload(self) -> dict[str, Any]:
        return {
            "records": [
                record.model_dump(mode="json")
                for record in sorted(self.records, key=lambda item: (item.source_type, item.url))
            ]
        }

    @classmethod
    def from_path(cls, path: Path) -> "FetchReport":
        """Load a fetch report from JSON."""

        return cls.model_validate_json(path.read_text(encoding="utf-8"))


class ExtractedNodeRecord(BaseModel):
    """Intermediate extracted node record."""

    model_config = ConfigDict(extra="forbid")

    node_url: str
    display_name: str
    family_hint: Family
    source_url: str | None = None
    source_type: SourceType = SourceType.NODE_PAGE
    section_text: dict[str, list[str]] = Field(default_factory=dict)
    supporting_pages: list[str] = Field(default_factory=list)
    content_hashes: dict[str, str] = Field(default_factory=dict)


class ExtractionReport(BaseModel):
    """Serializable extraction output."""

    model_config = ConfigDict(extra="forbid")

    records: list[ExtractedNodeRecord] = Field(default_factory=list)

    def as_sorted_payload(self) -> dict[str, Any]:
        return {
            "records": [
                record.model_dump(mode="json")
                for record in sorted(self.records, key=lambda item: (item.family_hint, item.node_url))
            ]
        }
