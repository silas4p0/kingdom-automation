import struct
import os
import tempfile
import threading
import time


class AudioRecorder:
    def __init__(self, sample_rate: int = 44100, max_duration_s: float = 5.0) -> None:
        self._sample_rate = sample_rate
        self._max_duration_s = max_duration_s
        self._recording = False
        self._samples: list[float] = []
        self._thread: threading.Thread | None = None
        self._last_wav_path: str = ""
        self._error: str = ""

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def last_wav_path(self) -> str:
        return self._last_wav_path

    @property
    def last_error(self) -> str:
        return self._error

    @property
    def max_duration_s(self) -> float:
        return self._max_duration_s

    @max_duration_s.setter
    def max_duration_s(self, val: float) -> None:
        self._max_duration_s = max(0.5, min(30.0, val))

    def start_recording(self) -> bool:
        if self._recording:
            return False
        self._error = ""
        self._samples = []
        self._recording = True
        self._thread = threading.Thread(target=self._record_thread, daemon=True)
        self._thread.start()
        return True

    def stop_recording(self) -> str:
        self._recording = False
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None

        if not self._samples:
            self._error = "No audio captured"
            return ""

        path = self._save_wav(self._samples)
        self._last_wav_path = path
        return path

    def _record_thread(self) -> None:
        try:
            self._record_with_pyaudio()
        except Exception:
            try:
                self._record_with_ossaudiodev()
            except Exception:
                self._record_stub()

    def _record_with_pyaudio(self) -> None:
        import pyaudio
        pa = pyaudio.PyAudio()
        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self._sample_rate,
                input=True,
                frames_per_buffer=1024,
            )
            max_frames = int(self._sample_rate * self._max_duration_s)
            collected = 0
            while self._recording and collected < max_frames:
                chunk_size = min(1024, max_frames - collected)
                data = stream.read(chunk_size, exception_on_overflow=False)
                for i in range(0, len(data), 2):
                    if i + 1 < len(data):
                        val = struct.unpack_from("<h", data, i)[0]
                        self._samples.append(val / 32768.0)
                collected += chunk_size
            stream.stop_stream()
            stream.close()
        finally:
            pa.terminate()

    def _record_with_ossaudiodev(self) -> None:
        import ossaudiodev
        dsp = ossaudiodev.open("/dev/dsp", "r")
        try:
            dsp.setfmt(ossaudiodev.AFMT_S16_LE)
            dsp.channels(1)
            dsp.speed(self._sample_rate)
            max_bytes = int(self._sample_rate * self._max_duration_s * 2)
            collected = 0
            while self._recording and collected < max_bytes:
                data = dsp.read(2048)
                for i in range(0, len(data), 2):
                    if i + 1 < len(data):
                        val = struct.unpack_from("<h", data, i)[0]
                        self._samples.append(val / 32768.0)
                collected += len(data)
        finally:
            dsp.close()

    def _record_stub(self) -> None:
        import math
        num_samples = int(self._sample_rate * min(self._max_duration_s, 2.0))
        freq = 220.0
        t = 0.0
        dt = 1.0 / self._sample_rate
        while self._recording and len(self._samples) < num_samples:
            val = 0.3 * math.sin(2.0 * math.pi * freq * t)
            val += 0.1 * math.sin(2.0 * math.pi * freq * 2.0 * t)
            val += 0.05 * math.sin(2.0 * math.pi * freq * 3.0 * t)
            env = 1.0
            progress = t / (num_samples / self._sample_rate)
            if progress < 0.05:
                env = progress / 0.05
            elif progress > 0.8:
                env = (1.0 - progress) / 0.2
            self._samples.append(val * env)
            t += dt
            time.sleep(dt * 0.5)
        self._error = "No audio input device found; generated stub tone"

    def _save_wav(self, samples: list[float]) -> str:
        tmp_dir = os.path.join(tempfile.gettempdir(), "kds_capture")
        os.makedirs(tmp_dir, exist_ok=True)
        path = os.path.join(tmp_dir, f"capture_{int(time.time())}.wav")

        num = len(samples)
        data_size = num * 2
        sr = self._sample_rate

        with open(path, "wb") as f:
            f.write(b"RIFF")
            f.write(struct.pack("<I", 36 + data_size))
            f.write(b"WAVE")
            f.write(b"fmt ")
            f.write(struct.pack("<I", 16))
            f.write(struct.pack("<HHI", 1, 1, sr))
            f.write(struct.pack("<IHH", sr * 2, 2, 16))
            f.write(b"data")
            f.write(struct.pack("<I", data_size))
            for s in samples:
                clamped = max(-1.0, min(1.0, s))
                f.write(struct.pack("<h", int(clamped * 32767)))

        return path

    @staticmethod
    def import_wav(path: str) -> str:
        if not os.path.isfile(path):
            return ""
        tmp_dir = os.path.join(tempfile.gettempdir(), "kds_capture")
        os.makedirs(tmp_dir, exist_ok=True)
        import shutil
        dest = os.path.join(tmp_dir, f"import_{int(time.time())}_{os.path.basename(path)}")
        shutil.copy2(path, dest)
        return dest
