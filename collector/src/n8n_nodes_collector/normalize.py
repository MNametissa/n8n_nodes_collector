"""Normalize extracted records into canonical package records."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from .models import (
    AgentGuidance,
    CanonicalMapEntry,
    CanonicalNodeRecord,
    CanonicalSourceRecord,
    ClusterConfig,
    CredentialsConfig,
    ExecutionRole,
    ExtractionReport,
    ExtractedNodeRecord,
    Family,
    NormalizeReport,
    SourceType,
)
from .progress import NullProgressReporter

GENERIC_SECTION_KEYS = {
    "summary",
    "templates_examples",
    "related_resources",
    "common_issues",
    "version_notes",
    "credentials",
    "ai_tool_usage",
    "node_options",
    "inputs",
    "outputs",
    "description",
    "source",
    "limitations",
}
SKIP_SECTION_PATTERNS = (
    "common_issue",
    "error",
    "issue",
    "troubleshoot",
    "troubleshooting",
    "unsupported",
)
ACTION_OPERATION_PREFIXES = (
    "create",
    "get",
    "get_all",
    "update",
    "delete",
    "add",
    "remove",
    "insert",
    "retrieve",
    "find",
    "list",
    "send",
    "append",
    "clear",
    "compress",
    "decompress",
    "extract",
    "convert",
    "sign",
    "hash",
)
GENERIC_CONTENT_VALUES = {
    "operations",
    "node parameters",
    "templates and examples",
    "related resources",
    "common issues",
    "source",
}
STOPWORDS = {
    "a",
    "an",
    "and",
    "api",
    "app",
    "applications",
    "automate",
    "automation",
    "be",
    "built",
    "by",
    "can",
    "data",
    "do",
    "for",
    "from",
    "get",
    "getting",
    "how",
    "hour",
    "hours",
    "in",
    "including",
    "integrate",
    "integration",
    "is",
    "it",
    "its",
    "manage",
    "make",
    "need",
    "n8n",
    "node",
    "of",
    "official",
    "or",
    "other",
    "range",
    "started",
    "supported",
    "supports",
    "that",
    "the",
    "this",
    "through",
    "to",
    "use",
    "using",
    "wide",
    "week",
    "weeks",
    "with",
    "workflow",
    "workflows",
    "work",
    "every",
    "day",
    "days",
    "month",
    "months",
    "minute",
    "minutes",
    "second",
    "seconds",
    "learning",
}
DOMAIN_HINTS = {
    "spreadsheet": ("spreadsheet", "sheets", "row", "rows", "sheet", "tabular"),
    "erp": ("erp", "odoo", "erpnext"),
    "crm": ("crm", "contact", "contacts", "lead", "leads", "opportunity", "opportunities"),
    "invoice": ("invoice", "invoices", "billing", "bill"),
    "database": ("database", "sql", "postgres", "mysql", "query", "record", "records"),
    "email": ("email", "emails", "mail", "gmail", "outlook"),
    "calendar": ("calendar", "event", "events", "schedule"),
    "chat": ("chat", "message", "messages", "conversation", "assistant"),
    "storage": ("storage", "drive", "file", "files", "bucket", "document", "documents"),
    "api": ("api", "http", "rest", "request", "endpoint"),
    "ai": ("ai", "agent", "model", "embedding", "retriever", "memory", "tool"),
}
SERVICE_ALIAS_HINTS = {
    "odoo": ["erp", "business management"],
    "google sheets": ["spreadsheet", "sheets"],
    "http request": ["api", "rest api", "http client"],
    "ai agent": ["agent orchestration", "tool-using agent"],
    "openai chat model": ["chat model", "llm", "language model"],
    "schedule trigger": ["scheduler", "cron", "time-based trigger"],
}
AI_TASK_HINTS = {
    "text-classifier": {
        "tags": ["classification", "classifier", "categorization", "sorting", "tri", "labeling"],
        "capabilities": ["text classification", "categorize text", "sort items by class"],
    },
    "information-extractor": {
        "tags": ["extraction", "structured output", "field extraction", "parsing"],
        "capabilities": ["extract structured information", "pull fields from text"],
    },
    "basic-llm-chain": {
        "tags": ["prompting", "instructions", "generation", "classification"],
        "capabilities": ["follow prompt instructions", "single-step llm task", "prompt-based classification"],
    },
    "ai-agent": {
        "tags": ["agentic", "reasoning", "tool use", "multi-step"],
        "capabilities": ["agentic reasoning", "tool-using workflow orchestration"],
    },
    "openrouter-chat-model": {
        "tags": ["provider", "llm provider", "openrouter", "chat model"],
        "capabilities": ["language model provider", "chat completion model"],
    },
}


def normalize_records(
    extraction_report: ExtractionReport,
    verified_at: str | None = None,
    progress: object | None = None,
) -> NormalizeReport:
    """Normalize extracted records into canonical node and map outputs."""

    normalized_date = verified_at or date.today().isoformat()
    node_records: list[CanonicalNodeRecord] = []
    map_entries: list[CanonicalMapEntry] = []
    source_records: list[CanonicalSourceRecord] = []
    reporter = progress or NullProgressReporter()

    records = sorted(extraction_report.records, key=lambda item: (item.family_hint, item.node_url))
    reporter.stage("Normalize node records", detail=f"{len(records)} extracted nodes")
    with reporter.task("normalize", total=len(records)) as tracker:
        for extracted in records:
            node = normalize_node_record(extracted, verified_at=normalized_date)
            node_records.append(node)
            tracker.advance(item=node.id)

    enrich_routing_metadata(node_records)

    for extracted, node in zip(records, node_records, strict=True):
        source_records.extend(normalize_source_records(extracted, node))
        map_entries.append(build_map_entry(node, extracted))

    return NormalizeReport(
        map_entries=map_entries,
        node_records=node_records,
        source_records=source_records,
    )


def normalize_node_record(extracted: ExtractedNodeRecord, verified_at: str) -> CanonicalNodeRecord:
    """Normalize a single extracted record into the canonical node shape."""

    display_name = normalize_display_name(extracted.display_name)
    slug = slugify(display_name)
    node_id = build_node_id(extracted.family_hint, slug)
    service = infer_service(extracted.family_hint, display_name)
    category_path = category_path_for(extracted.family_hint, slug)
    summary = first_value(extracted.section_text, "summary")
    common_issues = extracted.section_text.get("common_issues", [])
    templates_examples = extracted.section_text.get("templates_examples", [])
    related_resources = extracted.section_text.get("related_resources", [])
    version_notes = extracted.section_text.get("version_notes", [])
    operations = derive_operations(extracted)
    node_parameters = derive_node_parameters(extracted)
    credentials_required = infer_credentials_required(extracted)
    source_sections_present = set(extracted.section_text.keys())
    if operations:
        source_sections_present.add("operations")
    if node_parameters:
        source_sections_present.add("node_parameters")

    return CanonicalNodeRecord(
        id=node_id,
        slug=slug,
        display_name=display_name,
        display_name_short=display_name,
        doc_title=f"{display_name} node",
        family=extracted.family_hint,
        service=service,
        category_path=category_path,
        doc_url=extracted.node_url,
        summary=summary,
        description=summary,
        credentials=CredentialsConfig(
            required=credentials_required,
            notes=first_matching_value(extracted.section_text, "credentials") if credentials_required else "",
        ),
        operations=operations,
        resource_groups=[],
        node_parameters=node_parameters,
        execution_role=execution_role_for(extracted.family_hint),
        cluster=cluster_config_for(extracted.family_hint),
        templates_examples=templates_examples,
        related_resources=related_resources,
        common_issues=common_issues,
        version_notes=version_notes,
        tags=derive_tags(
            family=extracted.family_hint,
            display_name=display_name,
            service=service,
            summary=summary,
            operations=operations,
            node_parameters=node_parameters,
        ),
        capabilities=derive_capabilities(
            family=extracted.family_hint,
            display_name=display_name,
            service=service,
            summary=summary,
            operations=operations,
            node_parameters=node_parameters,
        ),
        limitations=[],
        gotchas=[],
        agent_guidance=build_agent_guidance(
            family=extracted.family_hint,
            display_name=display_name,
            service=service,
            summary=summary,
            operations=operations,
            node_parameters=node_parameters,
            common_issues=common_issues,
        ),
        related_nodes=[],
        source_sections_present=sorted(source_sections_present),
        last_verified_at=verified_at,
        status="active",
    )


def normalize_source_records(
    extracted: ExtractedNodeRecord,
    node: CanonicalNodeRecord,
) -> list[CanonicalSourceRecord]:
    """Derive canonical source records from extracted provenance data."""

    return [
        CanonicalSourceRecord(
            url=url,
            node_id=node.id,
            title=node.doc_title,
            type=SourceType.NODE_PAGE if url == extracted.node_url else SourceType.SUPPORTING_PAGE,
            family_hint=node.family,
            collected_at=node.last_verified_at,
            http_status=200,
            content_hash=content_hash,
            status="parsed",
            notes="",
        )
        for url, content_hash in sorted(extracted.content_hashes.items())
    ]


def build_map_entry(
    node: CanonicalNodeRecord,
    extracted: ExtractedNodeRecord,
) -> CanonicalMapEntry:
    """Build the canonical map entry for a normalized node."""

    return CanonicalMapEntry(
        id=node.id,
        slug=node.slug,
        display_name=node.display_name,
        family=node.family,
        category_path=node.category_path,
        service=node.service,
        doc_url=node.doc_url,
        file_md=f"{node_folder(node.family, node.slug)}/node.md",
        file_json=f"{node_folder(node.family, node.slug)}/node.json",
        tags=node.tags,
        capabilities=node.capabilities,
        related_nodes=node.related_nodes,
        requires_credentials=node.credentials.required,
        supports_tools_connector=node.cluster.tool_connector,
        has_common_issues_page=has_supporting_page(extracted, "common-issues"),
        has_templates_section=bool(node.templates_examples),
        status=node.status,
    )


def infer_credentials_required(extracted: ExtractedNodeRecord) -> bool:
    """Infer whether a node itself requires credentials."""

    if extracted.family_hint == Family.ACTION:
        return bool(matching_section_values(extracted.section_text, "credentials"))
    if extracted.family_hint == Family.TRIGGER:
        return bool(matching_section_values(extracted.section_text, "credentials"))
    if extracted.family_hint in {Family.CLUSTER_ROOT, Family.CLUSTER_SUB}:
        return bool(matching_section_values(extracted.section_text, "credentials"))
    return False


def has_supporting_page(extracted: ExtractedNodeRecord, suffix: str) -> bool:
    """Return whether the extracted node includes a supporting page with the given suffix."""

    return any(page.endswith(f"/{suffix}/") for page in extracted.supporting_pages)


def execution_role_for(family: Family) -> ExecutionRole:
    """Build execution-role flags from the family."""

    return ExecutionRole(
        is_trigger=family == Family.TRIGGER,
        is_action=family == Family.ACTION,
        is_core=family == Family.CORE,
        is_cluster_root=family == Family.CLUSTER_ROOT,
        is_cluster_sub=family == Family.CLUSTER_SUB,
    )


def cluster_config_for(family: Family) -> ClusterConfig:
    """Build the canonical cluster block."""

    if family == Family.CLUSTER_ROOT:
        return ClusterConfig(
            root_or_sub="root",
            compatible_with=[],
            compatible_parents=[],
            requires_parent=False,
            requires_subnodes=True,
            tool_connector=True,
            functional_group="agents",
        )
    if family == Family.CLUSTER_SUB:
        return ClusterConfig(
            root_or_sub="sub",
            compatible_with=[],
            compatible_parents=[],
            requires_parent=True,
            requires_subnodes=False,
            tool_connector=False,
            functional_group="sub_component",
        )
    return ClusterConfig()


def infer_service(family: Family, display_name: str) -> str | None:
    """Infer the service field from family and name."""

    if family == Family.ACTION:
        return display_name
    if family in {Family.CLUSTER_ROOT, Family.CLUSTER_SUB}:
        return "n8n AI"
    return None


def derive_operations(extracted: ExtractedNodeRecord) -> list[str]:
    """Build operations from explicit sections or family-specific fallbacks."""

    explicit = clean_content_list(extracted.section_text.get("operations", []))
    if explicit:
        return explicit

    if extracted.family_hint != Family.ACTION:
        return []

    fallback = [
        humanize_section_key(key)
        for key in extracted.section_text
        if is_action_operation_section(key)
    ]
    return dedupe_preserve_order(fallback)


def derive_node_parameters(extracted: ExtractedNodeRecord) -> list[str]:
    """Build node parameters from explicit sections or section-key fallbacks."""

    explicit = clean_content_list(extracted.section_text.get("node_parameters", []))
    if explicit:
        return explicit

    fallback = [
        humanize_section_key(key)
        for key in extracted.section_text
        if is_parameter_like_section(key, extracted.family_hint)
    ]
    if not fallback and extracted.section_text.get("node_options"):
        fallback.append(humanize_section_key("node_options"))
    return dedupe_preserve_order(fallback)


def build_agent_guidance(
    *,
    family: Family,
    display_name: str,
    service: str | None,
    summary: str,
    operations: list[str],
    node_parameters: list[str],
    common_issues: list[str],
) -> AgentGuidance:
    """Build deterministic AI-facing guidance from normalized node signals."""

    subject = service or display_name
    selection_rules = [selection_rule_for(family, subject, summary)]
    if operations:
        selection_rules.append(f"Prefer when you need {short_list(operations, limit=3)}.")
    if node_parameters:
        selection_rules.append(f"Configure through parameters such as {short_list(node_parameters, limit=3)}.")

    disambiguation = [disambiguation_rule_for(family, subject)]
    if common_issues:
        disambiguation.append("Check documented common issues before falling back to custom workarounds.")

    prompt_hints = build_prompt_hints(subject, operations, node_parameters)
    retrieval_keywords = build_retrieval_keywords(subject, operations, node_parameters, family)

    return AgentGuidance(
        selection_rules=dedupe_preserve_order(selection_rules),
        disambiguation=dedupe_preserve_order(disambiguation),
        prompt_hints=dedupe_preserve_order(prompt_hints),
        retrieval_keywords=dedupe_preserve_order(retrieval_keywords),
    )


def enrich_routing_metadata(node_records: list[CanonicalNodeRecord]) -> None:
    """Fill package-level routing relationships once all nodes are known."""

    by_id = {node.id: node for node in node_records}
    http_request_id = next((node.id for node in node_records if node.slug == "http-request"), None)
    cluster_roots = [node.id for node in node_records if node.family == Family.CLUSTER_ROOT]
    cluster_subs = [node.id for node in node_records if node.family == Family.CLUSTER_SUB]

    for node in node_records:
        related: list[str] = []
        if node.family == Family.ACTION and http_request_id is not None and node.id != http_request_id:
            related.append(http_request_id)
        if node.family == Family.CLUSTER_ROOT:
            related.extend(cluster_subs[:5])
        if node.family == Family.CLUSTER_SUB:
            related.extend(cluster_roots[:3])
        node.related_nodes = dedupe_preserve_order(related)
        node.agent_guidance.retrieval_keywords = dedupe_preserve_order(
            node.agent_guidance.retrieval_keywords + node.tags + node.capabilities
        )
        if http_request_id is not None and node.family == Family.ACTION:
            node.agent_guidance.disambiguation = dedupe_preserve_order(
                node.agent_guidance.disambiguation
                + ["Fallback to HTTP Request only when the required service operation is not exposed natively."]
            )

    if http_request_id is not None:
        http_request = by_id[http_request_id]
        action_ids = [candidate.id for candidate in node_records if candidate.family == Family.ACTION][:12]
        http_request.related_nodes = dedupe_preserve_order(http_request.related_nodes + action_ids)


def selection_rule_for(family: Family, subject: str, summary: str) -> str:
    """Return the primary selection rule for a node family."""

    if family == Family.ACTION:
        return f"Choose this node when you need native {subject} integration instead of a generic API call."
    if family == Family.TRIGGER:
        return f"Choose this node when a workflow should start from a {subject} event or schedule."
    if family == Family.CORE:
        return f"Choose this node for built-in workflow logic or data handling inside n8n."
    if family == Family.CLUSTER_ROOT:
        return "Choose this node as the main AI orchestration component that coordinates connected sub-nodes."
    return "Choose this node as a supporting AI sub-node that augments a parent AI workflow component."


def disambiguation_rule_for(family: Family, subject: str) -> str:
    """Return the primary disambiguation rule for a node family."""

    if family == Family.ACTION:
        return "Prefer this over HTTP Request when the documented native operations already cover the service workflow."
    if family == Family.TRIGGER:
        return "Prefer this over polling or webhook alternatives when the external event source matches the documented trigger behavior."
    if family == Family.CORE:
        return "Prefer this over custom code when the built-in node already expresses the required transformation or control flow."
    if family == Family.CLUSTER_ROOT:
        return "Use this as the parent AI node; attach models, memory, tools, or retrievers through compatible sub-node connections."
    return "Use this only with compatible AI parent nodes rather than as a standalone workflow step."


def build_prompt_hints(subject: str, operations: list[str], node_parameters: list[str]) -> list[str]:
    """Build short prompt-like hints for retrieval and orchestration."""

    hints = [f"use {subject.lower()}"]
    if operations:
        hints.extend(f"{operation.lower()} in {subject.lower()}" for operation in operations[:3])
    elif node_parameters:
        hints.extend(f"configure {parameter.lower()}" for parameter in node_parameters[:3])
    return hints


def build_retrieval_keywords(
    subject: str,
    operations: list[str],
    node_parameters: list[str],
    family: Family,
) -> list[str]:
    """Build deterministic retrieval keywords."""

    keywords = [subject.lower(), family.value.replace("_", " ")]
    keywords.extend(normalize_keyword_token(operation) for operation in operations[:5])
    keywords.extend(normalize_keyword_token(parameter) for parameter in node_parameters[:5])
    return [keyword for keyword in dedupe_preserve_order(keywords) if keyword]


def derive_tags(
    *,
    family: Family,
    display_name: str,
    service: str | None,
    summary: str,
    operations: list[str],
    node_parameters: list[str],
) -> list[str]:
    """Derive deterministic retrieval tags for a node."""

    tags: list[str] = []
    tags.extend(extract_keywords(display_name))
    if service:
        tags.extend(extract_keywords(service))
        tags.extend(SERVICE_ALIAS_HINTS.get(service.lower(), []))
    tags.extend(SERVICE_ALIAS_HINTS.get(display_name.lower(), []))
    tags.append(family.value.replace("_", " "))
    tags.extend(match_domain_hints(" ".join([display_name, service or "", summary])))
    tags.extend(extract_keywords(summary, limit=6))
    tags.extend(extract_keywords(" ".join(operations[:3]), limit=6))
    tags.extend(extract_keywords(" ".join(node_parameters[:3]), limit=4))
    if family in {Family.CLUSTER_ROOT, Family.CLUSTER_SUB}:
        tags.append("ai")
    tags.extend(ai_task_tags(slugify(display_name)))
    return dedupe_preserve_order(tags)[:16]


def derive_capabilities(
    *,
    family: Family,
    display_name: str,
    service: str | None,
    summary: str,
    operations: list[str],
    node_parameters: list[str],
) -> list[str]:
    """Derive deterministic capability strings for ranking and retrieval."""

    capabilities = [normalize_capability(item) for item in operations[:8]]
    if not capabilities:
        capabilities.extend(normalize_capability(item) for item in node_parameters[:6])
    if family == Family.ACTION and service:
        capabilities.append(f"native {service.lower()} integration")
    if family == Family.TRIGGER:
        capabilities.append("start workflow from external event")
    if family == Family.CORE:
        capabilities.append("built-in workflow logic")
    if family == Family.CLUSTER_ROOT:
        capabilities.append("ai workflow orchestration")
    if family == Family.CLUSTER_SUB:
        capabilities.append("ai sub-component")
    capabilities.extend(ai_task_capabilities(slugify(display_name)))
    return dedupe_preserve_order([cap for cap in capabilities if cap])[:12]


def is_action_operation_section(key: str) -> bool:
    """Return whether a section key likely describes an action operation."""

    if key in GENERIC_SECTION_KEYS:
        return False
    if any(pattern in key for pattern in SKIP_SECTION_PATTERNS):
        return False
    if key.endswith("_parameters") or key == "events":
        return False
    return key.startswith(ACTION_OPERATION_PREFIXES) or "_api" in key or key in {"management_api", "content_api"}


def is_parameter_like_section(key: str, family: Family) -> bool:
    """Return whether a section key should contribute parameter-like guidance."""

    if key in GENERIC_SECTION_KEYS:
        return False
    if any(pattern in key for pattern in SKIP_SECTION_PATTERNS):
        return False
    if family == Family.ACTION and is_action_operation_section(key):
        return False
    if key.endswith("_parameters"):
        return True
    if key in {"events", "authentication", "operation_mode", "node_usage_patterns", "rules"}:
        return True
    return True


def clean_content_list(values: list[str]) -> list[str]:
    """Normalize extracted list content for canonical storage."""

    cleaned: list[str] = []
    for value in values:
        if not value or not value.strip():
            continue
        normalized = " ".join(value.split())
        normalized = re.sub(r"\s+#\s*$", "", normalized).strip()
        if normalized.lower() in GENERIC_CONTENT_VALUES:
            continue
        cleaned.append(normalized)
    return dedupe_preserve_order(cleaned)


def dedupe_preserve_order(values: list[str]) -> list[str]:
    """Dedupe while preserving order."""

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def humanize_section_key(value: str) -> str:
    """Convert normalized section keys into human-readable labels."""

    text = value.replace("_", " ").strip()
    text = re.sub(r"\s+", " ", text)
    if not text:
        return text
    acronyms = {"ai", "api", "n8n", "url", "id", "http", "json", "sql", "csv", "rtf", "ods"}
    words = []
    for token in text.split():
        if token in acronyms:
            words.append(token.upper() if token != "n8n" else "n8n")
        elif token == "qa":
            words.append("Q&A")
        else:
            words.append(token.capitalize())
    return " ".join(words)


def short_list(values: list[str], limit: int) -> str:
    """Return a short comma-separated list."""

    subset = values[:limit]
    return ", ".join(subset)


def normalize_keyword_token(value: str) -> str:
    """Simplify a value into a compact retrieval keyword."""

    return value.lower().replace(":", " ").replace("(", " ").replace(")", " ").replace("/", " ").strip()


def normalize_capability(value: str) -> str:
    """Normalize a string into a concise capability phrase."""

    text = normalize_keyword_token(value)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+#\s*$", "", text)
    if text in GENERIC_CONTENT_VALUES:
        return ""
    return text.strip(" -")


def extract_keywords(value: str, limit: int = 8) -> list[str]:
    """Extract compact retrieval terms from text."""

    tokens = re.findall(r"[a-z0-9][a-z0-9+.-]*", value.lower())
    keywords: list[str] = []
    for token in tokens:
        if token in STOPWORDS:
            continue
        if len(token) < 3 and token not in {"ai", "db"}:
            continue
        if token.isdigit():
            continue
        keywords.append(token)
    return dedupe_preserve_order(keywords)[:limit]


def match_domain_hints(value: str) -> list[str]:
    """Return domain tags that can be inferred from text."""

    lowered = value.lower()
    matches: list[str] = []
    for domain, keywords in DOMAIN_HINTS.items():
        if any(re.search(rf"\b{re.escape(keyword)}\b", lowered) for keyword in keywords):
            matches.append(domain)
    return matches


def ai_task_tags(slug: str) -> list[str]:
    """Return explicit AI task tags for known AI-focused nodes."""

    return list(AI_TASK_HINTS.get(slug, {}).get("tags", []))


def ai_task_capabilities(slug: str) -> list[str]:
    """Return explicit AI task capabilities for known AI-focused nodes."""

    return list(AI_TASK_HINTS.get(slug, {}).get("capabilities", []))


def normalize_display_name(value: str) -> str:
    """Clean a docs heading into a stable display name."""

    cleaned = value.strip()
    cleaned = re.sub(r"\s+#\s*$", "", cleaned)
    cleaned = re.sub(r"\s+node\s*$", "", cleaned, flags=re.IGNORECASE)
    return " ".join(cleaned.split())


def category_path_for(family: Family, slug: str) -> list[str]:
    """Build the canonical category path."""

    if family == Family.ACTION:
        return ["actions", slug]
    if family == Family.TRIGGER:
        return ["triggers", slug]
    if family == Family.CORE:
        return ["core", slug]
    if family == Family.CLUSTER_ROOT:
        return ["cluster", "root", slug]
    return ["cluster", "sub", slug]


def build_node_id(family: Family, slug: str) -> str:
    """Build the canonical node ID."""

    prefix = {
        Family.ACTION: "n8n.action",
        Family.TRIGGER: "n8n.trigger",
        Family.CORE: "n8n.core",
        Family.CLUSTER_ROOT: "n8n.cluster-root",
        Family.CLUSTER_SUB: "n8n.cluster-sub",
    }[family]
    return f"{prefix}.{slug}"


def node_folder(family: Family, slug: str) -> str:
    """Build the package-relative node folder."""

    if family == Family.ACTION:
        return f"nodes/actions/{slug}"
    if family == Family.TRIGGER:
        return f"nodes/triggers/{slug}"
    if family == Family.CORE:
        return f"nodes/core/{slug}"
    if family == Family.CLUSTER_ROOT:
        return f"nodes/cluster/root/{slug}"
    return f"nodes/cluster/sub/{slug}"


def slugify(value: str) -> str:
    """Create a canonical slug."""

    lowered = value.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return re.sub(r"-{2,}", "-", normalized)


def first_value(section_text: dict[str, list[str]], key: str) -> str:
    """Return the first value from a section if present."""

    values = section_text.get(key, [])
    return values[0] if values else ""


def matching_section_values(section_text: dict[str, list[str]], prefix: str) -> list[str]:
    """Return merged values for an exact key or matching key prefix."""

    merged: list[str] = []
    for key, values in section_text.items():
        if key == prefix or key.startswith(f"{prefix}_"):
            merged.extend(values)
    return clean_content_list(merged)


def first_matching_value(section_text: dict[str, list[str]], prefix: str) -> str:
    """Return the first merged value for matching section keys."""

    values = matching_section_values(section_text, prefix)
    return values[0] if values else ""


def write_normalize_report(report: NormalizeReport, output_path: Path) -> None:
    """Serialize the normalization report to disk."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.as_sorted_payload(), indent=2) + "\n", encoding="utf-8")
