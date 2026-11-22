"""Build one continuous WAV master per language from scene-level WAV files.

This is a local-only operation. It does not call ElevenLabs or consume credits.
It preserves the original raw WAV files and does not normalize or add effects.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

LANGUAGES = {
    "hindi": "hindi_story_master.wav",
    "english": "english_story_master.wav",
}
EXPECTED_SCENES = 5
BLOCK_FRAMES = 131_072


def append_silence(output_file: sf.SoundFile, frames: int, channels: int) -> None:
    """Write digital silence in manageable blocks."""
    remaining = frames
    while remaining > 0:
        block = min(remaining, BLOCK_FRAMES)
        output_file.write(np.zeros((block, channels), dtype=np.float32))
        remaining -= block


def build_language_master(
    project_root: Path,
    language: str,
    output_name: str,
    gap_seconds: float,
) -> dict[str, Any]:
    input_dir = project_root / "assets" / "raw_audio" / language
    output_dir = project_root / "output" / language
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name

    if not input_dir.is_dir():
        raise FileNotFoundError(f"Audio folder not found: {input_dir}")

    wav_files = sorted(
        (path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() == ".wav"),
        key=lambda path: path.name.casefold(),
    )
    if len(wav_files) != EXPECTED_SCENES:
        raise ValueError(
            f"{language}: expected {EXPECTED_SCENES} scene WAV files in {input_dir}, "
            f"found {len(wav_files)}"
        )

    infos = [sf.info(str(path)) for path in wav_files]
    sample_rates = {info.samplerate for info in infos}
    channel_counts = {info.channels for info in infos}
    if len(sample_rates) != 1 or len(channel_counts) != 1:
        details = "; ".join(
            f"{path.name}: {info.samplerate} Hz, {info.channels} channel(s)"
            for path, info in zip(wav_files, infos)
        )
        raise ValueError(
            f"{language}: input WAV files do not share one sample rate/channel layout. "
            f"No automatic resampling or channel conversion is applied. {details}"
        )

    sample_rate = infos[0].samplerate
    channels = infos[0].channels
    gap_frames = round(gap_seconds * sample_rate)
    timeline: list[dict[str, Any]] = []
    cursor_frames = 0

    with sf.SoundFile(
        str(output_path),
        mode="w",
        samplerate=sample_rate,
        channels=channels,
        format="WAV",
        subtype="PCM_16",
    ) as output_file:
        for index, (path, info) in enumerate(zip(wav_files, infos)):
            start_seconds = cursor_frames / sample_rate
            frames_written = 0

            # Stream each source WAV rather than loading the entire story into memory.
            with sf.SoundFile(str(path), mode="r") as input_file:
                while True:
                    audio_block = input_file.read(
                        frames=BLOCK_FRAMES,
                        dtype="float32",
                        always_2d=True,
                    )
                    if audio_block.size == 0:
                        break
                    output_file.write(audio_block)
                    frames_written += len(audio_block)

            cursor_frames += frames_written
            end_seconds = cursor_frames / sample_rate
            timeline.append(
                {
                    "scene_number": index + 1,
                    "source_file": path.name,
                    "start_seconds": round(start_seconds, 3),
                    "end_seconds": round(end_seconds, 3),
                    "duration_seconds": round(frames_written / sample_rate, 3),
                }
            )

            if index < len(wav_files) - 1 and gap_frames > 0:
                append_silence(output_file, gap_frames, channels)
                cursor_frames += gap_frames

    final_info = sf.info(str(output_path))
    return {
        "language": language,
        "input_directory": str(input_dir),
        "output_file": str(output_path),
        "scene_count": len(wav_files),
        "sample_rate_hz": sample_rate,
        "channels": channels,
        "subtype": final_info.subtype,
        "gap_seconds_between_scenes": gap_seconds,
        "duration_seconds": round(final_info.duration, 3),
        "file_size_mb": round(output_path.stat().st_size / (1024 * 1024), 2),
        "timeline": timeline,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Join the five scene WAV files into a Hindi and English story master."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root (default: detected from this script's location).",
    )
    parser.add_argument(
        "--gap-seconds",
        type=float,
        default=1.5,
        help="Silence between scenes in seconds (default: 1.5).",
    )
    args = parser.parse_args()

    if args.gap_seconds < 0:
        parser.error("--gap-seconds cannot be negative")

    project_root = args.root.expanduser().resolve()
    reports_dir = project_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    print("\nStorySound AI — Story Master Builder")
    print("=" * 78)
    print(f"Project root : {project_root}")
    print(f"Scene gap    : {args.gap_seconds:.2f} seconds")
    print("API usage    : None — local WAV assembly only\n")

    results: list[dict[str, Any]] = []
    try:
        for language, output_name in LANGUAGES.items():
            result = build_language_master(project_root, language, output_name, args.gap_seconds)
            results.append(result)
            minutes, seconds = divmod(int(round(result["duration_seconds"])), 60)
            print(
                f"{language.upper():<8} PASS — {result['scene_count']} scenes | "
                f"{minutes}:{seconds:02d} | {result['sample_rate_hz']} Hz | "
                f"{result['channels']} channel(s) | {result['file_size_mb']:.2f} MB"
            )
            print(f"         Output: {result['output_file']}")
            for scene in result["timeline"]:
                print(
                    f"         Scene {scene['scene_number']}: "
                    f"{scene['start_seconds']:.2f}s–{scene['end_seconds']:.2f}s "
                    f"({scene['duration_seconds']:.2f}s)"
                )
            print()
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    manifest_path = reports_dir / "story_master_manifest.json"
    manifest = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "project_root": str(project_root),
        "gap_seconds_between_scenes": args.gap_seconds,
        "processing": "Scene WAV files concatenated in filename order; silence inserted between scenes.",
        "normalization_applied": False,
        "effects_applied": False,
        "elevenlabs_api_used": False,
        "masters": results,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 78)
    print("PASS — both language masters were created.")
    print(f"Manifest : {manifest_path}")
    print("Raw source WAV files were not modified.")
    print("No normalization, music, SFX, API calls, or ElevenLabs credits were used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
