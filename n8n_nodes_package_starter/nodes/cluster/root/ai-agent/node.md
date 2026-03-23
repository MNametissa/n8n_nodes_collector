# AI Agent

## Identity
- ID: `n8n.cluster-root.ai-agent`
- Slug: `ai-agent`
- Family: `cluster_root`
- Service: `n8n AI`
- Official doc: https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/
- Status: `active`

## One-line summary
Use AI Agent as a root node for tool-using agent workflows in n8n.

## What this node does
It orchestrates agent behavior and works with connected AI sub-nodes and tools.

## When to use it
- when the workflow needs agent-style orchestration
- when tools should be selected or used by the agent
- when a richer AI control loop is needed

## When not to use it
- when a direct model call is enough
- when no tool use or agent behavior is needed

## How it works
AI Agent is a cluster root node. It coordinates connected sub-nodes and tool-capable components in an AI workflow.

## Credentials
Credential needs depend on connected model and tool nodes.

## Operations / Parameters
Parameters focus on agent behavior, tool usage, prompting, and compatible AI connections.

## Inputs
Workflow items and connected sub-node capabilities.

## Outputs
Agent response or tool-assisted reasoning result.

## Typical use cases
- autonomous tool-using assistant workflows
- multi-step AI routing
- AI workflows that need tool access

## Common pitfalls
- forgetting required compatible connections
- confusing it with a simple model call
- mixing up root and sub-node roles

## Limitations
More complex than direct model invocation and depends on compatible sub-nodes.

## Related nodes
- OpenAI

## Agent guidance
### Best-fit selection rules
Use AI Agent when the user explicitly wants an agent that can reason and use tools.

### Disambiguation against similar nodes
Different from service action nodes and from cluster sub-nodes.

### Prompt retrieval hints
`ai agent`, `tool use`, `langchain`, `agent orchestration`, `root node`
