import json
import os
import shutil
import time
from typing import Any

from .alignment_engine import AlignmentResult, _read_wav_samples
from .audio_synth import _write_wav


class TrainingPackExporter:
    def export(
        self,
        output_dir: str,
        vocal_path: str,
        alignment: AlignmentResult | None,
        performance_script: dict[str, Any],
        reference_template: dict[str, Any] | None,
        performer_name: str = "",
        notes: str = "",
        segmentation: str = "none",
    ) -> dict[str, Any]:
        os.makedirs(output_dir, exist_ok=True)

        manifest: dict[str, Any] = {
            "format_version": 1,
            "created_at": time.time(),
            "files": [],
        }

        if vocal_path and os.path.isfile(vocal_path):
            dest = os.path.join(output_dir, "vocals.wav")
            shutil.copy2(vocal_path, dest)
            manifest["files"].append("vocals.wav")

        if alignment and segmentation != "none":
            seg_dir = os.path.join(output_dir, "segments")
            os.makedirs(seg_dir, exist_ok=True)
            seg_files = self._segment_audio(
                vocal_path, alignment, seg_dir, segmentation,
            )
            manifest["files"].extend(seg_files)
            manifest["segmentation"] = segmentation

        if alignment:
            align_path = os.path.join(output_dir, "alignment.json")
            with open(align_path, "w", encoding="utf-8") as f:
                json.dump(alignment.to_dict(), f, indent=2)
            manifest["files"].append("alignment.json")

        script_path = os.path.join(output_dir, "performance_script.json")
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(performance_script, f, indent=2)
        manifest["files"].append("performance_script.json")

        if reference_template:
            tpl_path = os.path.join(output_dir, "reference_template.json")
            with open(tpl_path, "w", encoding="utf-8") as f:
                json.dump(reference_template, f, indent=2)
            manifest["files"].append("reference_template.json")

        samples, sr = ([], 44100)
        if vocal_path and os.path.isfile(vocal_path):
            samples, sr = _read_wav_samples(vocal_path)
        metadata: dict[str, Any] = {
            "format_version": 1,
            "sample_rate": sr,
            "performer_name": performer_name,
            "notes": notes,
            "created_at": time.time(),
            "audio_duration_s": round(len(samples) / sr, 2) if samples else 0.0,
            "word_count": len(alignment.words) if alignment else 0,
            "segmentation": segmentation,
        }
        meta_path = os.path.join(output_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        manifest["files"].append("metadata.json")

        manifest["file_count"] = len(manifest["files"])
        manifest_path = os.path.join(output_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return manifest

    def _segment_audio(
        self,
        audio_path: str,
        alignment: AlignmentResult,
        seg_dir: str,
        mode: str,
    ) -> list[str]:
        if not audio_path or not os.path.isfile(audio_path):
            return []
        samples, sr = _read_wav_samples(audio_path)
        if not samples:
            return []

        segments: list[tuple[str, float, float]] = []
        if mode == "line":
            segments = self._group_by_line(alignment)
        elif mode == "phrase":
            segments = self._group_by_phrase(alignment)
        else:
            return []

        files: list[str] = []
        for i, (label, start_ms, end_ms) in enumerate(segments):
            start_idx = max(0, int(start_ms * sr / 1000.0))
            end_idx = min(len(samples), int(end_ms * sr / 1000.0))
            seg_samples = samples[start_idx:end_idx]
            if not seg_samples:
                continue
            fname = f"{i:03d}_{label}.wav"
            wav_data = _write_wav(seg_samples, sr)
            with open(os.path.join(seg_dir, fname), "wb") as f:
                f.write(wav_data)
            files.append(f"segments/{fname}")
        return files

    def _group_by_line(
        self, alignment: AlignmentResult,
    ) -> list[tuple[str, float, float]]:
        if not alignment.words:
            return []
        lines: list[tuple[str, float, float]] = []
        line_words: list[str] = []
        line_start = alignment.words[0].start_ms
        for w in alignment.words:
            line_words.append(w.word)
            if len(line_words) >= 8:
                label = "_".join(line_words[:3])
                lines.append((label, line_start, w.end_ms))
                line_words = []
                line_start = w.end_ms
        if line_words:
            label = "_".join(line_words[:3])
            lines.append((label, line_start, alignment.words[-1].end_ms))
        return lines

    def _group_by_phrase(
        self, alignment: AlignmentResult,
    ) -> list[tuple[str, float, float]]:
        if not alignment.words:
            return []
        phrases: list[tuple[str, float, float]] = []
        phrase_words: list[str] = []
        phrase_start = alignment.words[0].start_ms
        prev_end = alignment.words[0].start_ms
        gap_threshold_ms = 300.0
        for w in alignment.words:
            gap = w.start_ms - prev_end
            if gap > gap_threshold_ms and phrase_words:
                label = "_".join(phrase_words[:3])
                phrases.append((label, phrase_start, prev_end))
                phrase_words = []
                phrase_start = w.start_ms
            phrase_words.append(w.word)
            prev_end = w.end_ms
        if phrase_words:
            label = "_".join(phrase_words[:3])
            phrases.append((label, phrase_start, prev_end))
        return phrases
