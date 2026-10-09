# Quickstart Validation Guide: Lightweight Interactive Web Dashboard

**Feature**: `002-web-dashboard-ui`
**Date**: 2026-10-09

## Prerequisites

- Python 3.11+ installed.
- SQLite catalog database `gravel_madrid.db` initialized.

---

## Scenario 1: Launch Local Web Server

### Command
```bash
python3 gravel_tracker.py --web --port 8080 &
SERVER_PID=$!
sleep 1
```

### Verification
```bash
curl -I http://127.0.0.1:8080/
```

### Expected Output
- HTTP status `200 OK`.
- Header `Content-Type: text/html; charset=utf-8`.

---

## Scenario 2: Validate JSON Catalog API

### Command
```bash
curl -s http://127.0.0.1:8080/api/bikes | grep -q '"status": "success"' && echo "✅ API Catalog OK"
```

### Expected Output
- `✅ API Catalog OK`.
- Response contains an array of sanitized bikes with zero bare frames or ebikes.

---

## Scenario 3: Validate Dynamic Budget Recommendation API

### Command
```bash
curl -s "http://127.0.0.1:8080/api/recommend?budget=1000" | grep -q '"best_value"' && echo "✅ Recommendation API OK"
```

### Expected Output
- `✅ Recommendation API OK`.
- Best value model asking price is $\le 1.000\text{ €}$.

---

## Scenario 4: Teardown

```bash
kill $SERVER_PID
```