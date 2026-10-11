# Implementation Plan: Telegram Alert Formatting & Autonomous Cloud Worker

**Branch**: `005-telegram-alerts-cloud-worker` | **Date**: 2026-10-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-telegram-alerts-cloud-worker/spec.md`

## Summary

This feature resolves two core operational requirements:
1. **Pristine Telegram Message Formatting & Verified Store Links**: Implements strict `html.escape` sanitization, guaranteed direct purchase links, and interactive inline buttons (`[🛒 Ver Oferta en Tienda]`) for one-tap store opening on mobile, with an alert quality gate that drops notifications lacking valid URLs.
2. **Autonomous Cloud-Only Worker (Free GitHub Actions)**: Configures a dedicated cloud workflow that runs scraping, auditing, and alert dispatching 24/7 on schedule without requiring the user's laptop to be powered on, backed by an automated secret synchronization command (`gravel_tracker.py cloud-sync`).

## Technical Context

- **Language**: Python 3.11+
- **Dependencies**: Python standard library (`html`, `urllib`, `json`, `subprocess`). Zero external dependencies.
- **Target Files**:
  - `gravel_bot/notifier.py`: HTML escaping, inline keyboard payload builder, URL quality gate.
  - `gravel_bot/cli.py`: Add `cmd_cloud_sync` and `cloud-sync` subcommand.
  - `gravel_tracker.py`: Support `cloud-sync` command alias.
  - `.github/workflows/gravel_cloud_worker.yml`: Dedicated self-contained cloud worker with cron schedule and manual dispatch.
  - `test_new_features.py`: Unit tests for formatting, URL validation, and payload generation.

## Constitution Check

- *Principle I (Library-First)*: Messaging and cloud sync helpers reside in `gravel_bot`.
- *Principle II (CLI Interface)*: Managed via `gravel_tracker.py cloud-sync`.
- *Principle III (Test-First & Zero Regressions)*: 100% test coverage for payload generation and URL gating.
- *Ponytail*: Native standard library `html.escape`, `urllib.request`, and GitHub CLI `gh`. Zero external package dependencies.

## Complexity Tracking

*Zero external dependencies. Free tier cloud execution uses < 10% of monthly GitHub Actions quota.*
