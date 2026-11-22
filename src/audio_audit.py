"""Audit the Hindi and English WAV exports for the StorySound AI project.

This script works locally with soundfile and NumPy. It does not call ElevenLabs
or use any API credits.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import numpy as np
    import soundfile as sf
except ImportError as exc:
    missing = "numpy" if "numpy" in str(exc) else "soundfile"
    raise SystemExit(
        f"Missing package: {missing}. Install project dependencies with: "
        "python -m pip install -r requirements.txt"
    ) from exc


LANGUAGES = ("hindi", "english")
EXPECTED_SCENES = 5
BLOCK_SIZE = 65_536

BIT_DEPTHS = {
    "PCM_U8": 8,
    "PCM_16": 16,
    "PCM_24": 24,
    "PCM_32": 32,
    "FLOAT": 32,
    "DOUBLE": 64,
}


def to_dbfs(value: float) -> float | None:
    """Convert linear amplitude to dBFS. Digital silence returns None."""
    if value <= 0:
        return None
    return round(20.0 * math.log10(value), 2)


def inspect_wav(path: Path, language: str) -> dict[str, Any]:
    """Read metadata and decode the WAV in chunks to confirm it is readable."""
    result: dict[str, Any] = {
        "language": language,
        "file_name": path.name,
        "file_path": str(path),
        "status": "PASS",
        "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2),
        "duration_seconds": None,
        "sample_rate_hz": None,
        "channels": None,
        "format": None,
        "subtype": None,
        "bit_depth": None,
        "peak_dbfs": None,
        "rms_dbfs": None,
        "near_full_scale_samples": 0,
        "warnings": [],
        "error": "",
    }

    try:
        info = sf.info(str(path))
        if info.frames <= 0 or info.samplerate <= 0 or info.channels <= 0:
            raise ValueError("WAV header has invalid frame, sample-rate, or channel values")

        result.update(
            {
                "duration_seconds": round(float(info.duration), 2),
                "sample_rate_hz": int(info.samplerate),
                "channels": int(info.channels),
                "format": str(info.format),
                "subtype": str(info.subtype),
                "bit_depth": BIT_DEPTHS.get(str(info.subtype)),
            }
        )

        # Decode the complete file in small blocks instead of loading a long
        # recording into memory all at once.
        sample_count = 0
        sum_squares = 0.0
        peak = 0.0
        near_full_scale = 0

        with sf.SoundFile(str(path), mode="r") as audio_file:
            while True:
                samples = audio_file.read(
                    frames=BLOCK_SIZE,
                    dtype="float32",
                    always_2d=True,
                )
                if samples.size == 0:
                    break

                absolute = np.abs(samples)
                sample_count += int(samples.size)
                sum_squares += float(np.sum(np.square(samples), dtype=np.float64))
                peak = max(peak, float(np.max(absolute)))
                near_full_scale += int(np.count_nonzero(absolute >= 0.999))

        if sample_count == 0:
            raise ValueError("WAV contains no decodable audio samples")

        rms = math.sqrt(sum_squares / sample_count)
        result["peak_dbfs"] = to_dbfs(peak)
        result["rms_dbfs"] = to_dbfs(rms)
        result["near_full_scale_samples"] = near_full_scale

        # Reference settings are checks for consistency, not hard failures.
        if info.samplerate != 44_100:
            result["warnings"].append(
                f"Sample rate is {info.samplerate} Hz (reference: 44100 Hz)"
            )
        if info.channels != 1:
            result["warnings"].append(
                f"Audio has {info.channels} channels (reference: mono)"
            )
        if info.subtype != "PCM_16":
            result["warnings"].append(
                f"Subtype is {info.subtype} (reference: PCM_16)"
            )
        if near_full_scale:
            result["warnings"].append(
                f"{near_full_scale} samples are at or above -0.01 dBFS; check for clipping"
            )

    except Exception as exc:
        result["status"] = "ERROR"
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "language", "file_name", "status", "duration_seconds",
        "sample_rate_hz", "channels", "format", "subtype", "bit_depth",
        "file_size_mb", "peak_dbfs", "rms_dbfs", "near_full_scale_samples",
        "warnings", "error", "file_path",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            export_row = dict(row)
            export_row["warnings"] = " | ".join(row["warnings"])
            writer.writerow(export_row)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the Hindi and English StorySound AI WAV exports."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root folder (default: detected from this script's location).",
    )
    args = parser.parse_args()

    project_root = args.root.expanduser().resolve()
    audio_root = project_root / "assets" / "raw_audio"
    reports_root = project_root / "reports"
    reports_root.mkdir(parents=True, exist_ok=True)

    print("\nStorySound AI — Audio Audit")
    print("=" * 78)
    print(f"Project root : {project_root}")
    print(f"Audio folder : {audio_root}")
    print("API usage    : None — local file inspection only\n")

    all_rows: list[dict[str, Any]] = []
    language_summary: dict[str, Any] = {}
    directory_issues: list[str] = []

    for language in LANGUAGES:
        language_dir = audio_root / language
        if not language_dir.is_dir():
            directory_issues.append(f"Missing folder: {language_dir}")
            language_summary[language] = {
                "file_count": 0,
                "expected_files": EXPECTED_SCENES,
                "total_duration_seconds": 0,
                "total_size_mb": 0,
                "status": "MISSING_FOLDER",
            }
            continue

        wav_files = sorted(
            (
                item for item in language_dir.iterdir()
                if item.is_file() and item.suffix.lower() == ".wav"
            ),
            key=lambda item: item.name.casefold(),
        )
        language_rows = [inspect_wav(path, language) for path in wav_files]
        all_rows.extend(language_rows)

        valid_rows = [row for row in language_rows if row["status"] == "PASS"]
        total_duration = sum(row["duration_seconds"] or 0 for row in valid_rows)
        total_size = sum(row["file_size_mb"] for row in language_rows)
        language_status = "PASS" if len(valid_rows) == len(wav_files) else "CHECK_ERRORS"
        if len(wav_files) != EXPECTED_SCENES:
            language_status = "CHECK_FILE_COUNT"

        language_summary[language] = {
            "file_count": len(wav_files),
            "expected_files": EXPECTED_SCENES,
            "readable_files": len(valid_rows),
            "total_duration_seconds": round(total_duration, 2),
            "total_size_mb": round(total_size, 2),
            "status": language_status,
        }

        print(
            f"{language.upper():<8}  {len(wav_files)} WAV file(s) | "
            f"{total_duration / 60:.2f} min total | {total_size:.2f} MB | "
            f"{language_status}"
        )
        for row in language_rows:
            duration = row["duration_seconds"]
            duration_text = f"{duration:.2f}s" if duration is not None else "n/a"
            print(
                f"  [{row['status']:<5}] {row['file_name']} — {duration_text}, "
                f"{row['sample_rate_hz'] or 'n/a'} Hz, "
                f"{row['channels'] or 'n/a'} ch, {row['subtype'] or 'n/a'}"
            )
            for warning in row["warnings"]:
                print(f"         WARNING: {warning}")
            if row["error"]:
                print(f"         ERROR: {row['error']}")

        if len(wav_files) != EXPECTED_SCENES:
            print(
                f"  WARNING: expected {EXPECTED_SCENES} scene WAV files, "
                f"found {len(wav_files)}"
            )
        print()

    csv_path = reports_root / "audio_audit_report.csv"
    json_path = reports_root / "audio_audit_summary.json"
    write_csv(csv_path, all_rows)

    error_count = sum(row["status"] == "ERROR" for row in all_rows)
    overall = "PASS" if not error_count and not directory_issues else "CHECK"
    summary = {
        "project_root": str(project_root),
        "audio_root": str(audio_root),
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "expected_scene_files_per_language": EXPECTED_SCENES,
        "overall_status": overall,
        "directory_issues": directory_issues,
        "languages": language_summary,
        "files": all_rows,
    }
    json_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 78)
    print(f"Overall status : {overall}")
    print(f"CSV report     : {csv_path}")
    print(f"JSON summary   : {json_path}")
    print("\nNo ElevenLabs API request was made and no credits were used.")

    return 1 if error_count or directory_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
