# 📉 ANTIGRAVITY REPAIR LOG

## Context
Trajectory ID: cbfdc2eb-6b79-4884-aca7-f153052acda7 hit a "truncation error" in Jetski/Cortex.
Trajectory ID: 93eb9b86-214d-4dc8-8054-650d3784ccc3 also hit "could not convert a single message before hitting truncation".

This was caused by:
1. Massive single-message payloads (reading/printing base64 image data).
2. Infinite loop in "AUTO-RECOVERY" rule (Error → Diagnose → Auto-fix).
3. Attempting to use non-existent model versions (Gemini 3.1, Imagen 4.0).
4. Tool inputs containing large base64 lists being captured in conversation history.

## 🛠️ REPAIR ACTIONS

### 1. Model Fidelity Correction
The application was using hallucinated model names. These have been downgraded to current stable versions to ensure the system actually runs and doesn't trigger error recovery loops.
- **Stable Models**: `gemini-2.0-flash-exp`, `gemini-1.5-pro-002`, `imagen-3.0-generate-001`.

### 2. Context Safety Rules
- **NEVER** read large image files (PNG/JPG) with `read_file`. Use `list_directory` to confirm they exist.
- **NEVER** print raw base64 strings to the console/log during "Diagnosis".
- **TRUNCATE** all large outputs before they hit the agent's history.
- **MAX 3 RECOVERY CYCLES**: If a fix fails 3 times, stop and ask for human intervention.
- **SURGICAL LOGGING**: `app.py` now truncates exception messages to 500 characters to prevent base64 leakage into stdout.
- **TOOL INPUT LIMIT**: Avoid calling tools (like `analyze_room_image` or `replace`) with arguments exceeding 100KB in a single message.

### 3. Compact Engine Optimization
- Keep `app.py` logic concise.
- Use `grep_search` with narrow context to avoid reading the whole file.
- **NEVER** run scripts that output massive amounts of data without redirecting output to a file (e.g., `> output.txt`).
