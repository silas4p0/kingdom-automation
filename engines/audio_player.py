import os
import tempfile
import threading
import wave
from typing import Callable


class AudioPlayer:
    def __init__(self) -> None:
        self._last_wav_path: str = ""
        self._playing = False
        self._on_finished: Callable[[], None] | None = None

    @property
    def last_wav_path(self) -> str:
        return self._last_wav_path

    @property
    def is_playing(self) -> bool:
        return self._playing

    def set_on_finished(self, callback: Callable[[], None]) -> None:
        self._on_finished = callback

    def play_bytes(self, wav_data: bytes) -> bool:
        if not wav_data:
            return False
        cache_dir = os.path.join(tempfile.gettempdir(), "kds_preview_cache")
        os.makedirs(cache_dir, exist_ok=True)
        path = os.path.join(cache_dir, "_last_preview.wav")
        with open(path, "wb") as f:
            f.write(wav_data)
        self._last_wav_path = path
        return self._play_file(path)

    def replay_last(self) -> bool:
        if self._last_wav_path and os.path.exists(self._last_wav_path):
            return self._play_file(self._last_wav_path)
        return False

    def _play_file(self, path: str) -> bool:
        thread = threading.Thread(target=self._play_worker, args=(path,), daemon=True)
        thread.start()
        return True

    def _play_worker(self, path: str) -> None:
        self._playing = True
        try:
            self._play_with_ossaudiodev(path)
        except Exception:
            try:
                self._play_with_subprocess(path)
            except Exception:
                pass
        finally:
            self._playing = False
            if self._on_finished:
                self._on_finished()

    def _play_with_ossaudiodev(self, path: str) -> None:
        import ossaudiodev
        with wave.open(path, "rb") as wf:
            dsp = ossaudiodev.open("/dev/dsp", "w")
            try:
                dsp.setparameters(
                    ossaudiodev.AFMT_S16_LE,
                    wf.getnchannels(),
                    wf.getframerate(),
                )
                chunk = 1024
                data = wf.readframes(chunk)
                while data:
                    dsp.write(data)
                    data = wf.readframes(chunk)
            finally:
                dsp.close()

    def _play_with_subprocess(self, path: str) -> None:
        import subprocess
        import sys
        import shutil

        if sys.platform == "darwin":
            subprocess.run(["afplay", path], check=True,
                           capture_output=True, timeout=30)
        elif sys.platform == "win32":
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME)
        else:
            if shutil.which("aplay"):
                subprocess.run(["aplay", "-q", path], check=True,
                               capture_output=True, timeout=30)
            elif shutil.which("paplay"):
                subprocess.run(["paplay", path], check=True,
                               capture_output=True, timeout=30)
            elif shutil.which("ffplay"):
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                    check=True, capture_output=True, timeout=30,
                )
            else:
                raise RuntimeError("No audio player found")
