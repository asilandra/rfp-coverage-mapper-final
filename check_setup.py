"""
check_setup.py - run this first to confirm everything works.
    python check_setup.py
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")   # Windows: print "?" instead of crashing on special characters

from src.llm import MODEL, ask_json, get_client, key_source

print("1) Checking API key...")
client = get_client()
print(f"   OK - key loaded from: {key_source()}")

print("\n2) Text-generation Flash models your key can use:")
for m in client.models.list():
    name = m.name.replace("models/", "")
    actions = getattr(m, "supported_actions", None) or []
    skip = any(w in name for w in ("tts", "image", "audio", "live", "embedding"))
    if "generateContent" in actions and "flash" in name and not skip:
        print("   -", name)

print(f"\n3) Test call to {MODEL} (cache off, so this is a real API call)...")
reply = ask_json('Return JSON exactly like this: {"status": "ok", "message": "<one short greeting>"}',
                 use_cache=False)
print("   Gemini replied:", reply)
print("\nAll good - you're ready to generate the test data.")
