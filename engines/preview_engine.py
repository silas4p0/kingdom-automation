from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class PreviewQuality(Enum):
    FAST = "Fast"
    HIGH = "High"


class PreviewResult:
    def __init__(self) -> None:
        self.audio_data: bytes = b""
        self.duration_ms: int = 0
        self.quality: PreviewQuality = PreviewQuality.FAST
        self.cached: bool = False
        self.token_index: int = -1

    def is_valid(self) -> bool:
        return len(self.audio_data) > 0


class PreviewSynthesizer(ABC):
    @abstractmethod
    def synthesize_token(self, token_data: dict[str, Any],
                         voice_profile_id: str,
                         quality: PreviewQuality) -> PreviewResult:
        ...

    @abstractmethod
    def synthesize_phrase(self, tokens: list[dict[str, Any]],
                          voice_profile_id: str,
                          quality: PreviewQuality) -> PreviewResult:
        ...

    @abstractmethod
    def supports_quality(self, quality: PreviewQuality) -> bool:
        ...


class StubPreviewSynthesizer(PreviewSynthesizer):
    def synthesize_token(self, token_data: dict[str, Any],
                         voice_profile_id: str,
                         quality: PreviewQuality) -> PreviewResult:
        result = PreviewResult()
        result.quality = quality
        result.duration_ms = token_data.get("duration_ms", 500)
        result.token_index = token_data.get("index", -1)
        return result

    def synthesize_phrase(self, tokens: list[dict[str, Any]],
                          voice_profile_id: str,
                          quality: PreviewQuality) -> PreviewResult:
        result = PreviewResult()
        result.quality = quality
        result.duration_ms = sum(t.get("duration_ms", 500) for t in tokens)
        return result

    def supports_quality(self, quality: PreviewQuality) -> bool:
        return True


class PreviewCache:
    def __init__(self, max_entries: int = 200) -> None:
        self._cache: dict[str, PreviewResult] = {}
        self._max = max_entries

    def _make_key(self, token_index: int, voice_id: str,
                  quality: str, params_hash: str) -> str:
        return f"{token_index}:{voice_id}:{quality}:{params_hash}"

    def get(self, token_index: int, voice_id: str,
            quality: str, params_hash: str) -> PreviewResult | None:
        key = self._make_key(token_index, voice_id, quality, params_hash)
        result = self._cache.get(key)
        if result:
            result.cached = True
        return result

    def put(self, token_index: int, voice_id: str,
            quality: str, params_hash: str, result: PreviewResult) -> None:
        key = self._make_key(token_index, voice_id, quality, params_hash)
        if len(self._cache) >= self._max:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = result

    def clear(self) -> None:
        self._cache.clear()


class PreviewEngine:
    def __init__(self) -> None:
        self._synthesizer: PreviewSynthesizer = StubPreviewSynthesizer()
        self._cache = PreviewCache()
        self._quality = PreviewQuality.FAST
        self._voice_profile_id: str = "default"

    @property
    def quality(self) -> PreviewQuality:
        return self._quality

    def set_quality(self, quality: PreviewQuality) -> None:
        self._quality = quality

    def set_quality_by_name(self, name: str) -> None:
        for q in PreviewQuality:
            if q.value == name:
                self._quality = q
                return

    def set_voice_profile(self, profile_id: str) -> None:
        self._voice_profile_id = profile_id

    def set_synthesizer(self, synth: PreviewSynthesizer) -> None:
        self._synthesizer = synth
        self._cache.clear()

    def preview_token(self, token_data: dict[str, Any]) -> PreviewResult:
        params_hash = str(hash(frozenset(token_data.items())))
        cached = self._cache.get(
            token_data.get("index", -1),
            self._voice_profile_id,
            self._quality.value,
            params_hash,
        )
        if cached:
            return cached

        result = self._synthesizer.synthesize_token(
            token_data, self._voice_profile_id, self._quality
        )
        self._cache.put(
            token_data.get("index", -1),
            self._voice_profile_id,
            self._quality.value,
            params_hash,
            result,
        )
        return result

    def preview_phrase(self, tokens: list[dict[str, Any]]) -> PreviewResult:
        return self._synthesizer.synthesize_phrase(
            tokens, self._voice_profile_id, self._quality
        )

    def invalidate_cache(self) -> None:
        self._cache.clear()
