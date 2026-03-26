import struct
import math
from typing import Any


FORMAT_VERSION = 1


class DSPAnalysisResult:
    def __init__(self) -> None:
        self.rms_loudness: float = 0.0
        self.peak_amplitude: float = 0.0
        self.pitch_hz: float = 0.0
        self.vibrato_rate_hz: float = 0.0
        self.vibrato_depth_cents: float = 0.0
        self.spectral_centroid_hz: float = 0.0
        self.spectral_rolloff_hz: float = 0.0
        self.envelope_duration_ms: float = 0.0
        self.sample_rate: int = 44100
        self.num_samples: int = 0
        self.pitch_confidence: float = 0.0
        self.vibrato_confidence: float = 0.0
        self.overall_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": FORMAT_VERSION,
            "rms_loudness": round(self.rms_loudness, 6),
            "peak_amplitude": round(self.peak_amplitude, 6),
            "pitch_hz": round(self.pitch_hz, 2),
            "vibrato_rate_hz": round(self.vibrato_rate_hz, 2),
            "vibrato_depth_cents": round(self.vibrato_depth_cents, 2),
            "spectral_centroid_hz": round(self.spectral_centroid_hz, 2),
            "spectral_rolloff_hz": round(self.spectral_rolloff_hz, 2),
            "envelope_duration_ms": round(self.envelope_duration_ms, 2),
            "sample_rate": self.sample_rate,
            "num_samples": self.num_samples,
            "pitch_confidence": round(self.pitch_confidence, 3),
            "vibrato_confidence": round(self.vibrato_confidence, 3),
            "overall_confidence": round(self.overall_confidence, 3),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DSPAnalysisResult":
        r = cls()
        r.rms_loudness = data.get("rms_loudness", 0.0)
        r.peak_amplitude = data.get("peak_amplitude", 0.0)
        r.pitch_hz = data.get("pitch_hz", 0.0)
        r.vibrato_rate_hz = data.get("vibrato_rate_hz", 0.0)
        r.vibrato_depth_cents = data.get("vibrato_depth_cents", 0.0)
        r.spectral_centroid_hz = data.get("spectral_centroid_hz", 0.0)
        r.spectral_rolloff_hz = data.get("spectral_rolloff_hz", 0.0)
        r.envelope_duration_ms = data.get("envelope_duration_ms", 0.0)
        r.sample_rate = data.get("sample_rate", 44100)
        r.num_samples = data.get("num_samples", 0)
        r.pitch_confidence = data.get("pitch_confidence", 0.0)
        r.vibrato_confidence = data.get("vibrato_confidence", 0.0)
        r.overall_confidence = data.get("overall_confidence", 0.0)
        return r


