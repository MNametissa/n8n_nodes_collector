# Changelog

All notable changes to this repository will be documented in this file.

The format follows Keep a Changelog principles, and package versions use SemVer.

## [Unreleased]

### Added

- bootstrap governance files
- research inventory and architecture notes
- canonical schema, validation, collector, and git workflow specs
- Python collector scaffold with working `discover` and `fetch` commands
- fixture-based tests for discovery and fetch/cache behavior
- working `extract` command with intermediate node-record output
- fixture-based tests for extraction over the three sample node pages
- working `normalize` command for canonical node and map records
- fixture-based tests for normalization against the schema contract
- working `render` command for canonical package artifacts under `package/`
- working `validate` command for rendered package consistency checks
- render/validate tests covering success paths, CLI wiring, and a validator failure case
