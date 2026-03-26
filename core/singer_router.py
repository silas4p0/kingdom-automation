from typing import Any
from models.voice_profile import VoiceModelManager
from engines.preview_engine import PreviewEngine, PreviewQuality


class SingerRouter:
    def __init__(self, voice_manager: VoiceModelManager,
                 preview_engine: PreviewEngine) -> None:
        self._voice_manager = voice_manager
        self._preview_engine = preview_engine
        self._render_mode: str = "A Convert (Guide \u2192 Voice)"
        self._personality: str = "Neutral"
        self._personality_mix: int = 50

    @property
    def voice_manager(self) -> VoiceModelManager:
        return self._voice_manager

    @property
    def preview_engine(self) -> PreviewEngine:
        return self._preview_engine

    @property
    def render_mode(self) -> str:
        return self._render_mode

    def set_render_mode(self, mode: str) -> None:
        self._render_mode = mode

    def set_singer_by_name(self, name: str) -> bool:
        switched = self._voice_manager.switch_by_name(name)
        if switched:
            profile = self._voice_manager.active_profile
            if profile:
                self._preview_engine.set_voice_profile(profile.profile_id)
                self._preview_engine.invalidate_cache()
        return switched

    def set_personality(self, personality: str) -> None:
        self._personality = personality

    def set_personality_mix(self, mix: int) -> None:
        self._personality_mix = max(0, min(100, mix))

    def set_quality(self, quality_name: str) -> None:
        self._preview_engine.set_quality_by_name(quality_name)

    def trigger_preview(self, token_data: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(token_data)
        enriched["personality"] = self._personality
        enriched["personality_mix"] = self._personality_mix
        enriched["render_mode"] = self._render_mode

        result = self._preview_engine.preview_token(enriched)
        return {
            "duration_ms": result.duration_ms,
            "quality": result.quality.value,
            "cached": result.cached,
            "has_audio": result.is_valid(),
        }

    def get_active_singer_name(self) -> str:
        p = self._voice_manager.active_profile
        return p.name if p else ""

    def get_singer_names(self) -> list[str]:
        return self._voice_manager.profile_names()

    def to_dict(self) -> dict[str, Any]:
        return {
            "render_mode": self._render_mode,
            "personality": self._personality,
            "personality_mix": self._personality_mix,
            "voice_manager": self._voice_manager.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SingerRouter":
        vm = VoiceModelManager.from_dict(data.get("voice_manager", {}))
        pe = PreviewEngine()
        router = cls(vm, pe)
        router._render_mode = data.get("render_mode", "A Convert (Guide \u2192 Voice)")
        router._personality = data.get("personality", "Neutral")
        router._personality_mix = data.get("personality_mix", 50)
        if vm.active_profile:
            pe.set_voice_profile(vm.active_profile.profile_id)
        return router
