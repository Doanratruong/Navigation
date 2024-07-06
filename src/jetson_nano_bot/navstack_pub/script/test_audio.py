#!/usr/bin/env python

import pyaudio
import wave
import audioop
import speech_recognition as sr
def record_audio(output_filename, record_seconds=10, format=pyaudio.paInt16, channels=1, rate=48000, chunk=1024, input_device_index=1):
    """
    Records audio from the specified input device and saves it to a file.

    Parameters:
    - output_filename: The name of the output file (e.g., 'output.wav').
    - record_seconds: Duration of the recording in seconds (default is 10).
    - format: Audio format (default is pyaudio.paInt16).
    - channels: Number of audio channels (default is 1 for mono).
    - rate: Sample rate in Hz (default is 48000).
    - chunk: Chunk size (default is 1024).
    - input_device_index: Index of the input device (default is 1).
    """

    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    # Open stream
    stream = audio.open(format=format, channels=channels,
                        rate=rate, input=True,
                        frames_per_buffer=chunk, input_device_index=input_device_index)

    print("Recording...")

    frames = []

    # Record audio in chunks
    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    print("Finished recording.")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded audio as a .wav file
    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))

    print(f"Audio recorded and saved as {output_filename}")

def wait_for_speech(threshold=500, chunk=1024, rate=48000, channels=1, format=pyaudio.paInt16, input_device_index=1):
    """
    Waits for speech to start by monitoring audio input.

    Parameters:
    - threshold: The RMS threshold for detecting speech.
    - chunk: Chunk size.
    - rate: Sample rate in Hz.
    - channels: Number of audio channels.
    - format: Audio format.
    - input_device_index: Index of the input device.
    """

    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    # Open stream
    stream = audio.open(format=format, channels=channels,
                        rate=rate, input=True,
                        frames_per_buffer=chunk, input_device_index=input_device_index)

    print("Waiting for speech...")

    while True:
        data = stream.read(chunk, exception_on_overflow=False)
        rms = audioop.rms(data, 2)  # Calculate RMS of the chunk

        if rms > threshold:
            print("Speech detected!")
            break

    stream.stop_stream()
    stream.close()
    audio.terminate()

def get_voice(output_filename="output.wav", record_seconds=10):
    global idle_flag
    
    # Wait for speech to start
    wait_for_speech()

    # Record audio
    record_audio(output_filename, record_seconds)

    # Initialize recognizer
    r = sr.Recognizer()

    # Load the recorded audio file
    with sr.AudioFile(output_filename) as source:
        print("Me: ", end='')
        audio = r.record(source)

        try:
            text = r.recognize_google(audio, language="vi-VN")
            print(text)
            idle_flag = True
            return text
        except sr.UnknownValueError:
            print("Could not understand audio")
            return 0
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return 0
            
# Example usage
if __name__ == "__main__":
    get_voice("output.wav", record_seconds=10)
