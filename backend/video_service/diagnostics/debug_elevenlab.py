#!/usr/bin/env python3
"""
Debug ElevenLabs timestamps support.

This script answers three questions:

1) Is the ElevenLabs SDK installed and which version?
2) Does the SDK expose `text_to_speech.convert_with_timestamps`?
3) Does the raw HTTP endpoint `/v1/text-to-speech/{voice_id}/with-timestamps`
   return timestamps for your account?
"""

import os
import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- IMPORT YOUR CONFIG / SERVICE ------------------------------------
from backend.shared.utils.config import Config

print("=" * 70)
print("ELEVENLABS TIMESTAMPS DEBUG")
print("=" * 70)

# STEP 1: Basic config sanity check
print("\n[STEP 1] Config check")
api_key = Config.ELEVENLABS_API_KEY
voice_id = Config.ELEVENLABS_VOICE_ID

print(f" - ELEVENLABS_API_KEY present? {'YES' if api_key else 'NO'}")
print(f" - ELEVENLABS_VOICE_ID: {voice_id!r}")

if not api_key:
    print(" ❌ No API key set. Set ELEVENLABS_API_KEY in your .env first.")
    sys.exit(1)

# STEP 2: SDK availability and capabilities
print("\n[STEP 2] ElevenLabs SDK check")
try:
    import elevenlabs
    from elevenlabs.client import ElevenLabs

    print(f" - elevenlabs package version: {getattr(elevenlabs, '__version__', 'unknown')}")
    client = ElevenLabs(api_key=api_key)

    has_tts = hasattr(client, "text_to_speech")
    print(f" - client.text_to_speech available? {has_tts}")

    if has_tts:
        tts_obj = client.text_to_speech
        methods = [m for m in dir(tts_obj) if not m.startswith("_")]
        print(f" - text_to_speech methods: {methods}")
        print(f" - has convert_with_timestamps? {'convert_with_timestamps' in methods}")
    else:
        print(" ❌ client.text_to_speech missing on this SDK version")

except ImportError as e:
    print(f" ❌ elevenlabs package not installed: {e}")
    print("    Run: uv add elevenlabs")
    sys.exit(1)

# STEP 3: Try SDK convert_with_timestamps (if exposed)
print("\n[STEP 3] Testing SDK convert_with_timestamps (if available)")
test_text = "Hello world. This is a short test for timestamps."
try:
    if has_tts and hasattr(client.text_to_speech, "convert_with_timestamps"):
        try:
            resp = client.text_to_speech.convert_with_timestamps(
                voice_id=voice_id,
                text=test_text,
                model_id="eleven_multilingual_v2",
            )
            print(" ✅ convert_with_timestamps call succeeded")
            print(f"   Response type: {type(resp)}")

            if isinstance(resp, dict):
                print(f"   Top-level keys: {list(resp.keys())}")
                alignment = resp.get("alignment") or resp.get("normalizedAlignment") or {}
                print(f"   alignment type: {type(alignment)}; keys: {list(alignment.keys()) if isinstance(alignment, dict) else 'n/a'}")

                # Inspect a bit of alignment if present
                if isinstance(alignment, dict):
                    chars = alignment.get("characters") or []
                    starts = alignment.get("character_start_times_seconds") or []
                    print(f"   characters len: {len(chars)}, starts len: {len(starts)}")
            else:
                # Might be an SDK object
                print("   Attributes on resp:", [a for a in dir(resp) if not a.startswith("_")][:20])
                alignment = getattr(resp, "alignment", None)
                print("   alignment attr type:", type(alignment))
        except Exception as e:
            print(" ❌ convert_with_timestamps raised an exception:")
            print(f"   {type(e).__name__}: {e}")
    else:
        print(" ⚠️ convert_with_timestamps not available on this SDK.")
        print("    This might mean your SDK version predates timestamps support.")
except Exception as e:
    print(" ❌ Unexpected error while testing convert_with_timestamps:", e)

# STEP 4: Call raw HTTP endpoint /with-timestamps
print("\n[STEP 4] Testing raw HTTP /with-timestamps endpoint")
try:
    import requests
except ImportError as e:
    print(f" ❌ requests not installed: {e}")
    print("    Run: uv add requests")
    sys.exit(1)

url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
headers = {
    "xi-api-key": api_key,
    "Content-Type": "application/json",
}

payload = {
    "text": test_text,
    # model_id from ElevenLabs docs – adjust if your dashboard shows a different one
    "model_id": "eleven_multilingual_v2",
    # what kind of timestamps you want – some accounts expose `characters` only
    "timestamp_type": "characters",
}

print(f" - POST {url}")
resp = requests.post(url, headers=headers, json=payload)

print(f" - Status code: {resp.status_code}")
if resp.status_code != 200:
    print(" ❌ Non-200 response, raw text:")
    print(resp.text[:500])
else:
    print(" ✅ HTTP with-timestamps response OK")
    try:
        data = resp.json()
    except Exception as e:
        print(" ❌ Could not parse JSON:", e)
        print("    First 300 bytes:", resp.content[:300])
        sys.exit(1)

    print("   Top-level keys:", list(data.keys()))
    if "alignment" in data:
        a = data["alignment"]
        print("   alignment keys:", list(a.keys()))
        chars = a.get("characters") or []
        starts = a.get("character_start_times_seconds") or []
        print(f"   characters len: {len(chars)}, starts len: {len(starts)}")
    else:
        print("   No 'alignment' key in response – check ElevenLabs docs / plan.")

print("\n[SUMMARY]")
print(" - Use the output of STEP 3 and STEP 4 to decide:")
print("   * Does your plan actually support /with-timestamps?")
print("   * Does your SDK expose convert_with_timestamps or do we need raw HTTP?")
print("=" * 70)
