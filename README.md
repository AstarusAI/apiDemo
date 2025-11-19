# Our GPT2 x LUTs API

The Astarus API exposes a GPT-2-XL–based language model augmented with per-user Lookup Tables (LUTs) for continuous personalization. LUTs are stored and loaded per lut_name, so each user (or tenant) can “teach” the model and get personalized behavior.

Base URL: ```
      https://fhd5rgv0o0dd8i-8000.proxy.runpod.net/
          ```

No authentication is enforced yet in alpha.

## Endpoints
### 1. Health Check

GET /health

Returns a simple status to verify the service is up.

Response
```json
{
  "status": "ok"
}
```
### 2. Train LUT

Teach the model something for a specific user / LUT namespace.

POST /train_lut

Request body
```json
{
  "label": "TLG Capital is an asset management firm.",
  "label_context": "Optional extra context for this label.",
  "lut_name": "user_123"
}
```

label (string, required)
Text you want the model to learn / bias towards.

label_context (string, optional)
Extra context if your LUT training function uses it.

lut_name (string, required)
Identifier for the LUT namespace (user id, account id, etc.).

Response
```json
{
  "status": "ok",
  "lut_name": "user_123"
}
```
Example (curl)
```bash
curl -X POST "https://api.astarus.ai/train_lut" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "TLG Capital is an asset management firm.",
    "lut_name": "user_123"
  }'
```
### 3. Generate Text

Generate text from the base model + any LUTs associated with the given lut_name.

POST /generate

Request body
```json
{
  "prompt": "TLG Capital is",
  "length": 40,
  "lut_name": "user_123"
}
```

prompt (string, required)
Input text to condition the model on.

length (int, required)
Number of tokens to generate (must be ≤ model context window).

lut_name (string, optional but recommended)
If provided, the per-user LUT for this name is loaded before generation.

Response
```bash
{
  "prompt": "TLG Capital is",
  "completion": " a London-based Africa-focused private credit manager...",
  "lut_name": "user_123"
}
```
Example (curl)
```bash

curl -X POST "https://api.astarus.ai/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "TLG Capital is",
    "length": 40,
    "lut_name": "user_123"
  }'
```
Behavior Notes

Per-user state
All LUT updates are keyed by lut_name. Use a stable identifier per user / org.

Persistence
LUTs are stored in SQLite under the hood and persist across restarts.

Cold start
If no LUT exists yet for a given lut_name, generation falls back to the base GPT-2-XL behavior.

A quick demo in python using the requests library is provided in the repo!
Happy building!
