# Bilingual Production Update

This folder set adds the production-ready Hindi and English scripts, a structured dialogue manifest, and a local TTS credit calculator.

## Install in the existing Windows project

Extract/merge these files into the root of `D:\storysound-ai`:

- `assets/scripts/hindi_story.md`
- `assets/scripts/english_story.md`
- `assets/scripts/bilingual_story.json`
- `src/credit_budget.py`
- `docs/voice_and_credit_budget.md`

Then run:

```powershell
python src/credit_budget.py
```

## Before any generation

1. Replace `CURRENT_BALANCE` in `src/credit_budget.py` with the current live balance shown in ElevenLabs.
2. Confirm each selected voice's multiplier in the TTS interface. Change `VOICE_MULTIPLIERS` only after verifying it.
3. Keep the project hard cap at 7,500 unless the user explicitly changes the budget.
4. Generate in small batches and save successful clips. Do not regenerate the entire story to fix one line.

This script only counts local JSON dialogue text. It does not call ElevenLabs and does not spend credits.
