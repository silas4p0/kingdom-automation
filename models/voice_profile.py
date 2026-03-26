import json
import os
from typing import Any


class VoiceProfile:
    def __init__(self, profile_id: str, name: str) -> None:
        self.profile_id = profile_id
        self.name = name
        self.description: str = ""
        self.embedding_path: str = ""
        self.sample_rate: int = 44100
        self.language: str = "en"
        self.tags: list[str] = []
        self.training_status: str = "untrained"

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "description": self.description,
            "embedding_path": self.embedding_path,
            "sample_rate": self.sample_rate,
            "language": self.language,
            "tags": self.tags,
            "training_status": self.training_status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VoiceProfile":
        p = cls(data["profile_id"], data["name"])
        p.description = data.get("description", "")
        p.embedding_path = data.get("embedding_path", "")
        p.sample_rate = data.get("sample_rate", 44100)
        p.language = data.get("language", "en")
        p.tags = data.get("tags", [])
        p.training_status = data.get("training_status", "untrained")
        return p


class VoiceModelManager:
    def __init__(self, storage_dir: str = "") -> None:
        self._profiles: dict[str, VoiceProfile] = {}
        self._active_id: str = ""
        self._storage_dir = storage_dir
        self._init_defaults()

    def _init_defaults(self) -> None:
        defaults = [
            ("default", "Default Singer", "Built-in default voice profile"),
            ("singer_a", "Singer A", "Warm vocal tone"),
            ("singer_b", "Singer B", "Bright vocal tone"),
            ("singer_c", "Singer C", "Deep vocal tone"),
        ]
        for pid, name, desc in defaults:
            p = VoiceProfile(pid, name)
            p.description = desc
            p.training_status = "stub"
            self._profiles[pid] = p
        self._active_id = "default"

    @property
    def active_profile(self) -> VoiceProfile | None:
        return self._profiles.get(self._active_id)

    @property
    def active_id(self) -> str:
        return self._active_id

    def list_profiles(self) -> list[VoiceProfile]:
        return list(self._profiles.values())

    def profile_names(self) -> list[str]:
        return [p.name for p in self._profiles.values()]

    def get_profile(self, profile_id: str) -> VoiceProfile | None:
        return self._profiles.get(profile_id)

    def get_profile_by_name(self, name: str) -> VoiceProfile | None:
        for p in self._profiles.values():
            if p.name == name:
                return p
        return None

    def register_profile(self, profile: VoiceProfile) -> None:
        self._profiles[profile.profile_id] = profile

    def remove_profile(self, profile_id: str) -> bool:
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            if self._active_id == profile_id:
                self._active_id = next(iter(self._profiles), "")
            return True
        return False

    def switch_profile(self, profile_id: str) -> bool:
        if profile_id in self._profiles:
            self._active_id = profile_id
            return True
        return False

    def switch_by_name(self, name: str) -> bool:
        p = self.get_profile_by_name(name)
        if p:
            self._active_id = p.profile_id
            return True
        return False

    def save_metadata(self, path: str) -> None:
        data = {
            "active_id": self._active_id,
            "profiles": {k: v.to_dict() for k, v in self._profiles.items()},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_metadata(self, path: str) -> None:
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._profiles.clear()
        for pid, pdata in data.get("profiles", {}).items():
            self._profiles[pid] = VoiceProfile.from_dict(pdata)
        self._active_id = data.get("active_id", "")
        if self._active_id not in self._profiles and self._profiles:
            self._active_id = next(iter(self._profiles))

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_id": self._active_id,
            "profiles": {k: v.to_dict() for k, v in self._profiles.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VoiceModelManager":
        mgr = cls.__new__(cls)
        mgr._profiles = {}
        mgr._storage_dir = ""
        for pid, pdata in data.get("profiles", {}).items():
            mgr._profiles[pid] = VoiceProfile.from_dict(pdata)
        mgr._active_id = data.get("active_id", "")
        if not mgr._profiles:
            mgr._init_defaults()
        return mgr

    def request_training(self, profile_id: str) -> str:
        p = self._profiles.get(profile_id)
        if not p:
            return "Profile not found"
        p.training_status = "queued"
        return f"Training queued for '{p.name}' (placeholder — no real training)"

    def load_embedding(self, profile_id: str) -> bytes:
        return b""
