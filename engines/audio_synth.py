import io
import math
import struct
import tempfile
import os
from typing import Any
from .preview_engine import PreviewSynthesizer, PreviewResult, PreviewQuality

SAMPLE_RATE = 44100
TWO_PI = 2.0 * math.pi


def _write_wav(samples: list[float], sample_rate: int = SAMPLE_RATE) -> bytes:
    num_samples = len(samples)
    buf = io.BytesIO()
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = num_samples * block_align

    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))
    buf.write(struct.pack("<H", 1))
    buf.write(struct.pack("<H", num_channels))
    buf.write(struct.pack("<I", sample_rate))
    buf.write(struct.pack("<I", byte_rate))
    buf.write(struct.pack("<H", block_align))
    buf.write(struct.pack("<H", bits_per_sample))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))

    for s in samples:
        clamped = max(-1.0, min(1.0, s))
        buf.write(struct.pack("<h", int(clamped * 32767)))

    return buf.getvalue()


VOWEL_MAP: dict[str, str] = {
    "a": "A", "e": "E", "i": "I", "o": "O", "u": "U",
}

DEFAULT_VOWEL = "A"

VOICE_TYPES = ["Male", "Female", "Robot", "Family Bathroom", "Muted Percussive Piano"]

FORMANTS: dict[str, dict[str, list[tuple[float, float, float]]]] = {
    "Male": {
        "A": [(730, 90, 1.0), (1090, 110, 0.5), (2440, 120, 0.25)],
        "E": [(530, 60, 1.0), (1840, 100, 0.5), (2480, 120, 0.2)],
        "I": [(270, 60, 1.0), (2290, 100, 0.4), (3010, 120, 0.15)],
        "O": [(570, 70, 1.0), (840, 80, 0.6), (2410, 120, 0.2)],
        "U": [(300, 60, 1.0), (870, 90, 0.4), (2240, 120, 0.15)],
    },
    "Female": {
        "A": [(850, 80, 1.0), (1220, 100, 0.5), (2810, 120, 0.25)],
        "E": [(610, 60, 1.0), (2330, 100, 0.45), (2990, 120, 0.18)],
        "I": [(310, 50, 1.0), (2790, 100, 0.35), (3310, 120, 0.12)],
        "O": [(640, 70, 1.0), (1010, 80, 0.55), (2710, 120, 0.2)],
        "U": [(350, 55, 1.0), (950, 80, 0.4), (2530, 120, 0.15)],
    },
    "Robot": {
        "A": [(700, 40, 1.0), (1100, 50, 0.7), (2500, 60, 0.5)],
        "E": [(500, 40, 1.0), (1800, 50, 0.7), (2500, 60, 0.5)],
        "I": [(300, 35, 1.0), (2200, 50, 0.6), (3000, 60, 0.4)],
        "O": [(550, 40, 1.0), (850, 50, 0.7), (2400, 60, 0.5)],
        "U": [(320, 35, 1.0), (900, 50, 0.6), (2300, 60, 0.4)],
    },
    "Family Bathroom": {
        "A": [(780, 130, 1.0), (1150, 160, 0.6), (2500, 200, 0.35)],
        "E": [(570, 100, 1.0), (1900, 150, 0.55), (2550, 200, 0.25)],
        "I": [(290, 90, 1.0), (2350, 150, 0.45), (3100, 200, 0.2)],
        "O": [(600, 110, 1.0), (900, 130, 0.65), (2450, 200, 0.3)],
        "U": [(330, 95, 1.0), (910, 130, 0.45), (2300, 200, 0.2)],
    },
}

VOICE_TYPE_BASE_FREQ: dict[str, float] = {
    "Male": 120.0,
    "Female": 220.0,
    "Robot": 150.0,
    "Family Bathroom": 155.0,
}

SINGER_FREQ_OFFSETS: dict[str, float] = {
    "default": 0.0,
    "singer_a": -15.0,
    "singer_b": 30.0,
    "singer_c": -30.0,
}

DELIVERY_PARAMS: dict[str, dict[str, float]] = {
    "Whisper": {"amplitude": 0.25, "noise_mix": 0.55, "harmonic_count": 6, "harmonic_decay": 0.7},
    "Normal": {"amplitude": 0.5, "noise_mix": 0.03, "harmonic_count": 12, "harmonic_decay": 0.85},
    "Yell": {"amplitude": 0.8, "noise_mix": 0.08, "harmonic_count": 16, "harmonic_decay": 0.9},
    "Scream": {"amplitude": 0.95, "noise_mix": 0.18, "harmonic_count": 20, "harmonic_decay": 0.92},
    "Bravado": {"amplitude": 0.75, "noise_mix": 0.05, "harmonic_count": 14, "harmonic_decay": 0.88},
}


