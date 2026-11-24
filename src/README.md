# Python Source Code

Python modules for audio metadata inspection, signal measurements, quality checks, report generation, and workflow automation will be implemented here.


## Audio Audit

Run the local WAV integrity and metadata audit from the repository root:

```powershell
python src/audio_audit.py
```

The script scans `assets/raw_audio/hindi/` and `assets/raw_audio/english/`, checks every WAV by decoding it in blocks, and reports duration, sample rate, channels, bit depth, file size, peak level, RMS level, and possible near-full-scale samples. It writes:

- `reports/audio_audit_report.csv`
- `reports/audio_audit_summary.json`

This is a local-only operation. It does not call ElevenLabs or consume API credits. It uses the existing `numpy` and `soundfile` dependencies in `requirements.txt`.


## Story Master Builder

Join the five scene WAVs into one continuous WAV master per language:

```powershell
python src/build_story_masters.py
```

By default, the script inserts 1.5 seconds of silence between scenes. Use `--gap-seconds 2.0` to choose a different pause. It reads from `assets/raw_audio/hindi/` and `assets/raw_audio/english/`, then writes the masters under `output/hindi/` and `output/english/`. Scene timing is saved in `reports/story_master_manifest.json`.

The script streams audio in blocks, verifies that each language has five WAVs with matching sample rate and channel count, preserves the source files, and does not normalize or add effects. It runs locally and does not call ElevenLabs or consume credits.


## Final Mix Audio Analyzer

Place the Audacity final WAV exports in `output/final_mixes/` as `hindi_final_mix.wav` and `english_final_mix.wav`, then run:

```powershell
python src/analyze_final_mixes.py
```

Or pass explicit paths:

```powershell
python src/analyze_final_mixes.py --hindi "D:\path\Hindi.wav" --english "D:\path\English.wav"
```

The read-only analyzer reports duration, sample rate, channels, encoding, sample peak, RMS, near-silence regions and clipped samples. When FFmpeg is installed and on PATH, it also measures EBU R128 integrated loudness (LUFS), loudness range (LRA), and true peak. It does not change the audio or call ElevenLabs. Reports are written to `reports/final_mix_audio_audit.json` and `reports/final_mix_audio_audit.csv`.
