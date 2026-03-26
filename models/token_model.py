from enum import Enum
from typing import Any


class DeliveryMode(Enum):
    WHISPER = "Whisper"
    NORMAL = "Normal"
    YELL = "Yell"
    SCREAM = "Scream"
    BRAVADO = "Bravado"


class BravadoSubtype(Enum):
    CONFIDENT = "Confident"
    AGGRESSIVE = "Aggressive"
    TRIUMPHANT = "Triumphant"
    DEFIANT = "Defiant"


class BoundaryMarker(Enum):
    NORMAL = "Normal"
    HARD_STOP = "Hard Stop"
    POWERFUL_START = "Powerful Start"


class TokenModel:
    def __init__(self, word: str, index: int) -> None:
        self.word = word
        self.index = index
        self.duration_ms: int = 500
        self.loudness_pct: int = 100
        self.intensity: int = 50
        self.pitch_offset: int = 0
        self.delivery: DeliveryMode = DeliveryMode.NORMAL
        self.bravado_subtype: BravadoSubtype = BravadoSubtype.CONFIDENT
        self.boundary_after: BoundaryMarker = BoundaryMarker.NORMAL
        self.locked: bool = False
        self.line_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "word": self.word,
            "index": self.index,
            "duration_ms": self.duration_ms,
            "loudness_pct": self.loudness_pct,
            "intensity": self.intensity,
            "pitch_offset": self.pitch_offset,
            "delivery": self.delivery.value,
            "bravado_subtype": self.bravado_subtype.value,
            "boundary_after": self.boundary_after.value,
            "locked": self.locked,
            "line_index": self.line_index,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenModel":
        t = cls(data["word"], data["index"])
        t.duration_ms = data.get("duration_ms", 500)
        t.loudness_pct = data.get("loudness_pct", 100)
        t.intensity = data.get("intensity", 50)
        t.pitch_offset = data.get("pitch_offset", 0)
        t.delivery = DeliveryMode(data.get("delivery", "Normal"))
        t.bravado_subtype = BravadoSubtype(data.get("bravado_subtype", "Confident"))
        t.boundary_after = BoundaryMarker(data.get("boundary_after", "Normal"))
        t.locked = data.get("locked", False)
        t.line_index = data.get("line_index", 0)
        return t

    def copy_params_from(self, other: "TokenModel") -> None:
        self.duration_ms = other.duration_ms
        self.loudness_pct = other.loudness_pct
        self.intensity = other.intensity
        self.pitch_offset = other.pitch_offset
        self.delivery = other.delivery
        self.bravado_subtype = other.bravado_subtype
