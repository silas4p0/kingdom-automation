import json
import math
import os
import time
from typing import Any

FORMAT_VERSION = 2
PRESET_DIR = os.path.join(os.path.expanduser("~"), ".kds_lpe", "style_presets")


DELIVERY_IDS = {"Whisper": 0, "Normal": 1, "Yell": 2, "Scream": 3, "Bravado": 4}

INSTRUMENT_PRESETS: dict[str, dict[str, float]] = {
    "muted_piano": {
        "attack_ms": 2,
        "decay_ms": 40,
        "sustain": 0.05,
        "release_ms": 60,
        "harmonic_strength": 0.25,
        "noise_amount": 0.08,
        "vibrato_depth": 0,
        "formant_strength": 0,
        "brightness": 0.3,
    },
}

FEATURE_KEYS = [
    "rms_norm", "peak_norm", "pitch_median_st", "vibrato_rate",
    "vibrato_depth", "centroid_norm", "rolloff_norm", "env_duration_norm",
    "delivery_id",
]

FEATURE_WEIGHTS = {
    "rms_norm": 0.10,
    "peak_norm": 0.05,
    "pitch_median_st": 0.25,
    "vibrato_rate": 0.10,
    "vibrato_depth": 0.10,
    "centroid_norm": 0.10,
    "rolloff_norm": 0.05,
    "env_duration_norm": 0.10,
    "delivery_id": 0.15,
}


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def compute_feature_vector(analysis: dict[str, Any]) -> dict[str, float]:
    rms = analysis.get("rms_loudness", 0.0)
    peak = analysis.get("peak_amplitude", 0.0)
    pitch = analysis.get("pitch_hz", 0.0)
    vib_rate = analysis.get("vibrato_rate_hz", 0.0)
    vib_depth = analysis.get("vibrato_depth_cents", 0.0)
    centroid = analysis.get("spectral_centroid_hz", 0.0)
    rolloff = analysis.get("spectral_rolloff_hz", 0.0)
    env_dur = analysis.get("envelope_duration_ms", 0.0)
    delivery = analysis.get("delivery", "Normal") if isinstance(analysis.get("delivery"), str) else "Normal"

    pitch_st = 12.0 * math.log2(pitch / 261.63) if pitch > 20 else 0.0

    return {
        "rms_norm": _clamp(rms / 0.5),
        "peak_norm": _clamp(peak / 1.0),
        "pitch_median_st": _clamp((pitch_st + 36) / 72.0),
        "vibrato_rate": _clamp(vib_rate / 12.0),
        "vibrato_depth": _clamp(vib_depth / 100.0),
        "centroid_norm": _clamp(centroid / 8000.0),
        "rolloff_norm": _clamp(rolloff / 16000.0),
        "env_duration_norm": _clamp(env_dur / 3000.0),
        "delivery_id": DELIVERY_IDS.get(delivery, 1) / 4.0,
    }


def compute_similarity(
    vec_a: dict[str, float],
    vec_b: dict[str, float],
    confidence: dict[str, float] | None = None,
) -> tuple[float, dict[str, float]]:
    weights = dict(FEATURE_WEIGHTS)
    if confidence:
        pitch_conf = confidence.get("pitch_confidence", 1.0)
        vib_conf = confidence.get("vibrato_confidence", 1.0)
        weights["pitch_median_st"] *= max(0.2, pitch_conf)
        weights["vibrato_rate"] *= max(0.2, vib_conf)
        weights["vibrato_depth"] *= max(0.2, vib_conf)

    total_w = sum(weights.values())
    if total_w <= 0:
        return 0.0, {}

    deltas: dict[str, float] = {}
    dist = 0.0
    for key in FEATURE_KEYS:
        a = vec_a.get(key, 0.0)
        b = vec_b.get(key, 0.0)
        d = abs(a - b)
        deltas[key] = d
        w = weights.get(key, 0.0)
        dist += w * d

    score = max(0.0, 1.0 - dist / total_w)
    return score, deltas


