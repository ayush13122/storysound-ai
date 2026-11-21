from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "scripts" / "bilingual_story.json"

# Update these values from the live ElevenLabs dashboard before production.
CURRENT_BALANCE = 8551
PROJECT_CAP = 7500
VOICE_MULTIPLIERS = {
    "NARRATOR": 1.0,
    "AARAV": 1.0,
    "CALLER": 1.0,
}

payload = json.loads(DATA.read_text(encoding="utf-8"))
voice_totals = {
    key: {"segments": 0, "characters": 0, "words": 0}
    for key in payload["voices"]
}
language_totals = {}

for lang in payload["languages"].values():
    language_totals[lang["name"]] = {
        "segments": 0, "characters": 0, "words": 0
    }
    for clip in lang["segments"]:
        voice = clip["voice_speaker"]
        text = clip["text"]
        chars = len(text)
        words = len(text.split())

        voice_totals[voice]["segments"] += 1
        voice_totals[voice]["characters"] += chars
        voice_totals[voice]["words"] += words

        language_totals[lang["name"]]["segments"] += 1
        language_totals[lang["name"]]["characters"] += chars
        language_totals[lang["name"]]["words"] += words

total_chars = sum(item["characters"] for item in voice_totals.values())
estimated_credits = sum(
    item["characters"] * VOICE_MULTIPLIERS[voice]
    for voice, item in voice_totals.items()
)

print("StorySound AI — Bilingual TTS credit estimate")
print("=" * 52)
for language, values in language_totals.items():
    print(
        f"{language:10} | {values['segments']:2} clips | "
        f"{values['characters']:5} characters | {values['words']:4} words"
    )

print("-" * 52)
for voice, values in voice_totals.items():
    multiplier = VOICE_MULTIPLIERS[voice]
    cost = values["characters"] * multiplier
    voice_name = payload["voices"][voice]["name"]
    print(
        f"{voice_name:10} | {values['segments']:2} clips | "
        f"{values['characters']:5} chars | "
        f"multiplier {multiplier:.2f}x | est. {cost:.0f} credits"
    )

print("-" * 52)
print(f"Total dialogue segments : {sum(x['segments'] for x in voice_totals.values())}")
print(f"Total spoken characters : {total_chars}")
print(f"Estimated TTS credits    : {estimated_credits:.0f}")
print(f"Current balance entered  : {CURRENT_BALANCE}")
print(f"Project hard cap         : {PROJECT_CAP}")
print(f"Balance after first pass : {CURRENT_BALANCE - estimated_credits:.0f}")
print(f"Project cap remaining    : {PROJECT_CAP - estimated_credits:.0f}")
print("\nThis is a local estimate, not a live account-balance check.")
print("Verify live balance and each selected voice's multiplier in ElevenLabs before generating.")
print("Local Python, audio analysis, Audacity editing and local file operations do not consume ElevenLabs TTS credits.")

if estimated_credits > PROJECT_CAP:
    print("\nSTOP: Estimated first pass exceeds the project hard cap.")
    sys.exit(2)
if estimated_credits > CURRENT_BALANCE:
    print("\nSTOP: Estimated first pass exceeds the entered account balance.")
    sys.exit(3)
if CURRENT_BALANCE - estimated_credits < 1000:
    print("\nSTOP: Less than 1,000 account credits would remain after first pass.")
    sys.exit(4)

print("\nPASS: Both language versions fit the entered balance and project cap.")
