from __future__ import annotations

import pytest

from n8n_nodes_collector.discovery import discover_from_live_sources
from n8n_nodes_collector.models import Family


@pytest.mark.live
def test_discover_from_live_sources_finds_expected_builtin_families() -> None:
    report = discover_from_live_sources()

    by_url = {candidate.url: candidate for candidate in report.candidates}

    assert "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/" in by_url
    assert "https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/" in by_url
    assert "https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/" in by_url
    assert "https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/" in by_url

    assert by_url["https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/"].family == Family.ACTION
    assert by_url["https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/"].family == Family.CORE
    assert by_url["https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/"].family == Family.TRIGGER
    assert by_url["https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/"].family == Family.CLUSTER_ROOT
    assert any(candidate.family == Family.CLUSTER_SUB for candidate in report.candidates)
