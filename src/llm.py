"""
llm.py - the ONE place in the project that talks to Gemini.

Every other file calls ask_json(). Keeping all AI calls here means:
  - the API key is loaded in one place (never written in code)
  - busy/rate-limit errors are handled once, with an automatic backup model
    (if the main model gives up, the backup is used for the rest of the run)
  - every answer is cached to disk, so reruns are free and repeatable
  - switching model/provider later means changing only this file
"""
import hashlib
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # reads a .env file if one exists (local use); harmless if not

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
# Backup model(s), used only if the main one keeps failing (busy / quota)
FALLBACK_MODELS = [m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.5-flash-lite").split(",") if m.strip()]
CACHE_DIR = Path(os.getenv("LLM_CACHE_DIR", "cache"))
USE_CACHE = os.getenv("LLM_CACHE", "on").lower() != "off"
ATTEMPTS_PER_MODEL = 3
# Free-tier friendly pacing: at least this many seconds between real API calls (10 calls per minute max)
MIN_SECONDS_BETWEEN_CALLS = float(os.getenv("LLM_MIN_INTERVAL", "6"))

_client = None
_key_source = None
_main_model_busy = False     # becomes True once the main model has failed 3 times in this run
last_model_used = None       # which model produced the most recent answer (or "cache: <model>")
_last_call_time = 0.0


def _find_api_key():
    """Return (key, where_it_came_from). Checks .env/environment, then Kaggle Secrets."""
    key = os.getenv("GEMINI_API_KEY")
    if key and key != "paste-your-key-here":
        return key, ".env file / environment variable"
    try:
        from kaggle_secrets import UserSecretsClient  # only exists on Kaggle
        key = UserSecretsClient().get_secret("GEMINI_API_KEY")
        if key:
            return key, "Kaggle Secrets"
    except Exception:
        pass
    return None, None


def get_client():
    """Create the Gemini client once and reuse it."""
    global _client, _key_source
    if _client is None:
        key, _key_source = _find_api_key()
        if not key:
            raise RuntimeError(
                "No GEMINI_API_KEY found. Locally: add it to .env. "
                "On Kaggle: Add-ons > Secrets, add GEMINI_API_KEY and tick it for this notebook."
            )
        _client = genai.Client(api_key=key)
    return _client


def key_source():
    """Where the API key was loaded from (call after get_client())."""
    return _key_source


def _cache_file(prompt, system, temperature, tag):
    """
    A cache 'fingerprint': the same main model + prompt + settings always gives
    the same file name. If anything changes (even one word), it's a new entry.
    """
    raw = json.dumps({"model": MODEL, "system": system, "prompt": prompt,
                      "temperature": temperature, "tag": tag}, sort_keys=True)
    return CACHE_DIR / (hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16] + ".json")


def _is_temporary(msg):
    """Errors worth waiting for: rate limits (429) and busy servers (503/504)."""
    signs = ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "overloaded", "504", "DEADLINE_EXCEEDED")
    return any(s in msg for s in signs)


def ask_json(prompt, system=None, temperature=0.2, cache_tag="", use_cache=True):
    """
    Send a prompt to Gemini and get back a Python dict/list.

    1. If we've asked this exact question before, return the saved answer (no API call).
    2. Otherwise call the main model in JSON mode, so the reply is machine-readable.
    3. Temporary error (busy / rate limit)? Wait and retry, doubling the wait
       each time ("exponential backoff"), and print the REAL reason.
    4. Still failing after 3 tries? Switch to the backup model and repeat.
    5. Save the answer to the cache for next time (noting which model answered).

    cache_tag lets us deliberately ask the same prompt again for a fresh answer
    (e.g. "deck-attempt-2" when regenerating a deck that broke the rules).
    """
    global _main_model_busy, last_model_used, _last_call_time
    caching = USE_CACHE and use_cache
    path = _cache_file(prompt, system, temperature, cache_tag)
    if caching and path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        last_model_used = f"cache: {saved.get('model_used', 'unknown')}"
        print(f"  [llm] cache hit ({path.name}) - no API call used")
        return saved["response"]

    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        response_mime_type="application/json",
    )
    models = [MODEL] + FALLBACK_MODELS
    if _main_model_busy and FALLBACK_MODELS:
        models = FALLBACK_MODELS   # main model already gave up earlier in this run: go straight to the backup
    last_error = ""
    for model in models:
        wait = 10
        for attempt in range(1, ATTEMPTS_PER_MODEL + 1):
            pause = MIN_SECONDS_BETWEEN_CALLS - (time.time() - _last_call_time)
            if pause > 0:
                time.sleep(pause)           # stay under the free tier's requests-per-minute limit
            _last_call_time = time.time()
            try:
                response = get_client().models.generate_content(model=model, contents=prompt, config=config)
                if not response.text:
                    raise ValueError("empty reply")
                result = json.loads(response.text)
                last_model_used = model
                if model != MODEL:
                    print(f"  [llm] answered by backup model {model}")
                if caching:
                    CACHE_DIR.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps({"model_used": model, "tag": cache_tag,
                                                "prompt_preview": prompt[:300],
                                                "response": result}, indent=2), encoding="utf-8")
                return result
            except (json.JSONDecodeError, ValueError):
                print(f"  [llm] {model}: reply was empty or not valid JSON (try {attempt}), retrying...")
            except Exception as e:
                msg = str(e)
                if not _is_temporary(msg):
                    if "404" in msg or "NOT_FOUND" in msg:
                        raise RuntimeError(
                            f"Model '{model}' is not available to your API key (it may have been retired). "
                            "Run 'python check_setup.py' to list the models you can use, then set GEMINI_MODEL in your .env file.") from e
                    if "API_KEY_INVALID" in msg or "API key not valid" in msg or "PERMISSION_DENIED" in msg:
                        raise RuntimeError("Gemini rejected the API key. Check GEMINI_API_KEY in your .env file (or Kaggle Secrets).") from e
                    raise  # any other real error - stop and show it
                last_error = msg
                print(f"  [llm] {model}: busy / rate limited (try {attempt}). Reason: {msg[:150]}")
                if attempt < ATTEMPTS_PER_MODEL:
                    print(f"        waiting {wait}s...")
                    time.sleep(wait)
                    wait *= 2
        if model == MODEL:
            _main_model_busy = True
        if model != models[-1]:
            print(f"  [llm] giving up on {model}, trying the next model...")
            if model == MODEL:
                print("  [llm] the backup model will be used directly for the rest of this run")
        else:
            print(f"  [llm] giving up on {model} (no other model to try in this run)")
    if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error:
        raise RuntimeError("Gemini quota used up (429 RESOURCE_EXHAUSTED). Free-tier limits reset daily: wait, try another "
                           "model (see check_setup.py), or use a paid key. Cached results still work without any API calls.")
    raise RuntimeError("All models failed (the model is busy or overloaded). Wait a few minutes and run again.")