def _detect_vowel(word: str) -> str:
    vowels_found: list[str] = []
    for ch in word.lower():
        mapped = VOWEL_MAP.get(ch)
        if mapped:
            vowels_found.append(mapped)
    if not vowels_found:
        return DEFAULT_VOWEL
    return vowels_found[len(vowels_found) // 2]


def _formant_gain(freq: float, formant_freq: float, bandwidth: float) -> float:
    delta = freq - formant_freq
    return math.exp(-0.5 * (delta / (bandwidth * 0.5)) ** 2)


def _apply_formants(harmonic_freq: float,
                    formants: list[tuple[float, float, float]]) -> float:
    gain = 0.0
    for f_freq, f_bw, f_amp in formants:
        gain += f_amp * _formant_gain(harmonic_freq, f_freq, f_bw)
    return gain


_noise_state = 12345.0


def _pseudo_noise() -> float:
    global _noise_state
    _noise_state = (_noise_state * 1103515245.0 + 12345.0) % (2.0 ** 31)
    return (_noise_state / (2.0 ** 31)) * 2.0 - 1.0


def _filtered_noise(formants: list[tuple[float, float, float]],
                    t_index: int) -> float:
    raw = _pseudo_noise()
    center_freq = formants[0][0] if formants else 500.0
    mod = math.sin(TWO_PI * center_freq * t_index / SAMPLE_RATE)
    return raw * 0.5 + raw * mod * 0.5


def _envelope(t: float, duration: float, attack: float = 0.025,
              release: float = 0.06) -> float:
    if t < attack:
        return t / attack
    if t > duration - release:
        remaining = duration - t
        if remaining <= 0:
            return 0.0
        return remaining / release
    return 1.0


MUTED_PIANO_PARAMS: dict[str, float] = {
    "attack_ms": 2,
    "decay_ms": 40,
    "sustain": 0.05,
    "release_ms": 60,
    "harmonic_strength": 0.25,
    "noise_amount": 0.08,
    "vibrato_depth": 0,
    "formant_strength": 0,
    "brightness": 0.3,
}


def _synthesize_muted_piano(word: str, duration_ms: int, loudness_pct: int,
                            intensity: int, pitch_offset: int,
                            quality: PreviewQuality) -> list[float]:
    p = MUTED_PIANO_PARAMS
    duration_s = max(0.05, duration_ms / 1000.0)
    num_samples = int(duration_s * SAMPLE_RATE)

    base_freq = 261.63
    word_hash = sum(ord(c) * (i + 1) for i, c in enumerate(word))
    base_freq *= 2.0 ** (pitch_offset / 12.0)
    base_freq *= 1.0 + (word_hash % 5 - 2) * 0.008
    base_freq = max(50.0, min(base_freq, 2000.0))

    attack_s = p["attack_ms"] / 1000.0
    decay_s = p["decay_ms"] / 1000.0
    sustain_lvl = p["sustain"]
    release_s = p["release_ms"] / 1000.0

    amplitude = 0.6 * (loudness_pct / 100.0)
    intensity_factor = 0.5 + (intensity / 100.0) * 0.5
    amplitude *= intensity_factor

    brightness = p["brightness"]
    harmonic_strength = p["harmonic_strength"]
    noise_amount = p["noise_amount"]

    max_harmonics = 12 if quality != PreviewQuality.FAST else 6
    harmonic_gains: list[float] = []
    for h in range(1, max_harmonics + 1):
        h_freq = base_freq * h
        if h_freq > SAMPLE_RATE / 2.0:
            break
        rolloff = harmonic_strength ** h
        bright_cut = math.exp(-h * (1.0 - brightness) * 0.5)
        harmonic_gains.append(rolloff * bright_cut)

    actual_harmonics = len(harmonic_gains)
    if actual_harmonics == 0:
        harmonic_gains = [1.0]
        actual_harmonics = 1
    gain_sum = sum(harmonic_gains)
    if gain_sum > 0:
        harmonic_gains = [g / gain_sum for g in harmonic_gains]

    lp_cutoff_start = 1800.0
    lp_cutoff_end = 300.0
    lp_decay_s = decay_s * 2.0

    phases: list[float] = [0.0] * actual_harmonics
    lp_prev = 0.0
    samples: list[float] = []

    for i in range(num_samples):
        t = i / SAMPLE_RATE

        if t < attack_s:
            env = t / attack_s if attack_s > 0 else 1.0
        elif t < attack_s + decay_s:
            decay_pos = (t - attack_s) / decay_s
            env = 1.0 - (1.0 - sustain_lvl) * decay_pos
        elif t > duration_s - release_s:
            remaining = duration_s - t
            env = max(0.0, (remaining / release_s)) * sustain_lvl
        else:
            env = sustain_lvl

        sample = 0.0
        for h in range(actual_harmonics):
            h_freq = base_freq * (h + 1)
            phases[h] += TWO_PI * h_freq / SAMPLE_RATE
            if phases[h] > TWO_PI:
                phases[h] -= TWO_PI
            sample += math.sin(phases[h]) * harmonic_gains[h]

        noise = _pseudo_noise() * noise_amount
        sample = sample * (1.0 - noise_amount) + noise

        cutoff_env = math.exp(-t / lp_decay_s) if lp_decay_s > 0 else 0.0
        cutoff = lp_cutoff_end + (lp_cutoff_start - lp_cutoff_end) * cutoff_env
        rc = 1.0 / (TWO_PI * cutoff)
        dt = 1.0 / SAMPLE_RATE
        alpha = dt / (rc + dt)
        lp_prev = lp_prev + alpha * (sample - lp_prev)
        sample = lp_prev

        samples.append(sample * env * amplitude)

    return samples


def _synthesize_instrument(word: str, duration_ms: int, loudness_pct: int,
                           intensity: int, pitch_offset: int,
                           patch_dict: dict[str, Any],
                           quality: PreviewQuality) -> list[float]:
    attack_s = patch_dict.get("attack_ms", 2.0) / 1000.0
    decay_s = patch_dict.get("decay_ms", 40.0) / 1000.0
    sustain_lvl = patch_dict.get("sustain_level", 0.05)
    release_s = patch_dict.get("release_ms", 60.0) / 1000.0
    damping = patch_dict.get("damping", 0.5)
    harmonics_level = patch_dict.get("harmonics_level", 0.5)
    lowpass_hz = patch_dict.get("lowpass_hz", 4000.0)
    brightness = patch_dict.get("brightness", 0.5)
    noise_amount = patch_dict.get("noise_amount", 0.0)
    transient_click = patch_dict.get("transient_click", 0.0)
    vibrato_on = patch_dict.get("default_vibrato_on", True)

    duration_s = max(0.05, duration_ms / 1000.0)
    num_samples = int(duration_s * SAMPLE_RATE)

    base_freq = 261.63
    word_hash = sum(ord(c) * (i + 1) for i, c in enumerate(word))
    base_freq *= 2.0 ** (pitch_offset / 12.0)
    base_freq *= 1.0 + (word_hash % 5 - 2) * 0.008
    base_freq = max(50.0, min(base_freq, 2000.0))

    amplitude = 0.6 * (loudness_pct / 100.0)
    intensity_factor = 0.5 + (intensity / 100.0) * 0.5
    amplitude *= intensity_factor

    max_harmonics = 12 if quality != PreviewQuality.FAST else 6
    harmonic_gains: list[float] = []
    for h in range(1, max_harmonics + 1):
        h_freq = base_freq * h
        if h_freq > SAMPLE_RATE / 2.0:
            break
        rolloff = harmonics_level ** h
        bright_cut = math.exp(-h * (1.0 - brightness) * 0.5)
        damp_cut = math.exp(-h * damping * 0.3)
        harmonic_gains.append(rolloff * bright_cut * damp_cut)

    actual_harmonics = len(harmonic_gains)
    if actual_harmonics == 0:
        harmonic_gains = [1.0]
        actual_harmonics = 1
    gain_sum = sum(harmonic_gains)
    if gain_sum > 0:
        harmonic_gains = [g / gain_sum for g in harmonic_gains]

    lp_cutoff_start = lowpass_hz
    lp_cutoff_end = max(200.0, lowpass_hz * 0.15)
    lp_decay_s = decay_s * (1.0 + damping)

    phases: list[float] = [0.0] * actual_harmonics
    lp_prev = 0.0
    samples: list[float] = []

    for i in range(num_samples):
        t = i / SAMPLE_RATE

        if t < attack_s:
            env = t / attack_s if attack_s > 0 else 1.0
        elif t < attack_s + decay_s:
            decay_pos = (t - attack_s) / decay_s
            env = 1.0 - (1.0 - sustain_lvl) * decay_pos
        elif t > duration_s - release_s:
            remaining = duration_s - t
            env = max(0.0, (remaining / release_s)) * sustain_lvl
        else:
            env = sustain_lvl

        vib = 1.0
        if vibrato_on:
            vib = 1.0 + 0.005 * math.sin(TWO_PI * 5.0 * t)

        sample = 0.0
        for h in range(actual_harmonics):
            h_freq = base_freq * (h + 1) * vib
            phases[h] += TWO_PI * h_freq / SAMPLE_RATE
            if phases[h] > TWO_PI:
                phases[h] -= TWO_PI
            sample += math.sin(phases[h]) * harmonic_gains[h]

        if transient_click > 0 and t < 0.005:
            click_env = 1.0 - t / 0.005
            sample += _pseudo_noise() * transient_click * click_env * 2.0

        noise = _pseudo_noise() * noise_amount
        sample = sample * (1.0 - noise_amount) + noise

        cutoff_env = math.exp(-t / lp_decay_s) if lp_decay_s > 0 else 0.0
        cutoff = lp_cutoff_end + (lp_cutoff_start - lp_cutoff_end) * cutoff_env
        rc = 1.0 / (TWO_PI * cutoff)
        dt_s = 1.0 / SAMPLE_RATE
        alpha = dt_s / (rc + dt_s)
        lp_prev = lp_prev + alpha * (sample - lp_prev)
        sample = lp_prev

        samples.append(sample * env * amplitude)

    return samples


def _synthesize_vocal(word: str, duration_ms: int, loudness_pct: int,
                      intensity: int, pitch_offset: int,
                      delivery: str, voice_id: str,
                      voice_type: str,
                      quality: PreviewQuality) -> list[float]:
    duration_s = max(0.05, duration_ms / 1000.0)
    num_samples = int(duration_s * SAMPLE_RATE)

    base_freq = VOICE_TYPE_BASE_FREQ.get(voice_type, 150.0)
    base_freq += SINGER_FREQ_OFFSETS.get(voice_id, 0.0)
    freq = base_freq * (2.0 ** (pitch_offset / 12.0))

    word_hash = sum(ord(c) * (i + 1) for i, c in enumerate(word))
    freq *= 1.0 + (word_hash % 5 - 2) * 0.008
    freq = max(50.0, min(freq, 1000.0))

    vowel = _detect_vowel(word)
    formants = FORMANTS.get(voice_type, FORMANTS["Male"]).get(
        vowel, FORMANTS["Male"]["A"]
    )

    params = DELIVERY_PARAMS.get(delivery, DELIVERY_PARAMS["Normal"])
    amplitude = params["amplitude"] * (loudness_pct / 100.0)
    noise_mix = params["noise_mix"]
    harmonic_count = int(params["harmonic_count"])
    harmonic_decay = params["harmonic_decay"]

    intensity_factor = 0.5 + (intensity / 100.0) * 0.5
    amplitude *= intensity_factor

    vibrato_rate = 4.5 + (intensity / 100.0) * 3.0
    vibrato_depth = 0.003 + (intensity / 100.0) * 0.015

    if voice_type == "Robot":
        vibrato_depth *= 0.1
        vibrato_rate = 8.0

    attack = 0.02 if quality == PreviewQuality.FAST else 0.035
    release = 0.05 if quality == PreviewQuality.FAST else 0.1

    if quality == PreviewQuality.FAST:
        harmonic_count = min(harmonic_count, 8)

    harmonic_gains: list[float] = []
    for h in range(1, harmonic_count + 1):
        h_freq = freq * h
        if h_freq > SAMPLE_RATE / 2.0:
            break
        rolloff = harmonic_decay ** (h - 1)
        formant_g = _apply_formants(h_freq, formants)
        harmonic_gains.append(rolloff * formant_g)

    actual_harmonics = len(harmonic_gains)
    if actual_harmonics == 0:
        harmonic_gains = [1.0]
        actual_harmonics = 1

    gain_sum = sum(harmonic_gains)
    if gain_sum > 0:
        harmonic_gains = [g / gain_sum for g in harmonic_gains]

    phases: list[float] = [0.0] * actual_harmonics
    samples: list[float] = []

    for i in range(num_samples):
        t = i / SAMPLE_RATE
        env = _envelope(t, duration_s, attack, release)

        vibrato = 1.0 + vibrato_depth * math.sin(TWO_PI * vibrato_rate * t)
        f0 = freq * vibrato

        sample = 0.0
        for h in range(actual_harmonics):
            h_freq = f0 * (h + 1)
            phases[h] += TWO_PI * h_freq / SAMPLE_RATE
            if phases[h] > TWO_PI:
                phases[h] -= TWO_PI

            if voice_type == "Robot":
                wave = 1.0 if math.sin(phases[h]) > 0 else -1.0
                wave *= 0.7
                wave += math.sin(phases[h]) * 0.3
            else:
                wave = math.sin(phases[h])
                if h == 0:
                    wave += 0.15 * math.sin(2.0 * phases[h])

            sample += wave * harmonic_gains[h]

        noise = _filtered_noise(formants, i)
        sample = sample * (1.0 - noise_mix) + noise * noise_mix

        if voice_type == "Robot":
            if sample > 0.3:
                sample = 0.3 + (sample - 0.3) * 0.3
            elif sample < -0.3:
                sample = -0.3 + (sample + 0.3) * 0.3

        samples.append(sample * env * amplitude)

    return samples


class AudioPreviewSynthesizer(PreviewSynthesizer):
    def __init__(self) -> None:
        self._cache_dir = os.path.join(tempfile.gettempdir(), "kds_preview_cache")
        os.makedirs(self._cache_dir, exist_ok=True)
        self._voice_type: str = "Male"
        self._instrument_patch: dict[str, Any] | None = None

    @property
    def cache_dir(self) -> str:
        return self._cache_dir

    @property
    def voice_type(self) -> str:
        return self._voice_type

    def set_voice_type(self, vtype: str) -> None:
        if vtype in FORMANTS or vtype == "Muted Percussive Piano":
            self._voice_type = vtype

    def set_instrument_patch(self, patch_dict: dict[str, Any] | None) -> None:
        self._instrument_patch = patch_dict

    def synthesize_token(self, token_data: dict[str, Any],
                         voice_profile_id: str,
                         quality: PreviewQuality) -> PreviewResult:
        word = token_data.get("word", "")
        duration_ms = token_data.get("duration_ms", 500)
        loudness_pct = token_data.get("loudness_pct", 100)
        intensity = token_data.get("intensity", 50)
        pitch_offset = token_data.get("pitch_offset", 0)
        delivery = token_data.get("delivery", "Normal")

        if self._instrument_patch is not None:
            samples = _synthesize_instrument(
                word, duration_ms, loudness_pct, intensity,
                pitch_offset, self._instrument_patch, quality,
            )
        elif self._voice_type == "Muted Percussive Piano":
            samples = _synthesize_muted_piano(
                word, duration_ms, loudness_pct, intensity,
                pitch_offset, quality,
            )
        else:
            samples = _synthesize_vocal(
                word, duration_ms, loudness_pct, intensity,
                pitch_offset, delivery, voice_profile_id,
                self._voice_type, quality,
            )
        wav_data = _write_wav(samples)

        result = PreviewResult()
        result.audio_data = wav_data
        result.duration_ms = duration_ms
        result.quality = quality
        result.token_index = token_data.get("index", -1)
        return result

    def synthesize_phrase(self, tokens: list[dict[str, Any]],
                          voice_profile_id: str,
                          quality: PreviewQuality) -> PreviewResult:
        all_samples: list[float] = []
        total_ms = 0
        for td in tokens:
            word = td.get("word", "")
            dur = td.get("duration_ms", 500)
            loud = td.get("loudness_pct", 100)
            intensity = td.get("intensity", 50)
            pitch = td.get("pitch_offset", 0)
            delivery = td.get("delivery", "Normal")
            if self._instrument_patch is not None:
                samples = _synthesize_instrument(
                    word, dur, loud, intensity, pitch,
                    self._instrument_patch, quality,
                )
            elif self._voice_type == "Muted Percussive Piano":
                samples = _synthesize_muted_piano(
                    word, dur, loud, intensity, pitch, quality,
                )
            else:
                samples = _synthesize_vocal(
                    word, dur, loud, intensity, pitch,
                    delivery, voice_profile_id,
                    self._voice_type, quality,
                )
            all_samples.extend(samples)
            gap_samples = int(0.05 * SAMPLE_RATE)
            all_samples.extend([0.0] * gap_samples)
            total_ms += dur + 50

        wav_data = _write_wav(all_samples)
        result = PreviewResult()
        result.audio_data = wav_data
        result.duration_ms = total_ms
        result.quality = quality
        return result

    def supports_quality(self, quality: PreviewQuality) -> bool:
        return True
