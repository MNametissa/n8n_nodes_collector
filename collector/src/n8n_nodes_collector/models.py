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

    @classmethod
    def from_path(cls, path: Path) -> "ExtractionReport":
        """Load an extraction report from JSON."""

        return cls.model_validate_json(path.read_text(encoding="utf-8"))


class CredentialsConfig(BaseModel):
    """Canonical credentials block."""

    model_config = ConfigDict(extra="forbid")

    required: bool
    credential_refs: list[str] = Field(default_factory=list)
    notes: str = ""


class ExecutionRole(BaseModel):
    """Canonical execution-role block."""

    model_config = ConfigDict(extra="forbid")

    is_trigger: bool
    is_action: bool
    is_core: bool
    is_cluster_root: bool
    is_cluster_sub: bool


class ClusterConfig(BaseModel):
    """Canonical cluster block."""

    model_config = ConfigDict(extra="forbid")

    root_or_sub: str | None = None
    compatible_with: list[str] = Field(default_factory=list)
    compatible_parents: list[str] = Field(default_factory=list)
    requires_parent: bool = False
    requires_subnodes: bool = False
    tool_connector: bool = False
    functional_group: str | None = None


class AgentGuidance(BaseModel):
    """Canonical AI-guidance block."""

    model_config = ConfigDict(extra="forbid")

    selection_rules: list[str] = Field(default_factory=list)
    disambiguation: list[str] = Field(default_factory=list)
    prompt_hints: list[str] = Field(default_factory=list)
    retrieval_keywords: list[str] = Field(default_factory=list)


class CanonicalNodeRecord(BaseModel):
    """Canonical normalized node record."""

    model_config = ConfigDict(extra="forbid")

    id: str
    slug: str
    display_name: str
    display_name_short: str
    doc_title: str
    family: Family
    service: str | None
    category_path: list[str]
    doc_url: str
    source_type: str = "official_docs"
    summary: str = ""
    description: str = ""
    why_use_it: str = ""
    when_to_use: list[str] = Field(default_factory=list)
    when_not_to_use: list[str] = Field(default_factory=list)
    credentials: CredentialsConfig
    operations: list[str] = Field(default_factory=list)
    resource_groups: list[str] = Field(default_factory=list)
    node_parameters: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    execution_role: ExecutionRole
    cluster: ClusterConfig
    templates_examples: list[str] = Field(default_factory=list)
    related_resources: list[str] = Field(default_factory=list)
    common_issues: list[str] = Field(default_factory=list)
    unsupported_ops_guidance: str = ""
    version_notes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    gotchas: list[str] = Field(default_factory=list)
    agent_guidance: AgentGuidance = Field(default_factory=AgentGuidance)
    related_nodes: list[str] = Field(default_factory=list)
    source_sections_present: list[str] = Field(default_factory=list)
    last_verified_at: str
    status: str = "active"


class CanonicalMapEntry(BaseModel):
    """Canonical normalized map entry."""

    model_config = ConfigDict(extra="forbid")

    id: str
    slug: str
    display_name: str
    family: Family
    category_path: list[str]
    service: str | None
    doc_url: str
    file_md: str
    file_json: str
    tags: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    related_nodes: list[str] = Field(default_factory=list)
    requires_credentials: bool
    supports_tools_connector: bool
    has_common_issues_page: bool
    has_templates_section: bool
    status: str = "active"


class CanonicalSourceRecord(BaseModel):
    """Canonical source ledger record for rendering."""

    model_config = ConfigDict(extra="forbid")

    url: str
    node_id: str
    title: str
    type: SourceType
    family_hint: Family
    collected_at: str
    http_status: int
    content_hash: str
    status: str = "parsed"
    notes: str = ""


class NormalizeReport(BaseModel):
    """Serializable normalization output."""

    model_config = ConfigDict(extra="forbid")

    map_entries: list[CanonicalMapEntry] = Field(default_factory=list)
    node_records: list[CanonicalNodeRecord] = Field(default_factory=list)
    source_records: list[CanonicalSourceRecord] = Field(default_factory=list)

    def as_sorted_payload(self) -> dict[str, Any]:
        return {
            "map_entries": [
                entry.model_dump(mode="json")
                for entry in sorted(self.map_entries, key=lambda item: item.id)
            ],
            "node_records": [
                record.model_dump(mode="json")
                for record in sorted(self.node_records, key=lambda item: item.id)
            ],
            "source_records": [
                record.model_dump(mode="json")
                for record in sorted(self.source_records, key=lambda item: (item.node_id, item.url))
            ],
        }

    @classmethod
    def from_path(cls, path: Path) -> "NormalizeReport":
        """Load a normalization report from JSON."""

        return cls.model_validate_json(path.read_text(encoding="utf-8"))