class DSPAnalyzer:
    def __init__(self, sample_rate: int = 44100) -> None:
        self._sample_rate = sample_rate

    def analyze_wav_file(self, path: str) -> DSPAnalysisResult:
        samples, sr = self._read_wav_mono(path)
        self._sample_rate = sr
        return self.analyze_samples(samples, sr)

    def analyze_samples(self, samples: list[float], sample_rate: int) -> DSPAnalysisResult:
        self._sample_rate = sample_rate
        result = DSPAnalysisResult()
        result.sample_rate = sample_rate
        result.num_samples = len(samples)

        if not samples:
            return result

        result.rms_loudness = self._compute_rms(samples)
        result.peak_amplitude = self._compute_peak(samples)
        pitch_hz, pitch_conf = self._estimate_pitch_with_confidence(samples, sample_rate)
        result.pitch_hz = pitch_hz
        result.pitch_confidence = pitch_conf
        vib_rate, vib_depth, vib_conf = self._estimate_vibrato_with_confidence(samples, sample_rate, result.pitch_hz)
        result.vibrato_rate_hz = vib_rate
        result.vibrato_depth_cents = vib_depth
        result.vibrato_confidence = vib_conf
        result.spectral_centroid_hz = self._spectral_centroid(samples, sample_rate)
        result.spectral_rolloff_hz = self._spectral_rolloff(samples, sample_rate)
        result.envelope_duration_ms = self._envelope_duration(samples, sample_rate)
        result.overall_confidence = self._compute_overall_confidence(result)

        return result

    def _read_wav_mono(self, path: str) -> tuple[list[float], int]:
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

            while True:
                chunk_id = f.read(4)
                if len(chunk_id) < 4:
                    break
                chunk_size = struct.unpack("<I", f.read(4))[0]
                if chunk_id == b"fmt ":
                    fmt_data = f.read(chunk_size)
                    audio_fmt = struct.unpack("<H", fmt_data[0:2])[0]
                    channels = struct.unpack("<H", fmt_data[2:4])[0]
                    sr = struct.unpack("<I", fmt_data[4:8])[0]
                    bits = struct.unpack("<H", fmt_data[14:16])[0]
                elif chunk_id == b"data":
                    raw = f.read(chunk_size)
                    break
                else:
                    f.read(chunk_size)
            else:
                return [], sr

            samples: list[float] = []
            bytes_per_sample = bits // 8
            frame_size = bytes_per_sample * channels
            num_frames = len(raw) // frame_size

            for i in range(num_frames):
                offset = i * frame_size
                if bits == 16:
                    val = struct.unpack_from("<h", raw, offset)[0]
                    samples.append(val / 32768.0)
                elif bits == 8:
                    val = raw[offset]
                    samples.append((val - 128) / 128.0)
                else:
                    val = struct.unpack_from("<h", raw, offset)[0]
                    samples.append(val / 32768.0)

            return samples, sr

    def _compute_rms(self, samples: list[float]) -> float:
        if not samples:
            return 0.0
        sum_sq = sum(s * s for s in samples)
        return math.sqrt(sum_sq / len(samples))

    def _compute_peak(self, samples: list[float]) -> float:
        if not samples:
            return 0.0
        return max(abs(s) for s in samples)

    def _estimate_pitch_autocorr(self, samples: list[float], sr: int) -> float:
        hz, _conf = self._estimate_pitch_with_confidence(samples, sr)
        return hz

    def _estimate_pitch_with_confidence(self, samples: list[float], sr: int) -> tuple[float, float]:
        n = len(samples)
        if n < 128:
            return 0.0, 0.0

        min_lag = sr // 800
        max_lag = min(sr // 50, n // 2)
        if min_lag >= max_lag:
            return 0.0, 0.0

        window_size = min(4096, n)
        window = samples[:window_size]

        best_corr = 0.0
        second_corr = 0.0
        best_lag = min_lag

        for lag in range(min_lag, max_lag):
            corr = 0.0
            norm1 = 0.0
            norm2 = 0.0
            count = min(window_size - lag, 2048)
            for i in range(count):
                corr += window[i] * window[i + lag]
                norm1 += window[i] * window[i]
                norm2 += window[i + lag] * window[i + lag]
            denom = math.sqrt(norm1 * norm2) if norm1 > 0 and norm2 > 0 else 1.0
            normalized = corr / denom if denom > 0 else 0.0
            if normalized > best_corr:
                second_corr = best_corr
                best_corr = normalized
                best_lag = lag
            elif normalized > second_corr:
                second_corr = normalized

        if best_corr < 0.3:
            return 0.0, 0.0

        confidence = best_corr
        if second_corr > 0:
            ratio = second_corr / best_corr
            if ratio > 0.9:
                confidence *= 0.7

        hz = sr / best_lag if best_lag > 0 else 0.0
        return hz, min(1.0, confidence)

    def _estimate_vibrato(self, samples: list[float], sr: int, base_pitch: float) -> tuple[float, float]:
        rate, depth, _conf = self._estimate_vibrato_with_confidence(samples, sr, base_pitch)
        return rate, depth

    def _estimate_vibrato_with_confidence(self, samples: list[float], sr: int, base_pitch: float) -> tuple[float, float, float]:
        if base_pitch <= 0 or len(samples) < sr // 4:
            return (0.0, 0.0, 0.0)

        hop = sr // 50
        window = sr // 25
        pitches: list[float] = []

        for start in range(0, len(samples) - window, hop):
            chunk = samples[start:start + window]
            p = self._estimate_pitch_autocorr(chunk, sr)
            if p > 0:
                pitches.append(p)

        if len(pitches) < 4:
            return (0.0, 0.0, 0.0)

        mean_p = sum(pitches) / len(pitches)
        deviations = [p - mean_p for p in pitches]

        zero_crossings = 0
        for i in range(1, len(deviations)):
            if deviations[i - 1] * deviations[i] < 0:
                zero_crossings += 1

        duration_s = len(deviations) * (hop / sr)
        vib_rate = (zero_crossings / 2) / duration_s if duration_s > 0 else 0.0

        if vib_rate < 2.0 or vib_rate > 15.0:
            return (0.0, 0.0, 0.0)

        max_dev = max(abs(d) for d in deviations)
        vib_depth_cents = 1200.0 * math.log2((mean_p + max_dev) / mean_p) if mean_p > 0 and max_dev > 0 else 0.0

        pitch_std = (sum(d * d for d in deviations) / len(deviations)) ** 0.5
        regularity = 1.0 - min(pitch_std / (mean_p * 0.1), 1.0) if mean_p > 0 else 0.0
        rate_confidence = 1.0 if 4.0 <= vib_rate <= 8.0 else max(0.0, 1.0 - abs(vib_rate - 6.0) / 6.0)
        confidence = (regularity * 0.6 + rate_confidence * 0.4)

        return (vib_rate, abs(vib_depth_cents), min(1.0, confidence))

    def _spectral_centroid(self, samples: list[float], sr: int) -> float:
        n = min(4096, len(samples))
        if n < 64:
            return 0.0

        window = samples[:n]
        fft_size = n
        real = [0.0] * fft_size
        imag = [0.0] * fft_size

        for k in range(fft_size // 2):
            for i in range(n):
                angle = -2.0 * math.pi * k * i / fft_size
                real[k] += window[i] * math.cos(angle)
                imag[k] += window[i] * math.sin(angle)

        magnitudes = [math.sqrt(real[k] ** 2 + imag[k] ** 2) for k in range(fft_size // 2)]
        freq_bin = sr / fft_size

        weighted_sum = sum(magnitudes[k] * k * freq_bin for k in range(len(magnitudes)))
        total_mag = sum(magnitudes)

        return weighted_sum / total_mag if total_mag > 0 else 0.0

    def _spectral_rolloff(self, samples: list[float], sr: int, threshold: float = 0.85) -> float:
        n = min(4096, len(samples))
        if n < 64:
            return 0.0

        window = samples[:n]
        fft_size = n
        real = [0.0] * fft_size
        imag = [0.0] * fft_size

        for k in range(fft_size // 2):
            for i in range(n):
                angle = -2.0 * math.pi * k * i / fft_size
                real[k] += window[i] * math.cos(angle)
                imag[k] += window[i] * math.sin(angle)

        magnitudes = [math.sqrt(real[k] ** 2 + imag[k] ** 2) for k in range(fft_size // 2)]
        freq_bin = sr / fft_size

        total = sum(magnitudes)
        target = total * threshold
        cumulative = 0.0

        for k, mag in enumerate(magnitudes):
            cumulative += mag
            if cumulative >= target:
                return k * freq_bin

        return (len(magnitudes) - 1) * freq_bin

    def _compute_overall_confidence(self, result: DSPAnalysisResult) -> float:
        weights = []
        scores = []

        if result.pitch_hz > 0:
            weights.append(0.5)
            scores.append(result.pitch_confidence)
        else:
            weights.append(0.5)
            scores.append(0.0)

        if result.vibrato_rate_hz > 0:
            weights.append(0.2)
            scores.append(result.vibrato_confidence)
        else:
            weights.append(0.2)
            scores.append(0.5)

        rms_ok = 1.0 if result.rms_loudness > 0.01 else result.rms_loudness / 0.01
        weights.append(0.15)
        scores.append(rms_ok)

        duration_s = result.num_samples / result.sample_rate if result.sample_rate > 0 else 0
        dur_ok = min(duration_s / 0.5, 1.0)
        weights.append(0.15)
        scores.append(dur_ok)

        total_w = sum(weights)
        if total_w <= 0:
            return 0.0
        return sum(w * s for w, s in zip(weights, scores)) / total_w

    def _envelope_duration(self, samples: list[float], sr: int) -> float:
        if not samples:
            return 0.0

        peak = max(abs(s) for s in samples)
        if peak < 0.001:
            return 0.0

        threshold = peak * 0.1
        start_idx = 0
        for i, s in enumerate(samples):
            if abs(s) >= threshold:
                start_idx = i
                break

        end_idx = len(samples) - 1
        for i in range(len(samples) - 1, -1, -1):
            if abs(samples[i]) >= threshold:
                end_idx = i
                break

        duration_samples = end_idx - start_idx
        return (duration_samples / sr) * 1000.0


class TokenParameterMapper:
    def map_to_params(self, analysis: DSPAnalysisResult) -> dict[str, Any]:
        params: dict[str, Any] = {}

        params["loudness_pct"] = self._map_loudness(analysis.rms_loudness, analysis.peak_amplitude)
        params["intensity"] = self._map_intensity(
            analysis.rms_loudness, analysis.spectral_centroid_hz,
            analysis.vibrato_depth_cents,
        )
        params["pitch_offset"] = self._map_pitch_offset(analysis.pitch_hz)
        params["duration_ms"] = self._map_duration(analysis.envelope_duration_ms)
        params["delivery"] = self._classify_delivery(
            analysis.rms_loudness, analysis.peak_amplitude,
            analysis.spectral_centroid_hz, analysis.vibrato_depth_cents,
        )

        return params

    def _map_loudness(self, rms: float, peak: float) -> int:
        db = 20.0 * math.log10(max(rms, 1e-6))
        pct = int(((db + 60.0) / 60.0) * 200.0)
        return max(0, min(200, pct))

    def _map_intensity(self, rms: float, centroid: float, vib_depth: float) -> int:
        rms_factor = min(rms / 0.3, 1.0) * 40
        bright_factor = min(centroid / 4000.0, 1.0) * 30
        vib_factor = min(vib_depth / 50.0, 1.0) * 30
        return max(0, min(100, int(rms_factor + bright_factor + vib_factor)))

    def _map_pitch_offset(self, pitch_hz: float) -> int:
        if pitch_hz <= 0:
            return 0
        ref_hz = 261.63
        semitones = 12.0 * math.log2(pitch_hz / ref_hz)
        offset = int(round(semitones)) % 12
        if offset > 6:
            offset -= 12
        return max(-24, min(24, offset))

    def _map_duration(self, envelope_ms: float) -> int:
        if envelope_ms <= 0:
            return 500
        return max(50, min(2000, int(envelope_ms)))

    def _classify_delivery(self, rms: float, peak: float, centroid: float, vib_depth: float) -> str:
        if rms < 0.02:
            return "Whisper"
        if rms > 0.4 and centroid > 3000:
            return "Scream"
        if rms > 0.3 and peak > 0.8:
            return "Yell"
        if vib_depth > 30 and rms > 0.15:
            return "Bravado"
        return "Normal"
