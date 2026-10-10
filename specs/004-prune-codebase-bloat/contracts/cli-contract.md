# CLI Interface Contract: Unified CLI Parity

**Feature**: `004-prune-codebase-bloat`
**Target Executable**: `gravel_tracker.py`

---

## 1. Top-Level Delegation Contract

`gravel_tracker.py` MUST accept all commands supported by `gravel_bot/cli.py` and produce identical terminal output:

### Supported Invocations

```bash
# 1. Default (no args) -> lists ranking + deals
python3 gravel_tracker.py

# 2. Budget optimizer
python3 gravel_tracker.py presupuesto 1000 [--altura 169] [--talla S] [--local] [--json]
python3 gravel_tracker.py --presupuesto 1000

# 3. Live catalog audit
python3 gravel_tracker.py audit [--limit 20] [--all] [--tienda Mammoth] [--force]
python3 gravel_tracker.py --audit --limit 10

# 4. Calibrated rescore
python3 gravel_tracker.py re-score [--dry-run]
python3 gravel_tracker.py --re-score

# 5. Bike inspection card
python3 gravel_tracker.py ficha "Jakar 30"
python3 gravel_tracker.py --ficha "Jakar 30"

# 6. Web dashboard
python3 gravel_tracker.py web [--port 8080] [--host 127.0.0.1]
python3 gravel_tracker.py --web 8080

# 7. Scraper pipeline & daemon
python3 gravel_tracker.py scan [--no-alert] [--deep]
python3 gravel_tracker.py daemon [--interval 3600]
```

### Exit Codes
- `0`: Success.
- `1` / `2`: Argument parsing failure or unhandled exception.
