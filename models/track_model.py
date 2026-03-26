import uuid
from enum import Enum
from typing import Any


class TrackType(Enum):
    VOCAL = "VOCAL"
    INSTRUMENT = "INSTRUMENT"
    MASTER = "MASTER"


class TrackAssignment:
    def __init__(self, track_id: str, start_index: int, end_index: int,
                 notes: str = "") -> None:
        self.track_id = track_id
        self.start_index = start_index
        self.end_index = end_index
        self.notes = notes

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrackAssignment":
        return cls(
            track_id=data["track_id"],
            start_index=data["start_index"],
            end_index=data["end_index"],
            notes=data.get("notes", ""),
        )


class TrackModel:
    def __init__(self, name: str, track_type: TrackType,
                 track_id: str | None = None) -> None:
        self.id: str = track_id or uuid.uuid4().hex[:12]
        self.name: str = name
        self.track_type: TrackType = track_type
        self.voice_profile_id: str = ""
        self.enabled: bool = True
        self.solo: bool = False
        self.color: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "track_type": self.track_type.value,
            "voice_profile_id": self.voice_profile_id,
            "enabled": self.enabled,
            "solo": self.solo,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrackModel":
        t = cls(
            name=data["name"],
            track_type=TrackType(data["track_type"]),
            track_id=data.get("id"),
        )
        t.voice_profile_id = data.get("voice_profile_id", "")
        t.enabled = data.get("enabled", True)
        t.solo = data.get("solo", False)
        t.color = data.get("color", "")
        return t


DEFAULT_TRACKS = [
    ("Vocal 1", TrackType.VOCAL),
    ("Vocal 2", TrackType.VOCAL),
    ("Instruments", TrackType.INSTRUMENT),
    ("Master", TrackType.MASTER),
]


def create_default_tracks() -> list[TrackModel]:
    return [TrackModel(name, ttype) for name, ttype in DEFAULT_TRACKS]
