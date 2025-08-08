import pyaudio
import wave
import os

class AudioAlerts:
    def __init__(self):
        self.audio_path = "assets/sounds/alert.wav"
    
    def play_alert(self):
        if os.path.exists(self.audio_path):
            wf = wave.open(self.audio_path, 'rb')
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                           channels=wf.getnchannels(),
                           rate=wf.getframerate(),
                           output=True)
            data = wf.readframes(1024)
            while data:
                stream.write(data)
                data = wf.readframes(1024)
            stream.stop_stream()
            stream.close()
            p.terminate()