import json
import os
import time
from typing import Any

FORMAT_VERSION = 1

GLOBAL_INSTRUMENTS_DIR = os.path.join(
    os.path.expanduser("~"), ".kds_lpe", "instruments"
)


class InstrumentPatch:
    def __init__(self, name: str = "Default") -> None:
        self.name: str = name
        self.created_at: float = time.time()
        self.attack_ms: float = 2.0
        self.decay_ms: float = 40.0
        self.sustain_level: float = 0.05
        self.release_ms: float = 60.0
        self.damping: float = 0.5
        self.harmonics_level: float = 0.5
        self.lowpass_hz: float = 4000.0
        self.brightness: float = 0.5
        self.noise_amount: float = 0.0
        self.transient_click: float = 0.0
        self.default_duration_ms_min: int = 200
        self.default_duration_ms_max: int = 600
        self.default_intensity: int = 50
        self.default_delivery_mode: str = "Normal"
        self.default_vibrato_on: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": FORMAT_VERSION,
            "name": self.name,
            "created_at": self.created_at,
            "attack_ms": self.attack_ms,
            "decay_ms": self.decay_ms,
            "sustain_level": self.sustain_level,
            "release_ms": self.release_ms,
            "damping": self.damping,
            "harmonics_level": self.harmonics_level,
            "lowpass_hz": self.lowpass_hz,
            "brightness": self.brightness,
            "noise_amount": self.noise_amount,
            "transient_click": self.transient_click,
            "default_duration_ms_min": self.default_duration_ms_min,
            "default_duration_ms_max": self.default_duration_ms_max,
            "default_intensity": self.default_intensity,
            "default_delivery_mode": self.default_delivery_mode,
            "default_vibrato_on": self.default_vibrato_on,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstrumentPatch":
        p = cls(data.get("name", "Default"))
        p.created_at = data.get("created_at", time.time())
        p.attack_ms = data.get("attack_ms", 2.0)
        p.decay_ms = data.get("decay_ms", 40.0)
        p.sustain_level = data.get("sustain_level", 0.05)
        p.release_ms = data.get("release_ms", 60.0)
        p.damping = data.get("damping", 0.5)
        p.harmonics_level = data.get("harmonics_level", 0.5)
        p.lowpass_hz = data.get("lowpass_hz", 4000.0)
        p.brightness = data.get("brightness", 0.5)
        p.noise_amount = data.get("noise_amount", 0.0)
        p.transient_click = data.get("transient_click", 0.0)
        p.default_duration_ms_min = data.get("default_duration_ms_min", 200)
        p.default_duration_ms_max = data.get("default_duration_ms_max", 600)
        p.default_intensity = data.get("default_intensity", 50)
        p.default_delivery_mode = data.get("default_delivery_mode", "Normal")
        p.default_vibrato_on = data.get("default_vibrato_on", True)
        return p

    def clone(self, new_name: str = "") -> "InstrumentPatch":
        d = self.to_dict()
        d["name"] = new_name or f"{self.name} (Copy)"
        d["created_at"] = time.time()
        return InstrumentPatch.from_dict(d)


def build_default_instrument() -> InstrumentPatch:
    p = InstrumentPatch("Default Vocal")
    p.attack_ms = 25.0
    p.decay_ms = 100.0
    p.sustain_level = 0.8
    p.release_ms = 100.0
    p.damping = 0.2
    p.harmonics_level = 0.85
    p.lowpass_hz = 8000.0
    p.brightness = 0.6
    p.noise_amount = 0.03
    p.transient_click = 0.0
    p.default_duration_ms_min = 300
    p.default_duration_ms_max = 800
    p.default_intensity = 50
    p.default_delivery_mode = "Normal"
    p.default_vibrato_on = True
    return p


def build_palm_dusted_piano() -> InstrumentPatch:
    p = InstrumentPatch("Palm-Dusted Piano")
    p.attack_ms = 3.0
    p.decay_ms = 55.0
    p.sustain_level = 0.04
    p.release_ms = 45.0
    p.damping = 0.85
    p.harmonics_level = 0.2
    p.lowpass_hz = 1600.0
    p.brightness = 0.25
    p.noise_amount = 0.1
    p.transient_click = 0.35
    p.default_duration_ms_min = 80
    p.default_duration_ms_max = 220
    p.default_intensity = 65
    p.default_delivery_mode = "Normal"
    p.default_vibrato_on = False
    return p


BUILTIN_INSTRUMENTS: list[InstrumentPatch] = [
    build_default_instrument(),
    build_palm_dusted_piano(),
]


class InstrumentStore:
    def __init__(self, project_dir: str = "", global_dir: str = GLOBAL_INSTRUMENTS_DIR) -> None:
        self._global_dir = global_dir
        self._project_dir = project_dir
        self._instruments: dict[str, InstrumentPatch] = {}
        self._load_all()

    def _ensure_dir(self, d: str) -> None:
        if d:
            os.makedirs(d, exist_ok=True)

    def _load_all(self) -> None:
        self._instruments.clear()
        for bi in BUILTIN_INSTRUMENTS:
            self._instruments[bi.name] = InstrumentPatch.from_dict(bi.to_dict())

        self._ensure_dir(self._global_dir)
        self._load_from_dir(self._global_dir)

        if self._project_dir:
            self._ensure_dir(self._project_dir)
            self._load_from_dir(self._project_dir)

    def _load_from_dir(self, d: str) -> None:
        if not os.path.isdir(d):
            return
        for fname in sorted(os.listdir(d)):
            if fname.endswith(".json"):
                path = os.path.join(d, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    inst = InstrumentPatch.from_dict(data)
                    self._instruments[inst.name] = inst
                except (json.JSONDecodeError, KeyError, OSError):
                    pass

    def set_project_dir(self, d: str) -> None:
        self._project_dir = d
        self._load_all()

    def list_names(self) -> list[str]:
        return sorted(self._instruments.keys())

    def get(self, name: str) -> InstrumentPatch | None:
        return self._instruments.get(name)

    def add(self, inst: InstrumentPatch, to_project: bool = False) -> None:
        self._instruments[inst.name] = inst
        target_dir = self._project_dir if (to_project and self._project_dir) else self._global_dir
        self._save_one(inst, target_dir)

    def remove(self, name: str) -> None:
        builtin_names = {bi.name for bi in BUILTIN_INSTRUMENTS}
        if name in builtin_names:
            return
        if name in self._instruments:
            del self._instruments[name]
            for d in [self._global_dir, self._project_dir]:
                if d:
                    path = os.path.join(d, self._safe_filename(name))
                    if os.path.exists(path):
                        os.remove(path)

    def rename(self, old_name: str, new_name: str) -> None:
        inst = self._instruments.pop(old_name, None)
        if inst:
            for d in [self._global_dir, self._project_dir]:
                if d:
                    old_path = os.path.join(d, self._safe_filename(old_name))
                    if os.path.exists(old_path):
                        os.remove(old_path)
            inst.name = new_name
            self._instruments[new_name] = inst
            self._save_one(inst, self._global_dir)

    def _save_one(self, inst: InstrumentPatch, target_dir: str) -> None:
        self._ensure_dir(target_dir)
        path = os.path.join(target_dir, self._safe_filename(inst.name))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(inst.to_dict(), f, indent=2)

    def _safe_filename(self, name: str) -> str:
        safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
        return safe.strip() + ".json"
