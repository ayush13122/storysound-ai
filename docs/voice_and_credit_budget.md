# StorySound AI — Bilingual Voice and Credit Budget

## Story
- Hindi title: 2:13 AM — आख़िरी कॉल
- English title: 2:13 AM — The Last Call
- Hindi spoken dialogue: 2,820 characters across 31 clips
- English spoken dialogue: 3,183 characters across 31 clips
- Combined spoken dialogue: 6,003 characters across 62 clips

## Voice allocation
| Voice | Role | Hindi chars | English chars | Combined chars |
|---|---|---:|---:|---:|
| Natraj | Narrator | 1,404 | 1,694 | 3,098 |
| Rahul | Aarav (including outside/reflection imitation) | 396 | 463 | 859 |
| Aravinda | Future Aarav / Caller | 1,020 | 1,026 | 2,046 |
| **Total** | | **2,820** | **3,183** | **6,003** |

The voice allocation above follows the Python credit checker's Unicode-character counts. Small differences can occur if another interface counts grapheme clusters or normalizes punctuation differently.

## Free-plan budget snapshot
The user's dashboard screenshot showed:
- Monthly Free allowance: 10,000 credits
- Previously consumed: 1,449 credits
- Remaining balance at screenshot time: 8,551 credits

Estimated first TTS pass at 1.0x voice multipliers: 6,003 credits.
Estimated balance after first pass: 2,548 credits.

The local project checker is configured with:
- Project hard cap: 7,500 credits
- Retake allowance within cap: 1,497 credits after the planned first pass
- Protected remaining account balance at the hard cap: 1,051 credits, assuming no other account usage

## Assumptions and safeguards
1. The 6,003-credit estimate assumes standard 1.0x multipliers for all three voices. Verify the actual rate shown in ElevenLabs TTS before each batch.
2. Re-check the live account balance immediately before generation; the 8,551 figure is a snapshot, not a live connection.
3. Generate short batches, save each successful clip, and update the local usage ledger after each batch.
4. Do not regenerate the full story to fix one line. Retake only the affected dialogue clip.
5. Stop project generation at 7,500 project credits, or earlier if the live account balance would leave less than 1,000 credits.
6. Python counting, local audio analysis, Audacity editing and local file operations do not consume ElevenLabs TTS credits.
7. Avoid metered ElevenLabs Music, Sound Effects, Dubbing and Speech-to-Text in this budget. Use original or properly licensed local assets instead.
8. Confirm Free-plan voice eligibility and any voice-specific multiplier before generating. Voice Library access through the public API may differ from access in the website TTS interface.

## Production model
The user's TTS screenshots showed Eleven v4 selected. This is a planning estimate based on the displayed 1.0x assumption, not a live account quote. The voice/model interface's displayed credit estimate is the final check before clicking Generate.
