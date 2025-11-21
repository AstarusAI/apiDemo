
# Astarus LUT-LLM API

The Astarus API exposes large language models augmented with per-user Lookup Tables (LUTs) for continuous learning and personalization.

* **Base models (current alpha):**

  * **GPT-2-XL** (fast, lightweight)
  * **Mistral-7B-Instruct** (higher quality, more capable)
* **Personalization mechanism:** per-user LUTs keyed by `lut_name`
* **Storage:** LUTs are persisted in SQLite and survive restarts
* **State:** No authentication in alpha, but you should still treat your `lut_name`s as private identifiers

> **Base URL**

In alpha, the raw RunPod URL:

```text
https://fhd5rgv0o0dd8i-8000.proxy.runpod.net/
```

---

## Models

Most endpoints accept a `model` field:

* `"gpt2"` – GPT-2-XL with LUTs (default if omitted)
* `"mistral"` – Mistral-7B-Instruct with LUTs

LUTs are **model-specific**: training a LUT with `model: "mistral"` will affect `mistral` generations only; `gpt2` will use its own LUTs.

---

## 1. Health Check

**GET** `/health`

Simple status check to verify the service is up.

**Response**

```json
{
  "status": "ok"
}
```

---

## 2. Train LUT

Teach the model something for a specific user / tenant / LUT namespace.
This is how you “inject” facts, preferences and style into the per-user LUT.

**Endpoint**

**POST** `/train_lut`

### Request body

```json
{
  "label": "TLG Capital is an asset management firm.",
  "label_context": "Optional extra context for this label.",
  "lut_name": "user_123",
  "model": "mistral"
}
```

* `label` (**string, required**)
  The content you want the model to learn / bias toward. Think of this as the “ground truth” snippet.

* `label_context` (**string, optional**)
  Extra context to anchor the label, for example:

  * `"Assistant: "`
  * `"User: What is TLG Capital?\nAssistant:"`
    This helps the LUT specialize to specific conversational shapes.

* `lut_name` (**string, required**)
  A stable identifier for the LUT namespace:

  * User id (`"user_123"`)
  * Account id (`"tlg_capital_internal"`)
  * Session id (`"rafi-test-11"`)

* `model` (**string, optional**)
  Which base model to train the LUT on:

  * `"gpt2"` (default if omitted)
  * `"mistral"`

### Response

```json
{
  "status": "ok",
  "lut_name": "user_123",
  "model": "mistral"
}
```

### Example (curl)

```bash
curl -X POST "https://api.astarus.ai/train_lut" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "TLG Capital is an asset management firm.",
    "label_context": "Assistant: ",
    "lut_name": "user_123",
    "model": "mistral"
  }'
```

---

## 3. Generate Text

Generate text from the **base model + any LUTs** associated with the given `lut_name`.

**Endpoint**

**POST** `/generate`

### Request body

```json
{
  "prompt": "User: What is TLG Capital?\nAssistant:",
  "length": 40,
  "lut_name": "user_123",
  "model": "mistral",
  "threshold": 0.25
}
```

* `prompt` (**string, required**)
  The text to condition the model on.

* `length` (**int, required**)
  Number of tokens to generate. Must fit within the model’s context window.

* `lut_name` (**string, optional but recommended**)

  * If provided, the per-user LUT for this name is loaded and applied.
  * If not provided, you get the **base** model behavior with no personalization.

* `model` (**string, optional**)

  * `"gpt2"` (default) or `"mistral"`.

* `threshold` (**float, optional – new**)
  Controls how strongly the LUT influences the model.

  Intuition (exact implementation details may evolve):

  * Lower threshold (e.g. `0.1`) → LUT fires more often → **stronger personalization**
  * Higher threshold (e.g. `0.5`) → LUT only kicks in for close matches → **more conservative bias**

  If omitted, the server uses a reasonable default.

### Response

```json
{
  "prompt": "User: What is TLG Capital?\nAssistant:",
  "completion": " TLG Capital is a London-based Africa-focused private credit manager...",
  "lut_name": "user_123",
  "model": "mistral"
}
```

### Example (curl)

```bash
curl -X POST "https://api.astarus.ai/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "User: What is TLG Capital?\nAssistant:",
    "length": 40,
    "lut_name": "user_123",
    "model": "mistral",
    "threshold": 0.25
  }'
```

---

## 4. Python Quickstart

Here’s a small Python client using `requests` that shows the **new fields** (`model`, `threshold`) and both **train** + **generate** for Mistral:

```python
import requests

BASE_URL = "https://fhd5rgv0o0dd8i-8000.proxy.runpod.net/"
# Or, if you have the domain wired up:
# BASE_URL = "https://api.astarus.ai"

def generate(prompt, length=20, lut_name=None, model="mistral", threshold=0.25):
    payload = {
        "prompt": prompt,
        "length": length,
        "model": model,      # "mistral" or "gpt2"
        "threshold": threshold,
    }
    if lut_name is not None:
        payload["lut_name"] = lut_name

    r = requests.post(f"{BASE_URL}/generate", json=payload)
    print("Status:", r.status_code)
    try:
        print("Response:", r.json())
    except Exception:
        print("Raw response:", r.text)


def train_lut(label, lut_name="user_123", label_context=None, model="mistral"):
    payload = {
        "label": label,
        "lut_name": lut_name,
        "label_context": label_context,
        "model": model,  # "mistral" or "gpt2"
    }
    r = requests.post(f"{BASE_URL}/train_lut", json=payload)
    print("Status:", r.status_code)
    try:
        print("Response:", r.json())
    except Exception:
        print("Raw response:", r.text)


if __name__ == "__main__":
    # 1) Train a LUT for a specific user / namespace on Mistral
    train_lut(
        "Astarus is building continuously trainable LLMs.",
        lut_name="rafi-test-11",
        label_context="Assistant: ",
        model="mistral",
    )

    # 2) Generate using Mistral + that LUT
    generate(
        "User: What is Astarus?\nAssistant:",
        length=15,
        lut_name="rafi-test-11",
        model="mistral",
        threshold=0.25,
    )
```

---

## Behavior & Design Notes

* **Per-user state (`lut_name`)**

  * All LUT updates are keyed by `lut_name` (and logically by `model`).
  * Use a **stable** identifier per user / org.

* **Persistence**

  * LUTs are stored in SQLite.
  * They persist across process restarts.

* **Cold start**

  * If no LUT exists yet for a given `(lut_name, model)`, generation falls back to the base model.

* **Model choice**

  * Use `gpt2` for cheaper, faster personalization experiments.
  * Use `mistral` when you care more about output quality and instruction-following.

* **Safety**

  * The API is alpha; there is no authentication yet. Don’t expose this endpoint publicly without a gateway or auth layer in front of it.

