# Tutor Service (Hackathon Demo)

This is a minimal Spoon-powered Tutor service intended for a 3-day demo.

It exposes:
- `GET /health`
- `POST /tutor/1559/explain`
- `POST /tutor/7702/explain`

The service is implemented in `spoon_ai/tutor/service.py` and started via
`examples/tutor_service.py`.

## 1) Run It

From the repo root:

```bash
python -m examples.tutor_service
```

By default it listens on `0.0.0.0:8009`.

## 2) Environment Variables

These are optional but useful:

- `OPENAI_API_KEY=sk-proj-REPLACE_ME`
  - If present, the Tutor Agent will add a short extra note.
  - If missing, the service still works in deterministic mode.
- `TUTOR_LLM_PROVIDER=openai`
  - Provider name for `ChatBot(...)`.
- `TUTOR_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`
  - Comma-separated list.
  - Use `*` to allow all origins (default).
- `TUTOR_HOST=0.0.0.0`
- `TUTOR_PORT=8009`
- `TUTOR_RELOAD=1`

## 2.1 Stateless vs Stateful

The **/tutor/*/explain** endpoints are stateless and do not store conversation
history. If you want continuous dialogue for those endpoints, the frontend
should send the full conversation (or a compressed summary) each time.

The **/tutor/*/quiz/** endpoints are **stateful** by design: the server keeps
session context across three questions in order to generate a final assessment.

## 3) Frontend Contract (Stable JSON Shapes)

### 3.1 EIP-1559 Explain

Endpoint:

- `POST /tutor/1559/explain`

Example request:

```json
{
  "chainId": 1, 
  "baseFeePerGasGwei": 32.5,
  "maxFeePerGasGwei": 60,
  "maxPriorityFeePerGasGwei": 2,
  "gasLimit": 21000,
  "valueEth": 0.01,
  "userIntent": "fast but not too expensive",
  "txContext": {
    "to": "0xabc...",
    "valueEth": 0.01
  }
}
```

Example response shape:

```json
{
  "summary": "...",
  "bullets": ["...", "..."],
  "nextSteps": ["...", "..."],
  "derived": {
    "inclusionLikely": true,
    "effectiveGasPriceGwei": 34.5,
    "effectivePriorityFeeGwei": 2,
    "priorityFeeCapGwei": 27.5,
    "tipIsCapped": false,
    "maxBaseFeeSupportedGwei": 58,
    "baseFeeBufferGwei": 25.5,
    "maxFeeMinusBaseFeeGwei": 27.5,
    "expectedFeeEth": 0.0007245,
    "worstCaseFeeEth": 0.00126,
    "burnedBaseFeeEth": 0.0006825,
    "priorityFeeEth": 0.000042,
    "gasLimit": 21000
  },
  "meta": {
    "standard": "EIP-1559",
    "agentNoteAdded": false
  }
}
```

### 3.2 EIP-7702 Explain

Endpoint:

- `POST /tutor/7702/explain`

Example request:

```json
{
  "chainId": 1,
  "userIntent": "one-click flow",
  "delegationContext": {
    "delegate": "0xDelegate",
    "scope": "only this task",
    "expiry": 1738000000,
    "functions": ["swapExactTokensForTokens"]
  },
  "safetyContext": {
    "isSimulationOk": true,
    "warnings": []
  }
}
```

### 3.3 Quiz (Stateful)

Each EIP has its own 3-question quiz flow.

#### 3.3.1 EIP-1559 Quiz

Start:

- `POST /tutor/1559/quiz/start`

Start response:

```json
{
  "sessionId": "abc123",
  "done": false,
  "questionIndex": 1,
  "assistantMessage": "题目1：..."
}
```

Answer:

- `POST /tutor/1559/quiz/answer`

Request body:

```json
{
  "sessionId": "abc123",
  "answer": "用户回答..."
}
```

Answer response (Q1/Q2):

```json
{
  "sessionId": "abc123",
  "done": false,
  "questionIndex": 2,
  "assistantMessage": "反馈：...\\n\\n题目2：..."
}
```

Final response (Q3):

```json
{
  "sessionId": "abc123",
  "done": true,
  "questionIndex": 3,
  "assistantMessage": "最终反馈：问题在哪 + 如何提高",
  "passed": true
}
```

#### 3.3.2 EIP-7702 Quiz

Start:

- `POST /tutor/7702/quiz/start`

Answer:

- `POST /tutor/7702/quiz/answer`

Request/response shapes are the same as the 1559 quiz.

#### 3.3.3 ERC-8004 Quiz

Start:

- `POST /tutor/erc8004/quiz/start`

Answer:

- `POST /tutor/erc8004/quiz/answer`

Request/response shapes are the same as the 1559 quiz.

## 4) Networking Notes (Most Common Demo Pitfall)

If the frontend runs on a different machine:

1. Keep `TUTOR_HOST=0.0.0.0`.
2. Find your laptop IP on the same network.
3. Frontend should call `http://<your-ip>:8009/...`.
4. Set:
   - `TUTOR_CORS_ORIGINS=http://<frontend-host>:<port>`

For quick public demos, you can also tunnel the service (for example, with a
TCP/HTTP tunnel) and point the frontend at the tunnel URL.
