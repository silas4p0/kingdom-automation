import json
import math
import os
import time
from typing import Any

FORMAT_VERSION = 1

EMOTIONAL_TONES = [
    "loving",
    "compassionate",
    "reverent",
    "sorrowful",
    "joyful",
    "triumphant",
    "warlike",
    "prophetic",
]


class ReferenceTemplate:
    def __init__(self, name: str = "") -> None:
        self.name: str = name
        self.created_at: float = time.time()
        self.source_audio: str = ""
        self.reference_mode: str = "Master Mix"
        self.template_family: str = ""
        self.emotional_tone: str = "reverent"
        self.tempo_estimate: float = 120.0
        self.phrase_count: int = 0
        self.line_count: int = 0
        self.word_count: int = 0
        self.duration_distribution: dict[str, float] = {
            "mean_ms": 500.0,
            "std_ms": 100.0,
            "min_ms": 100.0,
            "max_ms": 2000.0,
        }
        self.loudness_envelope: dict[str, float] = {
            "mean_rms": 0.0,
            "peak_rms": 0.0,
            "dynamic_range_db": 0.0,
        }
        self.pitch_contour: dict[str, float] = {
            "median_hz": 0.0,
            "mean_st": 0.0,
            "std_st": 0.0,
            "range_st": 0.0,
        }
        self.vibrato_behavior: dict[str, float] = {
            "mean_rate_hz": 0.0,
            "mean_depth_cents": 0.0,
            "presence_ratio": 0.0,
        }
        self.delivery_tendencies: dict[str, float] = {
            "Whisper": 0.0,
            "Normal": 1.0,
            "Yell": 0.0,
            "Scream": 0.0,
            "Bravado": 0.0,
        }
        self.intensity_distribution: dict[str, float] = {
            "mean": 50.0,
            "std": 10.0,
            "min": 0.0,
            "max": 100.0,
        }
        self.token_defaults: dict[str, Any] = {
            "duration_ms": 500,
            "loudness_pct": 100,
            "intensity": 50,
            "pitch_offset": 0,
            "delivery": "Normal",
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": FORMAT_VERSION,
            "name": self.name,
            "created_at": self.created_at,
            "source_audio": self.source_audio,
            "reference_mode": self.reference_mode,
            "template_family": self.template_family,
            "emotional_tone": self.emotional_tone,
            "tempo_estimate": round(self.tempo_estimate, 1),
            "phrase_count": self.phrase_count,
            "line_count": self.line_count,
            "word_count": self.word_count,
            "duration_distribution": self.duration_distribution,
            "loudness_envelope": self.loudness_envelope,
            "pitch_contour": self.pitch_contour,
            "vibrato_behavior": self.vibrato_behavior,
            "delivery_tendencies": self.delivery_tendencies,
            "intensity_distribution": self.intensity_distribution,
            "token_defaults": self.token_defaults,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReferenceTemplate":
        t = cls(data.get("name", ""))
        t.created_at = data.get("created_at", time.time())
        t.source_audio = data.get("source_audio", "")
        t.reference_mode = data.get("reference_mode", "Master Mix")
        t.template_family = data.get("template_family", "")
        t.emotional_tone = data.get("emotional_tone", "reverent")
        t.tempo_estimate = data.get("tempo_estimate", 120.0)
        t.phrase_count = data.get("phrase_count", 0)
        t.line_count = data.get("line_count", 0)
        t.word_count = data.get("word_count", 0)
        t.duration_distribution = data.get("duration_distribution", t.duration_distribution)
        t.loudness_envelope = data.get("loudness_envelope", t.loudness_envelope)
        t.pitch_contour = data.get("pitch_contour", t.pitch_contour)
        t.vibrato_behavior = data.get("vibrato_behavior", t.vibrato_behavior)
        t.delivery_tendencies = data.get("delivery_tendencies", t.delivery_tendencies)
        t.intensity_distribution = data.get("intensity_distribution", t.intensity_distribution)
        t.token_defaults = data.get("token_defaults", t.token_defaults)
        return t


class TemplateFamily:
    def __init__(self, name: str = "") -> None:
        self.name: str = name
        self.created_at: float = time.time()
        self.description: str = ""
        self.template_names: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "description": self.description,
            "template_names": list(self.template_names),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TemplateFamily":
        f = cls(data.get("name", ""))
        f.created_at = data.get("created_at", time.time())
        f.description = data.get("description", "")
        f.template_names = data.get("template_names", [])
        return f

    def compute_summary(self, templates: list[ReferenceTemplate]) -> dict[str, Any]:
        if not templates:
            return {}
        tempos = [t.tempo_estimate for t in templates if t.tempo_estimate > 0]
        intensities_mean = [t.intensity_distribution.get("mean", 50.0) for t in templates]
        intensities_std = [t.intensity_distribution.get("std", 10.0) for t in templates]
        delivery_sums: dict[str, float] = {}
        for t in templates:
            for key, val in t.delivery_tendencies.items():
                delivery_sums[key] = delivery_sums.get(key, 0.0) + val
        n = len(templates)
        delivery_avg = {k: round(v / n, 3) for k, v in delivery_sums.items()}
        tones = {}
        for t in templates:
            tone = t.emotional_tone
            tones[tone] = tones.get(tone, 0) + 1
        return {
            "template_count": n,
            "tempo_range": {
                "min": round(min(tempos), 1) if tempos else 0.0,
                "max": round(max(tempos), 1) if tempos else 0.0,
                "mean": round(sum(tempos) / len(tempos), 1) if tempos else 0.0,
            },
            "intensity_distribution": {
                "mean": round(sum(intensities_mean) / n, 1),
                "std": round(sum(intensities_std) / n, 1),
            },
            "delivery_tendencies": delivery_avg,
            "emotional_tones": tones,
        }


class TemplateFamilyStore:
    def __init__(self, store_dir: str = "") -> None:
        if not store_dir:
            store_dir = os.path.join(os.path.expanduser("~"), ".kds_lpe", "reference_templates")
        self._dir = store_dir
        self._templates: dict[str, ReferenceTemplate] = {}
        self._families: dict[str, TemplateFamily] = {}
        self._custom_tones: list[str] = []
        self._ensure_dir()
        self._load_all()

    def _ensure_dir(self) -> None:
        os.makedirs(self._dir, exist_ok=True)
        os.makedirs(os.path.join(self._dir, "templates"), exist_ok=True)
        os.makedirs(os.path.join(self._dir, "families"), exist_ok=True)

    def _load_all(self) -> None:
        tpl_dir = os.path.join(self._dir, "templates")
        if os.path.isdir(tpl_dir):
            for fname in sorted(os.listdir(tpl_dir)):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(tpl_dir, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                        tpl = ReferenceTemplate.from_dict(data)
                        self._templates[tpl.name] = tpl
                    except (json.JSONDecodeError, KeyError, OSError):
                        pass
        fam_dir = os.path.join(self._dir, "families")
        if os.path.isdir(fam_dir):
            for fname in sorted(os.listdir(fam_dir)):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(fam_dir, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                        fam = TemplateFamily.from_dict(data)
                        self._families[fam.name] = fam
                    except (json.JSONDecodeError, KeyError, OSError):
                        pass
        tones_path = os.path.join(self._dir, "custom_tones.json")
        if os.path.isfile(tones_path):
            try:
                with open(tones_path, "r", encoding="utf-8") as f:
                    self._custom_tones = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

    def _safe_filename(self, name: str) -> str:
        safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
        return safe.strip() + ".json"

    def list_template_names(self) -> list[str]:
        return sorted(self._templates.keys())

    def list_family_names(self) -> list[str]:
        return sorted(self._families.keys())

    def get_template(self, name: str) -> ReferenceTemplate | None:
        return self._templates.get(name)

    def get_family(self, name: str) -> TemplateFamily | None:
        return self._families.get(name)

    def all_templates(self) -> list[ReferenceTemplate]:
        return sorted(self._templates.values(), key=lambda t: t.created_at)

    def all_families(self) -> list[TemplateFamily]:
        return sorted(self._families.values(), key=lambda f: f.created_at)

    def add_template(self, tpl: ReferenceTemplate) -> None:
        self._templates[tpl.name] = tpl
        self._save_template(tpl)

    def remove_template(self, name: str) -> None:
        if name in self._templates:
            del self._templates[name]
            path = os.path.join(self._dir, "templates", self._safe_filename(name))
            if os.path.exists(path):
                os.remove(path)
            for fam in self._families.values():
                if name in fam.template_names:
                    fam.template_names.remove(name)
                    self._save_family(fam)

    def rename_template(self, old_name: str, new_name: str) -> None:
        tpl = self._templates.pop(old_name, None)
        if tpl:
            old_path = os.path.join(self._dir, "templates", self._safe_filename(old_name))
            if os.path.exists(old_path):
                os.remove(old_path)
            tpl.name = new_name
            self._templates[new_name] = tpl
            self._save_template(tpl)
            for fam in self._families.values():
                if old_name in fam.template_names:
                    idx = fam.template_names.index(old_name)
                    fam.template_names[idx] = new_name
                    self._save_family(fam)

    def add_family(self, fam: TemplateFamily) -> None:
        self._families[fam.name] = fam
        self._save_family(fam)

    def remove_family(self, name: str) -> None:
        if name in self._families:
            del self._families[name]
            path = os.path.join(self._dir, "families", self._safe_filename(name))
            if os.path.exists(path):
                os.remove(path)

    def assign_to_family(self, template_name: str, family_name: str) -> None:
        fam = self._families.get(family_name)
        if fam and template_name in self._templates:
            old_family = self._templates[template_name].template_family
            if old_family and old_family in self._families:
                old_fam = self._families[old_family]
                if template_name in old_fam.template_names:
                    old_fam.template_names.remove(template_name)
                    self._save_family(old_fam)
            if template_name not in fam.template_names:
                fam.template_names.append(template_name)
            self._templates[template_name].template_family = family_name
            self._save_family(fam)
            self._save_template(self._templates[template_name])

    def get_family_templates(self, family_name: str) -> list[ReferenceTemplate]:
        fam = self._families.get(family_name)
        if not fam:
            return []
        return [self._templates[n] for n in fam.template_names if n in self._templates]

    def get_family_summary(self, family_name: str) -> dict[str, Any]:
        fam = self._families.get(family_name)
        if not fam:
            return {}
        templates = self.get_family_templates(family_name)
        return fam.compute_summary(templates)

    def all_tones(self) -> list[str]:
        return EMOTIONAL_TONES + [t for t in self._custom_tones if t not in EMOTIONAL_TONES]

    def add_custom_tone(self, tone: str) -> None:
        if tone and tone not in EMOTIONAL_TONES and tone not in self._custom_tones:
            self._custom_tones.append(tone)
            self._save_custom_tones()

    def _save_template(self, tpl: ReferenceTemplate) -> None:
        self._ensure_dir()
        path = os.path.join(self._dir, "templates", self._safe_filename(tpl.name))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tpl.to_dict(), f, indent=2)

    def _save_family(self, fam: TemplateFamily) -> None:
        self._ensure_dir()
        path = os.path.join(self._dir, "families", self._safe_filename(fam.name))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(fam.to_dict(), f, indent=2)

    def _save_custom_tones(self) -> None:
        self._ensure_dir()
        path = os.path.join(self._dir, "custom_tones.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._custom_tones, f, indent=2)
