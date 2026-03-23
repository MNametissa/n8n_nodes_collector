# Update playbook

## Daily lightweight job

1. Load current `sources.json`.
2. Re-fetch each known node page.
3. Compare hash or normalized content digest.
4. Rebuild only changed node artifacts.
5. Regenerate maps and indexes.
6. Commit changes.

## Weekly full refresh

1. Re-scan official n8n index pages.
2. Discover added or removed node pages.
3. Rebuild the full node inventory.
4. Re-run extraction for all nodes.
5. Regenerate package files.
6. Review diff summary.
7. Publish a new package snapshot.

## Monthly audit

1. Compare package counts by family.
2. Check cluster node taxonomy.
3. Check nodes with version notes.
4. Validate a manual sample of node pages.
5. Update parser rules if the doc layout changed.

## Failure handling

If a page cannot be parsed:
- mark source status as `parse_failed`
- keep previous node snapshot if available
- set node status to `stale_pending_review`
- do not silently delete the node
