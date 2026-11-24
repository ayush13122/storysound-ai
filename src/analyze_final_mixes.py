"""Technical audit for the final Hindi and English StorySound WAV mixes.

Uses the project's existing NumPy and SoundFile dependencies. If FFmpeg is
available, also reads EBU R128 integrated loudness, loudness range and true
peak via the loudnorm analysis pass. This script never modifies the audio.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

BLOCK_FRAMES = 131_072


def dbfs(value: float) -> float | None:
    if value <= 0:
        return None
    return round(20.0 * math.log10(value), 2)


def ffmpeg_loudness(path: Path) -> dict[str, Any] | None:
    """Return FFmpeg loudnorm measurement values, or None if unavailable."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None

    command = [
        ffmpeg, "-hide_banner", "-nostats", "-i", str(path),
        "-af", "loudnorm=I=-16:TP=-1.0:LRA=11:print_format=json",
        "-f", "null", "-"
    ]
    completed = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False
    )
    combined = completed.stderr + "\n" + completed.stdout
    matches = re.findall(r"\{\s*\"input_i\".*?\}", combined, flags=re.DOTALL)
    if not matches:
        return {
            "available": True,
            "error": "FFmpeg was found, but the EBU R128 measurement could not be parsed.",
            "return_code": completed.returncode,
        }

    try:
        measured = json.loads(matches[-1])
        return {
            "available": True,
            "integrated_lufs": measured.get("input_i"),
            "loudness_range_lu": measured.get("input_lra"),
            "threshold_lufs": measured.get("input_thresh"),
            "true_peak_dbtp": measured.get("input_tp"),
            "target_i_lufs": measured.get("target_i"),
            "target_tp_dbtp": measured.get("target_tp"),
            "target_lra_lu": measured.get("target_lra"),
        }
    except (json.JSONDecodeError, TypeError):
        return {
            "available": True,
            "error": "FFmpeg loudness JSON was invalid.",
            "return_code": completed.returncode,
        }


