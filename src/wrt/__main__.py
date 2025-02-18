import argparse
import os
from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from typing import Any

import numpy as np
import speech_recognition as sr
import torch
import whisper


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", default="medium", help="Model to use", choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("-l", "--language", default="en", help="Language to use")
    parser.add_argument("-e", "--energy_threshold", default=None, help="Energy level for mic to detect.", type=int)
    parser.add_argument("-rt", "--record_timeout", default=2, help="How real time the recording is in seconds.", type=float)
    parser.add_argument("-pt", "--phrase_timeout", default=3, help="How much empty space between recordings before we consider it a new line in the transcription.", type=float)
    args = parser.parse_args()

    # The last time a recording was retrieved from the queue.
    phrase_time = None
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue: Queue = Queue(maxsize=0)
    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
    recorder.dynamic_energy_threshold = False

    # Important for linux users.
    # Prevents permanent application hang and crash by using the wrong Microphone
    source = None

    print("Available microphone devices are: ")
    for id, name in sr.Microphone.list_working_microphones().items():
        print(f"{id:<2}: {name}")
    print()

    # Get the id of the microphone we want to use.
    mic_id = input("Enter the id of the microphone you want to use: ")

    mic_name = sr.Microphone.list_microphone_names()[int(mic_id)]

    if not mic_name or mic_name == 'list':
        print("Available microphone devices are: ")
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f"Microphone with name \"{name}\" found")
        return
    else:
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            if mic_name in name:
                source = sr.Microphone(sample_rate=16000, device_index=index)
                break

    if source is None:
        print("No microphone found, exiting.")
        return

    # Print the microphone we're using.
    print(f"Using microphone \"{mic_name}\"")

    # Load / Download model
    model = args.model
    if args.model != "large" and args.language != "any":
        model = model + "." + args.language
    audio_model = whisper.load_model(model)

    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout

    transcription = ['']

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_: Any, audio: sr.AudioData) -> None:
        """
        Threaded callback function to receive audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        data_queue.put(data)

    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

    # Cue the user that we're ready to go.
    print("Model loaded.\n")

    while True:
        try:
            now = datetime.utcnow()
            # Pull raw recorded audio from the queue.
            if not data_queue.empty():
                phrase_complete = False
                # If enough time has passed between recordings, consider the phrase complete.
                # Clear the current working audio buffer to start over with the new data.
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    phrase_complete = True
                # This is the last time we received new audio data from the queue.
                phrase_time = now

                # Combine audio data from queue
                audio_data = b''.join(data_queue.queue)
                data_queue.queue.clear()

                # Convert in-ram buffer to something the model can use directly without needing a temp file.
                # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
                # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
                try:
                    # Convert in-ram buffer to something the model can use directly without needing a temp file.
                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                    # Read the transcription.
                    result = audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                    text = result['text'].strip()
                    print("Transcription result:", text)  # Log transcription result

                    # Rest of your code...
                except Exception as e:
                    print("Error during transcription:", e)  # Log any errors

                # If we detected a pause between recordings, add a new item to our transcription.
                # Otherwise edit the existing one.
                if phrase_complete:
                    transcription.append(text)
                else:
                    transcription[-1] = text

                # Clear the console to reprint the updated transcription.
                os.system('cls' if os.name == 'nt' else 'clear')
                for line in transcription:
                    print(line)
                # Flush stdout.
                print('', end='', flush=True)

                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            break

    print("\n\nTranscription:")
    for line in transcription:
        print(line)


if __name__ == "__main__":
    main()
