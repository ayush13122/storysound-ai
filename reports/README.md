# Audio Quality Reports

This directory contains reproducible local analyzer outputs and curated snapshots of the project's bilingual audio quality checks.

## Final mix audit

- `final_mix_audio_audit.md`: human-readable audit report, measurement definitions, interpretation, caveats, and current project decision.
- `final_mix_audio_audit_snapshot.json`: structured snapshot of the initial and latest measurements.
- `final_mix_audio_audit_snapshot.csv`: tabular comparison of Hindi and English measurements across the two audit stages.

To regenerate analyzer output locally, keep the WAV files in `output/final_mixes/` and run:

```powershell
python src/analyze_final_mixes.py
```

The analyzer writes `final_mix_audio_audit.json` and `final_mix_audio_audit.csv` locally. Final audio binaries are excluded from Git; only reports and code are versioned.

## Raw scene audio audit

The `src/audio_audit.py` tool checks the five source scene WAV files per language and writes local `audio_audit_report.csv` and `audio_audit_summary.json` files. See `src/README.md` for commands.
