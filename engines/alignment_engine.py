import math
import struct
from typing import Any

from .dsp_analyzer import DSPAnalyzer, DSPAnalysisResult


class AlignedWord:
    def __init__(self, word: str, start_ms: float, end_ms: float,
                 confidence: float = 1.0) -> None:
        self.word: str = word
        self.start_ms: float = start_ms
        self.end_ms: float = end_ms
        self.confidence: float = confidence

    @property
    def duration_ms(self) -> float:
        return self.end_ms - self.start_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "word": self.word,
            "start_ms": round(self.start_ms, 1),
            "end_ms": round(self.end_ms, 1),
            "duration_ms": round(self.duration_ms, 1),
            "confidence": round(self.confidence, 3),
        }


class AlignmentResult:
    def __init__(self) -> None:
        self.words: list[AlignedWord] = []
        self.audio_duration_ms: float = 0.0
        self.sample_rate: int = 44100
        self.method: str = "energy_forced"

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "audio_duration_ms": round(self.audio_duration_ms, 1),
            "sample_rate": self.sample_rate,
            "word_count": len(self.words),
            "words": [w.to_dict() for w in self.words],
        }


def _read_wav_samples(path: str) -> tuple[list[float], int]:
    with open(path, "rb") as f:
        riff = f.read(4)
        if riff != b"RIFF":
            return [], 44100
        f.read(4)
        wave = f.read(4)
        if wave != b"WAVE":
            return [], 44100
        sr = 44100
        channels = 1
        bits = 16
        raw = b""
        while True:
            chunk_id = f.read(4)
            if len(chunk_id) < 4:
                break
            chunk_size = struct.unpack("<I", f.read(4))[0]
            if chunk_id == b"fmt ":
                fmt_data = f.read(chunk_size)
                channels = struct.unpack("<H", fmt_data[2:4])[0]
                sr = struct.unpack("<I", fmt_data[4:8])[0]
                bits = struct.unpack("<H", fmt_data[14:16])[0]
            elif chunk_id == b"data":
                raw = f.read(chunk_size)
                break
            else:
                f.read(chunk_size)
        if not raw:
            return [], sr
        samples: list[float] = []
        bytes_per = bits // 8
        frame_size = bytes_per * channels
        num_frames = len(raw) // frame_size
        for i in range(num_frames):
            offset = i * frame_size
            if bits == 16:
                val = struct.unpack_from("<h", raw, offset)[0]
                samples.append(val / 32768.0)
            elif bits == 8:
                samples.append((raw[offset] - 128) / 128.0)
            else:
                val = struct.unpack_from("<h", raw, offset)[0]
                samples.append(val / 32768.0)
        return samples, sr


def _compute_energy_envelope(samples: list[float], sr: int,
                             hop_ms: float = 10.0) -> list[float]:
    hop = max(1, int(sr * hop_ms / 1000.0))
    envelope: list[float] = []
    for start in range(0, len(samples), hop):
        chunk = samples[start:start + hop]
        rms = math.sqrt(sum(s * s for s in chunk) / max(len(chunk), 1))
        envelope.append(rms)
    return envelope


def _find_energy_boundaries(envelope: list[float],
                            threshold_ratio: float = 0.15) -> list[tuple[int, int]]:
    if not envelope:
        return []
    peak = max(envelope)
    if peak < 1e-6:
        return []
    threshold = peak * threshold_ratio
    regions: list[tuple[int, int]] = []
    in_region = False
    start = 0
    for i, val in enumerate(envelope):
        if val >= threshold and not in_region:
            in_region = True
            start = i
        elif val < threshold and in_region:
            in_region = False
            regions.append((start, i))
    if in_region:
        regions.append((start, len(envelope)))
    merged: list[tuple[int, int]] = []
    for reg in regions:
        if merged and reg[0] - merged[-1][1] <= 3:
            merged[-1] = (merged[-1][0], reg[1])
        else:
            merged.append(reg)
    return merged


