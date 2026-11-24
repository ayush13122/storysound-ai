# StorySound AI
## AI-Powered Multilingual Audio Production Studio

**Status: Bilingual story production and technical audio audit completed — portfolio packaging in progress**

StorySound AI is an end-to-end learning and portfolio project focused on producing Hindi and English audio stories through AI-assisted voice generation, hands-on audio editing, sound design, and Python-based audio analysis.

### Current production story
**2:13 AM — The Last Call / 2:13 AM — आख़िरी कॉल**

A psychological-horror and time-loop mystery prepared in two language versions:
- Hindi: 31 dialogue clips, 2,820 spoken characters.
- English: 31 dialogue clips, 3,183 spoken characters.
- Combined: 62 dialogue clips and 6,003 spoken characters.

The same three voice identities are assigned across both language versions:
- **Natraj:** narrator
- **Rahul:** Aarav, including the outside/reflection imitation
- **Aravinda:** future Aarav / caller

See `assets/scripts/hindi_story.md` and `assets/scripts/english_story.md` for the production scripts. Speaker labels, scene headings, and SFX directions are not included in spoken-text character counts.

### Planned capabilities
- Generate Hindi and English narration and character dialogue using ElevenLabs TTS, subject to voice and plan eligibility.
- Maintain a consistent voice cast and document voice settings and pronunciation decisions.
- Edit dialogue in Audacity; apply noise reduction, equalization, telephone filtering, distance effects, and volume balancing where appropriate.
- Layer original or properly licensed music, ambience, and sound effects.
- Build Python tools to inspect duration, sample rate, channels, peak and RMS levels, clipping, silence, and WAV/MP3 metadata.
- Produce quality reports and compare raw voice output with edited final audio.

### Production workflow
1. Finalize original Hindi and English dialogue scripts.
2. Verify Free-plan voice eligibility, model, and credit multipliers.
3. Generate dialogue in small, tracked batches and preserve every successful clip.
4. Edit dialogue and sound design in Audacity.
5. Inspect audio properties and quality with Python.
6. Export final WAV/MP3 versions and perform a listening review.

### Credit planning
The local estimate for the first bilingual TTS pass is **6,003 credits**, assuming a 1.0x multiplier for each selected voice. This is a planning estimate, not a live account balance or a guarantee of voice eligibility. See `docs/voice_and_credit_budget.md` for the dated account snapshot and safeguards.

### Technology stack
- **ElevenLabs:** AI voice generation
- **Audacity:** audio editing and mixing
- **Python:** script processing, credit estimation, audio analysis, and workflow utilities

### Planned repository structure
```text
storysound-ai/
├── assets/
│   ├── scripts/
│   │   ├── hindi_story.md
│   │   └── english_story.md
│   ├── raw_audio/
│   ├── sound_effects/
│   └── background_music/
├── output/
│   ├── hindi/
│   └── english/
├── src/
├── reports/
├── docs/
│   └── voice_and_credit_budget.md
├── requirements.txt
├── .gitignore
└── README.md
```

### Responsible use
Use original scripts and audio assets that you own or are licensed to use. Only clone or imitate a voice with the voice owner's explicit authorization. Do not upload API keys, private credentials, or unlicensed audio assets.

### Production tools
- Structured bilingual dialogue: `assets/scripts/bilingual_story.json`
- Local credit estimator: `src/credit_budget.py`
- Local setup instructions: `docs/INSTALL_BILINGUAL_UPDATE.md`

Run the local estimator without calling ElevenLabs:

```powershell
python src/credit_budget.py
```

Before voice generation, update the balance snapshot and confirm actual voice multipliers in the ElevenLabs interface. The script is a local estimate only and does not read the live account balance.


### Audio analysis and quality audit

The project includes local Python tooling for source WAV inspection, scene-master assembly, and read-only technical analysis of the finished Hindi and English mixes:

- `src/audio_audit.py`: checks the 10 scene-level WAVs (five per language).
- `src/build_story_masters.py`: assembles scene-level WAVs into language masters.
- `src/analyze_final_mixes.py`: measures final-mix metadata, sample peak, RMS, near-silence, and—when FFmpeg is installed—EBU R128 Integrated Loudness, LRA, and True Peak.
- `reports/final_mix_audio_audit.md`: final measurement report and methodology.
- `reports/final_mix_audio_audit_snapshot.json` and `reports/final_mix_audio_audit_snapshot.csv`: machine-readable audit snapshots.

The latest user-supplied measurement snapshot records Hindi at -23.72 LUFS / -0.88 dBTP and English at -24.34 LUFS / -1.20 dBTP. Both latest files had zero samples at or above the analyzer's -0.01 dBFS near-full-scale threshold. This counter is not a definitive hard-clipping detector. The current decision is to keep the audio mixes unchanged.

Large WAV/MP3 binaries and Audacity session files are kept locally rather than committed to Git; see `.gitignore`.
