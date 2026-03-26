import uuid
from enum import Enum
from typing import Any


class RenderTarget(Enum):
    MASTER = "Master"
    TRACK = "Track"


class RenderStatus(Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    DONE = "Done"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class RenderJob:
    def __init__(
        self,
        target: RenderTarget,
        track_id: str = "",
        track_name: str = "",
        token_start: int = 0,
        token_end: int = -1,
        engine: str = "PreviewSynth",
        output_path: str = "",
        job_id: str | None = None,
    ) -> None:
        self.id: str = job_id or uuid.uuid4().hex[:12]
        self.target: RenderTarget = target
        self.track_id: str = track_id
        self.track_name: str = track_name
        self.token_start: int = token_start
        self.token_end: int = token_end
        self.engine: str = engine
        self.output_path: str = output_path
        self.status: RenderStatus = RenderStatus.PENDING
        self.error: str = ""

    def label(self) -> str:
        if self.target == RenderTarget.MASTER:
            rng = f"[{self.token_start}-{self.token_end}]" if self.token_end >= 0 else "[all]"
            return f"Master {rng}"
        return f"{self.track_name} [{self.token_start}-{self.token_end}]"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "target": self.target.value,
            "track_id": self.track_id,
            "track_name": self.track_name,
            "token_start": self.token_start,
            "token_end": self.token_end,
            "engine": self.engine,
            "output_path": self.output_path,
            "status": self.status.value,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RenderJob":
        j = cls(
            target=RenderTarget(data["target"]),
            track_id=data.get("track_id", ""),
            track_name=data.get("track_name", ""),
            token_start=data.get("token_start", 0),
            token_end=data.get("token_end", -1),
            engine=data.get("engine", "PreviewSynth"),
            output_path=data.get("output_path", ""),
            job_id=data.get("id"),
        )
        j.status = RenderStatus(data.get("status", "Pending"))
        j.error = data.get("error", "")
        return j
