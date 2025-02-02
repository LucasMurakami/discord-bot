from vosk import Model, KaldiRecognizer
import pyaudio 

# model = Model("e:/Vosk - Speech Recognition/vosk-model-pt-fb")
model = Model("E:/Vosk - Speech Recognition/vosk-model-small-pt-0.3")
recognizer = KaldiRecognizer(model, 16000)

cap = pyaudio.PyAudio()
stream = cap.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

while True:
    data = stream.read(8000)
    if len(data) == 0:
        break
    if recognizer.AcceptWaveform(data):
        print(recognizer.Result())