class StylePreset:
    def __init__(self, name: str = "") -> None:
        self.name: str = name
        self.created_at: float = time.time()
        self.loudness_pct: int = 100
        self.intensity: int = 50
        self.pitch_offset: int = 0
        self.duration_ms: int = 500
        self.delivery: str = "Normal"
        self.analysis_features: dict[str, Any] = {}
        self.feature_vector: dict[str, float] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": FORMAT_VERSION,
            "name": self.name,
            "created_at": self.created_at,
            "loudness_pct": self.loudness_pct,
            "intensity": self.intensity,
            "pitch_offset": self.pitch_offset,
            "duration_ms": self.duration_ms,
            "delivery": self.delivery,
            "analysis_features": self.analysis_features,
            "feature_vector": self.feature_vector,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StylePreset":
        p = cls(data.get("name", ""))
        p.created_at = data.get("created_at", time.time())
        p.loudness_pct = data.get("loudness_pct", 100)
        p.intensity = data.get("intensity", 50)
        p.pitch_offset = data.get("pitch_offset", 0)
        p.duration_ms = data.get("duration_ms", 500)
        p.delivery = data.get("delivery", "Normal")
        p.analysis_features = data.get("analysis_features", {})
        p.feature_vector = data.get("feature_vector", {})
        if not p.feature_vector and p.analysis_features:
            p.feature_vector = compute_feature_vector(p.analysis_features)
        return p

    @classmethod
    def from_mapped_params(cls, name: str, params: dict[str, Any],
                           analysis: dict[str, Any] | None = None) -> "StylePreset":
        p = cls(name)
        p.loudness_pct = params.get("loudness_pct", 100)
        p.intensity = params.get("intensity", 50)
        p.pitch_offset = params.get("pitch_offset", 0)
        p.duration_ms = params.get("duration_ms", 500)
        p.delivery = params.get("delivery", "Normal")
        if analysis:
            p.analysis_features = analysis
            merged = dict(analysis)
            merged["delivery"] = params.get("delivery", "Normal")
            p.feature_vector = compute_feature_vector(merged)
        return p


class StylePresetStore:
    def __init__(self, preset_dir: str = PRESET_DIR) -> None:
        self._dir = preset_dir
        self._presets: dict[str, StylePreset] = {}
        self._ensure_dir()
        self._load_all()

    def _ensure_dir(self) -> None:
        os.makedirs(self._dir, exist_ok=True)

    def _load_all(self) -> None:
        self._presets.clear()
        if not os.path.isdir(self._dir):
            return
        for fname in sorted(os.listdir(self._dir)):
            if fname.endswith(".json"):
                path = os.path.join(self._dir, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    preset = StylePreset.from_dict(data)
                    self._presets[preset.name] = preset
                except (json.JSONDecodeError, KeyError, OSError):
                    pass

    def list_names(self) -> list[str]:
        return sorted(self._presets.keys())

    def get(self, name: str) -> StylePreset | None:
        return self._presets.get(name)

    def all_presets(self) -> list[StylePreset]:
        return sorted(self._presets.values(), key=lambda p: p.created_at)

    def find_closest(
        self,
        feature_vec: dict[str, float],
        confidence: dict[str, float] | None = None,
        top_n: int = 3,
    ) -> list[tuple[str, float, dict[str, float]]]:
        results: list[tuple[str, float, dict[str, float]]] = []
        for preset in self._presets.values():
            if not preset.feature_vector:
                continue
            score, deltas = compute_similarity(feature_vec, preset.feature_vector, confidence)
            results.append((preset.name, score, deltas))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]

    def add(self, preset: StylePreset) -> None:
        self._presets[preset.name] = preset
        self._save_one(preset)

    def remove(self, name: str) -> None:
        if name in self._presets:
            del self._presets[name]
            path = os.path.join(self._dir, self._safe_filename(name))
            if os.path.exists(path):
                os.remove(path)

    def rename(self, old_name: str, new_name: str) -> None:
        preset = self._presets.pop(old_name, None)
        if preset:
            old_path = os.path.join(self._dir, self._safe_filename(old_name))
            if os.path.exists(old_path):
                os.remove(old_path)
            preset.name = new_name
            self._presets[new_name] = preset
            self._save_one(preset)

    def generate_name(self) -> str:
        idx = len(self._presets) + 1
        while True:
            name = f"StylePreset_{idx:05d}"
            if name not in self._presets:
                return name
            idx += 1

    def _save_one(self, preset: StylePreset) -> None:
        self._ensure_dir()
        path = os.path.join(self._dir, self._safe_filename(preset.name))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(preset.to_dict(), f, indent=2)

    def _safe_filename(self, name: str) -> str:
        safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
        return safe.strip() + ".json"
