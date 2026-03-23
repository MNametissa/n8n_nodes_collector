# OpenAI

## Identity
- ID: `n8n.action.openai`
- Slug: `openai`
- Family: `action`
- Service: `OpenAI`
- Official doc: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-langchain.openai/
- Status: `active`

## One-line summary
Use the official OpenAI node for supported OpenAI-powered tasks inside n8n.

## What this node does
It connects n8n workflows to supported OpenAI capabilities exposed by the built-in node.

## When to use it
- when the user wants a built-in OpenAI integration
- when supported model-driven tasks are enough
- when the workflow fits the documented node behavior

## When not to use it
- when a needed API feature is not exposed
- when a custom low-level request is required

## How it works
The node uses configured OpenAI credentials and exposes supported AI operations through n8n.

## Credentials
Requires OpenAI credentials configured in n8n.

## Operations / Parameters
Use the official page as the source of truth for supported operations and parameters. The package treats unsupported operations as a reason to consider HTTP Request.

## Inputs
Prompt or structured inputs from previous nodes.

## Outputs
AI-generated responses or operation results.

## Typical use cases
- text generation inside a workflow
- AI enrichment of business data
- AI-assisted automation steps

## Common pitfalls
- expecting full API parity with OpenAI
- confusing this node with AI Agent or model sub-nodes

## Limitations
Unsupported endpoints or advanced API features may require HTTP Request.

## Related nodes
- AI Agent

## Agent guidance
### Best-fit selection rules
Prefer this node for supported OpenAI tasks.

### Disambiguation against similar nodes
Different from AI Agent, which orchestrates agent logic. Different from OpenAI chat model sub-nodes in cluster AI setups.

### Prompt retrieval hints
`openai node`, `text generation`, `supported openai operation`, `tools`
