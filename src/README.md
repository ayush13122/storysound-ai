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
