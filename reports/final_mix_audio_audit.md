# StorySound AI — Final Audio Quality Audit

**Story:** 2:13 AM — The Last Call / 2:13 AM — आख़िरी कॉल  
**Snapshot date:** 2026-11-25  
**Source:** Final-mix analyzer output supplied by the project owner  
**Decision:** Keep the current Hindi and English mixes as-is; no further audio edits are planned.

## Final mix measurements

| Metric | Hindi | English |
|---|---:|---:|
| Duration | 6 min 45 sec | 5 min 58 sec |
| Container | WAV | WAV |
| Sample rate | 48,000 Hz | 48,000 Hz |
| Channels | Stereo (2) | Stereo (2) |
| Subtype | PCM_16 | PCM_16 |
| File size | 74.17 MB | 65.63 MB |
| Sample peak | -0.88 dBFS | -1.20 dBFS |
| RMS | -25.82 dBFS | -26.17 dBFS |
| Samples at or above -0.01 dBFS | 0 | 0 |
| Integrated loudness | -23.72 LUFS | -24.34 LUFS |
| Loudness range (LRA) | 17.60 LU | 12.20 LU |
| True peak | -0.88 dBTP | -1.20 dBTP |
| Near-silence share | 5.18% | 3.69% |
| Near-silence regions >= 0.2 sec | 18 | 10 |

## Audit history

### Initial measurement before the gain-reduced re-audit

| Metric | Hindi | English |
|---|---:|---:|
| Sample peak | 0.0 dBFS | 0.0 dBFS |
| RMS | -13.83 dBFS | -14.67 dBFS |
| Samples at or above -0.01 dBFS | 390,036 | 413,475 |
| Near-silence share | 3.70% | 3.63% |
| Near-silence regions >= 0.2 sec | 18 | 21 |
| EBU R128 | Not available in that run | Not available in that run |

### Latest measurement after gain reduction

The latest analyzer run reported zero samples at or above its -0.01 dBFS threshold in both mixes. FFmpeg was available and the analyzer returned Integrated LUFS, LRA, and True Peak measurements.

## Metric definitions and interpretation

- **Sample peak (dBFS):** Maximum decoded sample amplitude relative to digital full scale.
- **RMS (dBFS):** Whole-file signal energy estimate. RMS is not the same as perceived loudness.
- **Integrated loudness (LUFS):** EBU R128 loudness measurement over the complete file.
- **LRA (LU):** Loudness Range; describes variation in loudness over time. It does not, by itself, prove whether dialogue is intelligible.
- **True Peak (dBTP):** Estimated peak of the reconstructed waveform, which can exceed the highest stored sample value.
- **Near-silence:** The analyzer classifies 100 ms windows below -55 dBFS RMS as near-silence. In a psychological-horror story, some of these may be intentional pauses.

### Important limitation: near-full-scale counter

The Python analyzer's counter is based on **absolute normalized sample amplitude >= 0.999**, approximately -0.01 dBFS. It is a **near-full-scale sample counter**, not a definitive detector of hard-clipped flat-topped waveforms. Therefore, the earlier counts (390,036 Hindi; 413,475 English) should not be interpreted as a proven number of hard-clipped samples. The latest count of zero means no decoded samples crossed that threshold in the latest exports; it does not prove that any distortion introduced earlier was repaired.

## Production notes

- Both files were read and analyzed without modifying the audio.
- The FFmpeg loudness analysis was measurement-only; it did not normalize or rewrite either WAV.
- No ElevenLabs API request was made and no ElevenLabs credits were consumed by analysis.
- The exports are 48 kHz stereo PCM_16. The older project reference was 44.1 kHz mono; the difference is documented, not treated as an automatic defect. 48 kHz stereo is a valid delivery configuration.
- PCM_24 was suggested as an optional high-resolution delivery target in the original analyzer warning. Converting a 16-bit export to 24-bit later does not restore lost precision, so no such conversion is claimed here.
- The current project-owner decision is to retain the mixes as-is. This report records technical measurements only; it is not a substitute for a subjective listening review.

## Reproducibility

Run the final mix analyzer from the repository root:

```powershell
python src/analyze_final_mixes.py
```

Expected default input paths:

- `output/final_mixes/hindi_final_mix.wav`
- `output/final_mixes/english_final_mix.wav`

The analyzer writes local JSON and CSV outputs under `reports/`. The report files committed here are a curated snapshot of the terminal results supplied by the project owner. Large audio binaries remain local and are excluded from Git by the repository's audio ignore rules.