class AlignmentEngine:
    def __init__(self) -> None:
        self._dsp = DSPAnalyzer()

    def forced_align(self, audio_path: str,
                     words: list[str]) -> AlignmentResult:
        samples, sr = _read_wav_samples(audio_path)
        result = AlignmentResult()
        result.sample_rate = sr
        if not samples:
            return result
        result.audio_duration_ms = (len(samples) / sr) * 1000.0
        if not words:
            return result
        hop_ms = 10.0
        envelope = _compute_energy_envelope(samples, sr, hop_ms)
        regions = _find_energy_boundaries(envelope)
        if regions:
            result.words = self._align_words_to_regions(
                words, regions, hop_ms, result.audio_duration_ms
            )
        else:
            result.words = self._uniform_align(words, result.audio_duration_ms)
        result.method = "energy_forced"
        return result

    def _align_words_to_regions(
        self, words: list[str], regions: list[tuple[int, int]],
        hop_ms: float, total_ms: float,
    ) -> list[AlignedWord]:
        aligned: list[AlignedWord] = []
        n_words = len(words)
        n_regions = len(regions)
        if n_regions >= n_words:
            for i, word in enumerate(words):
                reg = regions[i]
                start = reg[0] * hop_ms
                end = reg[1] * hop_ms
                conf = 0.8 if i < n_regions else 0.5
                aligned.append(AlignedWord(word, start, end, conf))
        else:
            words_per_region = n_words / n_regions
            idx = 0.0
            for i, word in enumerate(words):
                reg_idx = min(int(idx), n_regions - 1)
                reg = regions[reg_idx]
                reg_start = reg[0] * hop_ms
                reg_end = reg[1] * hop_ms
                reg_dur = reg_end - reg_start
                local_count = max(1, round(words_per_region))
                local_idx = i - int(reg_idx * words_per_region)
                local_idx = max(0, min(local_idx, local_count - 1))
                w_start = reg_start + (local_idx / local_count) * reg_dur
                w_end = reg_start + ((local_idx + 1) / local_count) * reg_dur
                aligned.append(AlignedWord(word, w_start, w_end, 0.6))
                idx += 1.0 / words_per_region if words_per_region > 0 else 1.0
        return aligned

    def _uniform_align(self, words: list[str],
                       total_ms: float) -> list[AlignedWord]:
        if not words:
            return []
        dur_per = total_ms / len(words)
        aligned: list[AlignedWord] = []
        for i, word in enumerate(words):
            start = i * dur_per
            end = (i + 1) * dur_per
            aligned.append(AlignedWord(word, start, end, 0.4))
        return aligned

    def analyze_word_segments(
        self, audio_path: str, alignment: AlignmentResult,
    ) -> list[tuple[AlignedWord, DSPAnalysisResult]]:
        samples, sr = _read_wav_samples(audio_path)
        if not samples:
            return [(w, DSPAnalysisResult()) for w in alignment.words]
        results: list[tuple[AlignedWord, DSPAnalysisResult]] = []
        for word in alignment.words:
            start_idx = int(word.start_ms * sr / 1000.0)
            end_idx = int(word.end_ms * sr / 1000.0)
            start_idx = max(0, min(start_idx, len(samples)))
            end_idx = max(start_idx, min(end_idx, len(samples)))
            segment = samples[start_idx:end_idx]
            if len(segment) < 64:
                results.append((word, DSPAnalysisResult()))
            else:
                analysis = _fast_analyze(segment, sr)
                results.append((word, analysis))
        return results


def _fast_analyze(samples: list[float], sr: int) -> DSPAnalysisResult:
    result = DSPAnalysisResult()
    result.sample_rate = sr
    result.num_samples = len(samples)
    if not samples:
        return result
    sum_sq = sum(s * s for s in samples)
    result.rms_loudness = math.sqrt(sum_sq / len(samples))
    result.peak_amplitude = max(abs(s) for s in samples)
    result.envelope_duration_ms = (len(samples) / sr) * 1000.0
    n = len(samples)
    min_lag = sr // 800
    max_lag = min(sr // 50, n // 2)
    if min_lag < max_lag and n >= 128:
        window = samples[:min(2048, n)]
        wlen = len(window)
        best_corr = 0.0
        best_lag = min_lag
        for lag in range(min_lag, max_lag):
            corr = 0.0
            norm1 = 0.0
            norm2 = 0.0
            count = min(wlen - lag, 1024)
            for i in range(count):
                corr += window[i] * window[i + lag]
                norm1 += window[i] * window[i]
                norm2 += window[i + lag] * window[i + lag]
            denom = math.sqrt(norm1 * norm2) if norm1 > 0 and norm2 > 0 else 1.0
            normalized = corr / denom if denom > 0 else 0.0
            if normalized > best_corr:
                best_corr = normalized
                best_lag = lag
        if best_corr > 0.3 and best_lag > 0:
            result.pitch_hz = sr / best_lag
            result.pitch_confidence = min(1.0, best_corr)
    return result
