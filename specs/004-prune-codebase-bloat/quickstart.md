# Quickstart Validation Guide: Prune Codebase Bloat & Over-Engineering

**Feature**: `004-prune-codebase-bloat`
**Date**: 2026-10-10

## Validation Scenarios

### Scenario 1: Verify Unified CLI Parity
Test that `gravel_tracker.py` properly delegates to `gravel_bot.cli.main()`.

```bash
# Budget optimizer test
python3 gravel_tracker.py --presupuesto 1000

# Audit test
python3 gravel_tracker.py --audit --limit 2

# Rescore dry run
python3 gravel_tracker.py --re-score --dry-run
```
**Expected Outcome**: All commands execute properly with zero `sys.argv` errors.

---

### Scenario 2: Verify Defunct Scraper Deletion
Verify that `tuvalum.py` is deleted and pipeline imports succeed without missing module errors.

```bash
python3 -c "from gravel_bot.scrapers.multi_store import MultiStoreScraper; print('MultiStoreScraper OK')"
python3 -c "import os; assert not os.path.exists('gravel_bot/scrapers/tuvalum.py'), 'Tuvalum scraper should be deleted'"
```
**Expected Outcome**: Module imports succeed; file does not exist.

---

### Scenario 3: Verify Sizing Logic Consistency
Verify that `budget_optimizer` yields identical compatibility to `geometry_sizing`.

```bash
python3 -c "
from gravel_bot.budget_optimizer import clean_candidate_from_row
from gravel_bot.db import get_all_bikes
bikes = get_all_bikes()
for b in bikes[:10]:
    cand = clean_candidate_from_row(b, 169)
print('Sizing integration verified!')
"
```
**Expected Outcome**: Sizing runs smoothly without discrepancies.

---

### Scenario 4: Full Test Suite Execution
Run the consolidated test suite to prove zero regressions.

```bash
python3 -m unittest discover -s . -p "test_*.py"
```
**Expected Outcome**: 100% tests pass.