def analyze_wav(label: str, path: Path, silence_threshold_dbfs: float) -> dict[str, Any]:
    result: dict[str, Any] = {
        "label": label,
        "file": str(path),
        "status": "PASS",
    }
    if not path.exists():
        result.update(status="ERROR", error=f"File not found: {path}")
        return result

    try:
        info = sf.info(str(path))
        if info.frames <= 0 or info.samplerate <= 0 or info.channels <= 0:
            raise ValueError("Invalid or empty WAV header")

        sample_count = 0
        sum_squares = 0.0
        peak = 0.0
        clipped_samples = 0
        silent_frames = 0
        silence_regions: list[dict[str, float]] = []
        active_silence_start: float | None = None
        frame_cursor = 0
        window_frames = max(1, round(info.samplerate * 0.1))
        pending = np.empty((0, info.channels), dtype=np.float32)

        with sf.SoundFile(str(path), mode="r") as audio:
            while True:
                block = audio.read(BLOCK_FRAMES, dtype="float32", always_2d=True)
                if block.size == 0:
                    break

                absolute = np.abs(block)
                sample_count += int(block.size)
                sum_squares += float(np.sum(np.square(block), dtype=np.float64))
                peak = max(peak, float(np.max(absolute)))
                clipped_samples += int(np.count_nonzero(absolute >= 0.999))
                pending = np.concatenate((pending, block), axis=0)

                while len(pending) >= window_frames:
                    window = pending[:window_frames]
                    pending = pending[window_frames:]
                    rms = float(np.sqrt(np.mean(np.square(window), dtype=np.float64)))
                    window_db = dbfs(rms)
                    is_silent = window_db is None or window_db < silence_threshold_dbfs
                    start = frame_cursor / info.samplerate
                    end = (frame_cursor + len(window)) / info.samplerate
                    if is_silent:
                        silent_frames += len(window)
                        if active_silence_start is None:
                            active_silence_start = start
                    elif active_silence_start is not None:
                        if end - active_silence_start >= 0.2:
                            silence_regions.append({
                                "start_seconds": round(active_silence_start, 3),
                                "end_seconds": round(start, 3),
                                "duration_seconds": round(start - active_silence_start, 3),
                            })
                        active_silence_start = None
                    frame_cursor += len(window)

        if pending.size:
            rms = float(np.sqrt(np.mean(np.square(pending), dtype=np.float64)))
            window_db = dbfs(rms)
            start = frame_cursor / info.samplerate
            end = (frame_cursor + len(pending)) / info.samplerate
            is_silent = window_db is None or window_db < silence_threshold_dbfs
            if is_silent:
                silent_frames += len(pending)
                if active_silence_start is None:
                    active_silence_start = start
            elif active_silence_start is not None:
                if end - active_silence_start >= 0.2:
                    silence_regions.append({
                        "start_seconds": round(active_silence_start, 3),
                        "end_seconds": round(start, 3),
                        "duration_seconds": round(start - active_silence_start, 3),
                    })

        overall_rms = math.sqrt(sum_squares / sample_count) if sample_count else 0.0
        peak_db = dbfs(peak)
        rms_db = dbfs(overall_rms)
        duration = float(info.duration)

        result.update({
            "duration_seconds": round(duration, 3),
            "sample_rate_hz": int(info.samplerate),
            "channels": int(info.channels),
            "format": str(info.format),
            "subtype": str(info.subtype),
            "bit_depth": {
                "PCM_U8": 8, "PCM_16": 16, "PCM_24": 24,
                "PCM_32": 32, "FLOAT": 32, "DOUBLE": 64,
            }.get(str(info.subtype)),
            "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "sample_peak_dbfs": peak_db,
            "rms_dbfs": rms_db,
            "clipped_samples_at_or_above_minus_0_01_dbfs": clipped_samples,
            "near_silence_threshold_dbfs": silence_threshold_dbfs,
            "near_silence_percent": round((silent_frames / info.frames) * 100, 2),
            "near_silence_regions_200ms_or_longer": silence_regions,
            "ebu_r128": ffmpeg_loudness(path),
            "warnings": [],
        })

        if clipped_samples:
            result["warnings"].append(
                f"{clipped_samples} samples are at or above -0.01 dBFS; inspect for clipping."
            )
        if peak_db is not None and peak_db > -0.1:
            result["warnings"].append("Sample peak is very close to 0 dBFS.")
        if info.channels == 1:
            result["warnings"].append("This final export is mono, not stereo.")
        if info.subtype != "PCM_24":
            result["warnings"].append(
                f"Subtype is {info.subtype}; intended delivery target is PCM_24 if a 24-bit master is needed."
            )
        if info.samplerate != 44_100:
            result["warnings"].append(
                f"Sample rate is {info.samplerate} Hz; project reference is 44100 Hz."
            )

    except Exception as exc:
        result.update(status="ERROR", error=f"{type(exc).__name__}: {exc}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the final sound-designed Hindi and English WAV exports."
    )
    parser.add_argument("--hindi", type=Path, help="Path to the final Hindi WAV mix.")
    parser.add_argument("--english", type=Path, help="Path to the final English WAV mix.")
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1],
        help="Project root (used for default file paths and report output)."
    )
    parser.add_argument(
        "--silence-threshold", type=float, default=-55.0,
        help="RMS threshold in dBFS for near-silence windows (default: -55)."
    )
    args = parser.parse_args()

    project_root = args.root.expanduser().resolve()
    default_dir = project_root / "output" / "final_mixes"
    hindi_path = (args.hindi or (default_dir / "hindi_final_mix.wav")).expanduser().resolve()
    english_path = (args.english or (default_dir / "english_final_mix.wav")).expanduser().resolve()

    print("\nStorySound AI — Final Mix Audio Analyzer")
    print("=" * 78)
    print(f"Hindi WAV   : {hindi_path}")
    print(f"English WAV : {english_path}")
    print("Mode        : Read-only technical analysis; original audio will not be changed.")
    print("API usage   : None — no ElevenLabs request or credits used.\n")

    results = [
        analyze_wav("Hindi", hindi_path, args.silence_threshold),
        analyze_wav("English", english_path, args.silence_threshold),
    ]

    for result in results:
        print(f"{result['label'].upper():<8} {result['status']}")
        if result["status"] == "ERROR":
            print(f"         {result['error']}")
            print()
            continue

        print(
            f"         Duration: {result['duration_seconds'] / 60:.2f} min | "
            f"{result['sample_rate_hz']} Hz | {result['channels']} channel(s) | "
            f"{result['subtype']} | {result['file_size_mb']:.2f} MB"
        )
        print(
            f"         Sample peak: {result['sample_peak_dbfs']} dBFS | "
            f"RMS: {result['rms_dbfs']} dBFS | "
            f"Clipped samples: {result['clipped_samples_at_or_above_minus_0_01_dbfs']}"
        )
        r128 = result.get("ebu_r128")
        if r128 is None:
            print("         EBU R128: unavailable (install FFmpeg to measure LUFS/LRA/true peak)")
        elif "integrated_lufs" in r128:
            print(
                f"         Integrated loudness: {r128['integrated_lufs']} LUFS | "
                f"LRA: {r128['loudness_range_lu']} LU | "
                f"True peak: {r128['true_peak_dbtp']} dBTP"
            )
        else:
            print(f"         EBU R128: {r128.get('error', 'measurement unavailable')}")
        print(
            f"         Near-silence: {result['near_silence_percent']}% | "
            f"Regions >= 0.2 sec: {len(result['near_silence_regions_200ms_or_longer'])}"
        )
        for warning in result.get("warnings", []):
            print(f"         WARNING: {warning}")
        print()

    report_dir = project_root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "final_mix_audio_audit.json"
    summary = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "project_root": str(project_root),
        "read_only": True,
        "api_used": False,
        "files": results,
    }
    report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    csv_path = report_dir / "final_mix_audio_audit.csv"
    columns = [
        "label", "status", "duration_seconds", "sample_rate_hz", "channels",
        "subtype", "file_size_mb", "sample_peak_dbfs", "rms_dbfs",
        "clipped_samples_at_or_above_minus_0_01_dbfs", "near_silence_percent", "file",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in results:
            writer.writerow({key: row.get(key, "") for key in columns})

    overall = "PASS" if all(row.get("status") == "PASS" for row in results) else "CHECK"
    print("=" * 78)
    print(f"Overall status : {overall}")
    print(f"JSON report    : {report_path}")
    print(f"CSV report     : {csv_path}")
    print("No audio was modified. No ElevenLabs API credits were used.")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
