# 📉 ANTIGRAVITY REPAIR LOG

## Context
Trajectory ID: cbfdc2eb-6b79-4884-aca7-f153052acda7 hit a "truncation error" in Jetski/Cortex.
This was likely caused by:
1. Massive single-message payloads (reading/printing base64 image data).
2. Infinite loop in "AUTO-RECOVERY" rule (Error → Diagnose → Auto-fix).
3. Attempting to use non-existent model versions (Gemini 3.1, Imagen 4.0).

## 🛠️ REPAIR ACTIONS

### 1. Model Fidelity Correction
The application was using hallucinated model names (Gemini 3.1, Imagen 4.0, Gemini 2.5). These have been downgraded to current stable versions (Gemini 1.5 Flash, Imagen 3.0) to ensure the system actually runs and doesn't trigger error recovery loops.

### 2. Context Safety Rules
- **NEVER** read large image files (PNG/JPG) with `read_file`. Use `list_directory` to confirm they exist.
- **NEVER** print raw base64 strings to the console/log during "Diagnosis".
- **TRUNCATE** all large outputs before they hit the agent's history.
- **MAX 3 RECOVERY CYCLES**: If a fix fails 3 times, stop and ask for human intervention.

### 3. Compact Engine Optimization
- Keep `app.py` logic concise.
- Use `grep_search` with narrow context to avoid reading the whole file.
- **NEVER** run scripts that output massive amounts of data (e.g., `generate_index.py`, `build-catalog.js`) without redirecting output to a file (e.g., `> output.txt`). Large stdout will crash the agent's history.
