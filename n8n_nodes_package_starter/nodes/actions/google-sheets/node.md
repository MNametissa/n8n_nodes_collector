# Google Sheets

## Identity
- ID: `n8n.action.google-sheets`
- Slug: `google-sheets`
- Family: `action`
- Service: `Google Sheets`
- Official doc: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/
- Status: `active`

## One-line summary
Use Google Sheets to read, append, update, and manage spreadsheet data inside an n8n workflow.

## What this node does
This node provides native Google Sheets operations for spreadsheet automation.

## When to use it
- reading rows from sheets
- appending workflow outputs to sheets
- updating tabular records maintained in Google Sheets

## When not to use it
- when the required API operation is not exposed by the node
- when a fully custom Google API call is required

## How it works
The node connects to Google Sheets through configured credentials and exposes supported spreadsheet operations as workflow actions.

## Credentials
Requires Google Sheets-compatible credentials configured in n8n.

## Operations / Parameters
Typical operations include append, read, update, clear, and delete. Parameters usually include spreadsheet selection, sheet selection, ranges, filters, and field mapping.

## Inputs
Workflow items.

## Outputs
Spreadsheet rows or action results.

## Typical use cases
- CRM or leads sync to sheets
- logging workflow outputs in a spreadsheet
- enriching data pipelines with spreadsheet lookup data

## Common pitfalls
- wrong worksheet selected
- mismatched columns during write/update
- permissions or auth errors

## Limitations
If a required operation is not supported directly, HTTP Request may be needed.

## Related nodes
- OpenAI

## Agent guidance
### Best-fit selection rules
Prefer this node when the user explicitly wants Google Sheets work using supported operations.

### Disambiguation against similar nodes
Use this instead of generic API access when the use case maps to the official Google Sheets node.

### Prompt retrieval hints
`google sheets`, `append rows`, `read spreadsheet`, `update rows`
