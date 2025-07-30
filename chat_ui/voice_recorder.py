import sounddevice as sd
import numpy as np
import queue
import threading
import webrtcvad
from faster_whisper import WhisperModel
import time

# === Voice Recorder Class
class VoiceRecorder:
    def __init__(self, model_name="base", silence_duration=4.0, aggressiveness=3):
        # 🎙️ Audio capture config
        self.sample_rate = 16000
        self.block_duration = 30  # ms per audio block
        self.block_size = int(self.sample_rate * self.block_duration / 1000)

        # === Voice Activity Detection
        self.vad = webrtcvad.Vad(aggressiveness)

        # === Streaming state
        self.audio_queue = queue.Queue()
        self.recording = False
        self.model = WhisperModel(model_name, compute_type="int8", device="cpu")

        # === Silence and timeout control
        self.silence_duration = silence_duration
        self._last_voice_time = time.time()
        self.continuous_mode = True
        self.status_callback = None
        self.max_empty_loops = 3

    # === Audio callback
    # ✅ Captures microphone input and queues it for processing
    def _callback(self, indata, frames, time_info, status):
        if status:
            print("Status:", status)
        audio_data = indata[:, 0]
        self.audio_queue.put(audio_data.copy())

    # === Speech Detection
    # ✅ Checks if an audio chunk contains speech
    def _is_speech(self, chunk):
        pcm = (chunk * 32768).astype(np.int16).tobytes()
        return self.vad.is_speech(pcm, self.sample_rate)

    # === Recording Loop
    # ✅ Records audio until silence is detected
    def _record_until_silence(self):
        if self.status_callback:
            self.status_callback("Listening...")

        audio = []
        with sd.InputStream(
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            dtype="float32",
            callback=self._callback
        ):
            self._last_voice_time = time.time()
            while self.recording:
                try:
                    block = self.audio_queue.get(timeout=1)
                except queue.Empty:
                    continue

                audio.append(block)

                if self._is_speech(block):
                    self._last_voice_time = time.time()
                elif time.time() - self._last_voice_time > self.silence_duration:
                    print(f"⏹️ Silence detected — stopping chunk after {time.time() - self._last_voice_time:.2f}s")
                    break

        return np.concatenate(audio)

    # === Transcription
    # ✅ Uses Whisper model to convert recorded audio to text
    def _transcribe(self, audio):
        if self.status_callback:
            self.status_callback("Transcribing...")
        print("🧠 Transcribing...")

        segments, _ = self.model.transcribe(audio, language="en")
        full_text = " ".join(segment.text for segment in segments)
        print("📝 Transcript:", full_text)
        return full_text

    # === Main Loop
    # ✅ Records → Transcribes → Sends text back via callback
    def _run_loop(self, callback):
        empty_count = 0
        while self.recording:
            audio = self._record_until_silence()
            if not self.recording:
                break

            transcript = self._transcribe(audio).strip()
            if transcript:
                empty_count = 0
                callback(transcript)
            else:
                empty_count += 1
                print(f"⚠️ Skipped empty transcript. ({empty_count}/{self.max_empty_loops})")
                if self.status_callback:
                    self.status_callback(f"Silent ({empty_count}/{self.max_empty_loops})")

            if empty_count >= self.max_empty_loops:
                print("🛑 Auto-stopping after too many silent loops.")
                if self.status_callback:
                    self.status_callback("Stopped.")
                self.stop()
                return

            if not self.continuous_mode:
                break

        self.recording = False
        if self.status_callback:
            self.status_callback("Stopped.")
        print("🛑 VoiceRecorder stopped")

    # === Start Recording
    # ✅ Launches voice recorder in a background thread
    def start_recording_async(self, callback, on_status=None):
        if self.recording:
            print("⚠️ Already recording. Ignored.")
            return

        self.recording = True
        self.status_callback = on_status
        thread = threading.Thread(target=self._run_loop, args=(callback,), daemon=True)
        thread.start()

    # === Stop Recording
    # ✅ Manually stops recording and transcription
    def stop(self):
        print("⏹️ Manual stop called")
        self.recording = False
