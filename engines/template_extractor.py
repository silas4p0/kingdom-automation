import math
from typing import Any

from .alignment_engine import (
    AlignmentEngine, AlignmentResult, AlignedWord, _read_wav_samples,
    _compute_energy_envelope, _fast_analyze,
)
from .dsp_analyzer import DSPAnalysisResult, TokenParameterMapper
from models.reference_template import ReferenceTemplate


class TemplateExtractor:
    def __init__(self) -> None:
        self._alignment = AlignmentEngine()
        self._mapper = TokenParameterMapper()

    def extract(
        self,
        audio_path: str,
        words: list[str],
        name: str = "",
        reference_mode: str = "Master Mix",
        emotional_tone: str = "reverent",
    ) -> ReferenceTemplate:
        tpl = ReferenceTemplate(name or "Untitled Template")
        tpl.source_audio = audio_path
        tpl.reference_mode = reference_mode
        tpl.emotional_tone = emotional_tone

        samples, sr = _read_wav_samples(audio_path)
        if not samples:
            return tpl

        tpl.word_count = len(words)
        tpl.tempo_estimate = self._estimate_tempo(samples, sr)

        lines = self._split_into_lines(words)
        tpl.line_count = len(lines)
        tpl.phrase_count = max(1, len(lines) // 2)

        alignment = self._alignment.forced_align(audio_path, words)
        if not alignment.words:
            return tpl

        durations = [w.duration_ms for w in alignment.words]
        tpl.duration_distribution = self._compute_distribution(durations)

        analyses = self._analyze_segments(samples, sr, alignment)

        self._fill_loudness(tpl, analyses)
        self._fill_pitch(tpl, analyses)
        self._fill_vibrato(tpl, analyses)
        self._fill_delivery(tpl, analyses)
        self._fill_intensity(tpl, analyses)
        self._compute_token_defaults(tpl)

        return tpl

    def _estimate_tempo(self, samples: list[float], sr: int) -> float:
        envelope = _compute_energy_envelope(samples, sr, hop_ms=10.0)
        if len(envelope) < 20:
            return 120.0
        mean_e = sum(envelope) / len(envelope)
        crossings = 0
        above = envelope[0] > mean_e
        for val in envelope[1:]:
            now_above = val > mean_e
            if now_above != above:
                crossings += 1
                above = now_above
        duration_s = len(samples) / sr
        if duration_s <= 0:
            return 120.0
        beats_estimate = crossings / 2.0
        bpm = (beats_estimate / duration_s) * 60.0
        bpm = max(40.0, min(240.0, bpm))
        return round(bpm, 1)

    def _split_into_lines(self, words: list[str]) -> list[list[str]]:
        lines: list[list[str]] = []
        current: list[str] = []
        for w in words:
            current.append(w)
            if len(current) >= 8:
                lines.append(current)
                current = []
        if current:
            lines.append(current)
        return lines

    def _analyze_segments(
        self, samples: list[float], sr: int, alignment: AlignmentResult,
    ) -> list[DSPAnalysisResult]:
        results: list[DSPAnalysisResult] = []
        for word in alignment.words:
            start_idx = int(word.start_ms * sr / 1000.0)
            end_idx = int(word.end_ms * sr / 1000.0)
            start_idx = max(0, min(start_idx, len(samples)))
            end_idx = max(start_idx, min(end_idx, len(samples)))
            segment = samples[start_idx:end_idx]
            if len(segment) < 64:
                results.append(DSPAnalysisResult())
            else:
                results.append(_fast_analyze(segment, sr))
        return results

    def _compute_distribution(self, values: list[float]) -> dict[str, float]:
        if not values:
            return {"mean_ms": 500.0, "std_ms": 100.0, "min_ms": 100.0, "max_ms": 2000.0}
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / max(len(values), 1)
        std = math.sqrt(variance)
        return {
            "mean_ms": round(mean, 1),
            "std_ms": round(std, 1),
            "min_ms": round(min(values), 1),
            "max_ms": round(max(values), 1),
        }

    def _fill_loudness(self, tpl: ReferenceTemplate,
                       analyses: list[DSPAnalysisResult]) -> None:
        rms_vals = [a.rms_loudness for a in analyses if a.rms_loudness > 0]
        if not rms_vals:
            return
        mean_rms = sum(rms_vals) / len(rms_vals)
        peak_rms = max(rms_vals)
        min_rms = min(rms_vals)
        dynamic_db = 20.0 * math.log10(peak_rms / max(min_rms, 1e-6)) if min_rms > 0 else 0.0
        tpl.loudness_envelope = {
            "mean_rms": round(mean_rms, 6),
            "peak_rms": round(peak_rms, 6),
            "dynamic_range_db": round(dynamic_db, 1),
        }

    def _fill_pitch(self, tpl: ReferenceTemplate,
                    analyses: list[DSPAnalysisResult]) -> None:
        pitches_hz = [a.pitch_hz for a in analyses if a.pitch_hz > 20]
        if not pitches_hz:
            return
        ref = 261.63
        semitones = [12.0 * math.log2(p / ref) for p in pitches_hz]
        median_hz = sorted(pitches_hz)[len(pitches_hz) // 2]
        mean_st = sum(semitones) / len(semitones)
        var_st = sum((s - mean_st) ** 2 for s in semitones) / len(semitones)
        std_st = math.sqrt(var_st)
        range_st = max(semitones) - min(semitones)
        tpl.pitch_contour = {
            "median_hz": round(median_hz, 2),
            "mean_st": round(mean_st, 2),
            "std_st": round(std_st, 2),
            "range_st": round(range_st, 2),
        }

    def _fill_vibrato(self, tpl: ReferenceTemplate,
                      analyses: list[DSPAnalysisResult]) -> None:
        rates = [a.vibrato_rate_hz for a in analyses if a.vibrato_rate_hz > 0]
        depths = [a.vibrato_depth_cents for a in analyses if a.vibrato_depth_cents > 0]
        total = len(analyses) if analyses else 1
        presence = len(rates) / total
        tpl.vibrato_behavior = {
            "mean_rate_hz": round(sum(rates) / len(rates), 2) if rates else 0.0,
            "mean_depth_cents": round(sum(depths) / len(depths), 2) if depths else 0.0,
            "presence_ratio": round(presence, 3),
        }

    def _fill_delivery(self, tpl: ReferenceTemplate,
                       analyses: list[DSPAnalysisResult]) -> None:
        counts: dict[str, int] = {
            "Whisper": 0, "Normal": 0, "Yell": 0, "Scream": 0, "Bravado": 0,
        }
        for a in analyses:
            params = self._mapper.map_to_params(a)
            d = params.get("delivery", "Normal")
            if d in counts:
                counts[d] += 1
        total = max(sum(counts.values()), 1)
        tpl.delivery_tendencies = {k: round(v / total, 3) for k, v in counts.items()}

    def _fill_intensity(self, tpl: ReferenceTemplate,
                        analyses: list[DSPAnalysisResult]) -> None:
        intensities: list[float] = []
        for a in analyses:
            params = self._mapper.map_to_params(a)
            intensities.append(float(params.get("intensity", 50)))
        if not intensities:
            return
        mean = sum(intensities) / len(intensities)
        var = sum((v - mean) ** 2 for v in intensities) / len(intensities)
        std = math.sqrt(var)
        tpl.intensity_distribution = {
            "mean": round(mean, 1),
            "std": round(std, 1),
            "min": round(min(intensities), 1),
            "max": round(max(intensities), 1),
        }

    def _compute_token_defaults(self, tpl: ReferenceTemplate) -> None:
        dur = tpl.duration_distribution.get("mean_ms", 500.0)
        loud_rms = tpl.loudness_envelope.get("mean_rms", 0.0)
        loud_pct = int(min(200, max(0, ((20.0 * math.log10(max(loud_rms, 1e-6)) + 60.0) / 60.0) * 200.0)))
        intensity = int(tpl.intensity_distribution.get("mean", 50.0))
        pitch_st = tpl.pitch_contour.get("mean_st", 0.0)
        pitch_offset = int(max(-24, min(24, round(pitch_st))))
        best_delivery = "Normal"
        best_ratio = 0.0
        for d, ratio in tpl.delivery_tendencies.items():
            if ratio > best_ratio:
                best_ratio = ratio
                best_delivery = d
        tpl.token_defaults = {
            "duration_ms": int(max(50, min(2000, dur))),
            "loudness_pct": loud_pct,
            "intensity": intensity,
            "pitch_offset": pitch_offset,
            "delivery": best_delivery,
        }
