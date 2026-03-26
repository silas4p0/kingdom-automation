import json
import os
from typing import Any
from .token_model import TokenModel
from .track_model import TrackModel, TrackAssignment, create_default_tracks

PROJECT_SUBDIRS = [
    "audio/captures",
    "audio/renders",
    "audio/imports",
    "audio/reference",
    "presets",
    "exports",
    "stems",
]


class ProjectModel:
    def __init__(self) -> None:
        self.lyrics: str = ""
        self.tokens: list[TokenModel] = []
        self.render_mode: str = "A Convert (Guide → Voice)"
        self.engine_quality: str = "Fast"
        self.auto_preview: bool = False
        self.singer: str = "Default Singer"
        self.personality: str = "Neutral"
        self.personality_mix: int = 50
        self.tempo: int = 120
        self.key: str = "C Major"
        self.theme: str = "dark"
        self.preview_mode: str = "Single"
        self.project_folder: str = ""
        self.folder_based: bool = True
        self.active_book: str = "Composition"
        self.tracks: list[TrackModel] = create_default_tracks()
        self.track_assignments: list[TrackAssignment] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "lyrics": self.lyrics,
            "tokens": [t.to_dict() for t in self.tokens],
            "render_mode": self.render_mode,
            "engine_quality": self.engine_quality,
            "auto_preview": self.auto_preview,
            "singer": self.singer,
            "personality": self.personality,
            "personality_mix": self.personality_mix,
            "tempo": self.tempo,
            "key": self.key,
            "theme": self.theme,
            "preview_mode": self.preview_mode,
            "project_folder": self.project_folder,
            "folder_based": self.folder_based,
            "active_book": self.active_book,
            "tracks":[t.to_dict() for t in self.tracks],
            "track_assignments": [a.to_dict() for a in self.track_assignments],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectModel":
        p = cls()
        p.lyrics = data.get("lyrics", "")
        p.tokens = [TokenModel.from_dict(td) for td in data.get("tokens", [])]
        p.render_mode = data.get("render_mode", "A Convert (Guide → Voice)")
        p.engine_quality = data.get("engine_quality", "Fast")
        p.auto_preview = data.get("auto_preview", False)
        p.singer = data.get("singer", "Default Singer")
        p.personality = data.get("personality", "Neutral")
        p.personality_mix = data.get("personality_mix", 50)
        p.tempo = data.get("tempo", 120)
        p.key = data.get("key", "C Major")
        p.theme = data.get("theme", "dark")
        p.preview_mode = data.get("preview_mode", "Single")
        p.project_folder = data.get("project_folder", "")
        p.folder_based = data.get("folder_based", True)
        p.active_book = data.get("active_book", "Composition")
        tracks_data= data.get("tracks")
        if tracks_data:
            p.tracks = [TrackModel.from_dict(td) for td in tracks_data]
        else:
            p.tracks = create_default_tracks()
        p.track_assignments = [
            TrackAssignment.from_dict(ad)
            for ad in data.get("track_assignments", [])
        ]
        return p

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "ProjectModel":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @staticmethod
    def create_project_folder(base_dir: str, name: str) -> str:
        folder = os.path.join(base_dir, name)
        os.makedirs(folder, exist_ok=True)
        for sub in PROJECT_SUBDIRS:
            os.makedirs(os.path.join(folder, sub), exist_ok=True)
        return folder
