# Local Run Guide

This document explains how to run the project locally and how to test the
Tutor service endpoints.

## 1) Prerequisites

- Python 3.12+ (required by `pyproject.toml`)
- macOS / Linux / Windows terminal

Check your version:

```bash
python3 --version
```

## 2) Create venv & install dependencies

From the repo root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
```

## 3) Run Tutor service

```bash
python -m examples.tutor_service
```

Default address: `http://127.0.0.1:8009`

Optional environment variables:

- `OPENAI_API_KEY=...` (or other provider keys)
- `TUTOR_LLM_PROVIDER=openai`
- `TUTOR_HOST=0.0.0.0`
- `TUTOR_PORT=8009`
- `TUTOR_RELOAD=1`

## 4) Frontend local integration

Set CORS for your frontend origin (example for Vite/Next on 3000):

```bash
export TUTOR_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Frontend API base URL:

```
http://127.0.0.1:8009
```

Quiz flow (frontend):

1) `POST /tutor/{eip}/quiz/start`
2) `POST /tutor/{eip}/quiz/answer` (repeat 3 times with `sessionId`)
3) On the 3rd response, read `passed` (bool) and show reward UI

ERC-8004 quiz flow (frontend):

1) `POST /tutor/erc8004/quiz/start`
2) `POST /tutor/erc8004/quiz/answer` (repeat 3 times with `sessionId`)

If the frontend runs on another device, set:

```
TUTOR_HOST=0.0.0.0
```

Then call:

```
http://<your-ip>:8009
```

## 5) Swagger UI testing

Open:

```
http://127.0.0.1:8009/docs
```

Then test:

- `GET /health`
- `POST /tutor/1559/explain`
- `POST /tutor/7702/explain`
- `POST /tutor/1559/quiz/start`
- `POST /tutor/1559/quiz/answer`
- `POST /tutor/7702/quiz/start`
- `POST /tutor/7702/quiz/answer`
- `POST /tutor/erc8004/quiz/start`
- `POST /tutor/erc8004/quiz/answer`

Example `POST /tutor/1559/explain` body:

```json
{
  "baseFeePerGasGwei": 32.5,
  "maxFeePerGasGwei": 60,
  "maxPriorityFeePerGasGwei": 2,
  "gasLimit": 21000,
  "txContext": {
    "to": "0xabc0000000000000000000000000000000000000",
    "valueEth": 0.01
  }
}
```

Example `POST /tutor/7702/explain` body:

```json
{
  "delegationContext": {
    "delegate": "0xdef0000000000000000000000000000000000000",
    "scope": "only this task",
    "expiry": 1893456000,
    "functions": ["swapExactTokensForTokens"],
    "limits": {"maxValueEth": 0.1}
  },
  "safetyContext": {
    "isSimulationOk": true,
    "warnings": []
  }
}
```

Example quiz flow (EIP-1559):

```bash
# Start
curl -s http://127.0.0.1:8009/tutor/1559/quiz/start

# Answer (replace sessionId)
curl -s http://127.0.0.1:8009/tutor/1559/quiz/answer \
  -H 'Content-Type: application/json' \
  -d '{
    "sessionId": "REPLACE_ME",
    "answer": "用户回答..."
  }'
```

Example ERC-8004 quiz flow:

```bash
# Start
curl -s http://127.0.0.1:8009/tutor/erc8004/quiz/start

# Answer (replace sessionId)
curl -s http://127.0.0.1:8009/tutor/erc8004/quiz/answer \
  -H 'Content-Type: application/json' \
  -d '{
    "sessionId": "REPLACE_ME",
    "answer": "用户回答..."
  }'
```

## 6) Notes

- The Tutor explain endpoints are stateless. If you need full dialogue context,
  send it in on every request (if you choose to add such a field).
- The `/tutor/*/quiz/` endpoints are stateful and keep session context across
  three questions.
- If you only want deterministic responses, skip API keys.
