import argparse
import os
import sys
from datetime import datetime, timedelta
from queue import Empty, Queue
from time import sleep

import numpy as np
import speech_recognition as sr
import torch
import whisper


def get_transcriptions_dir(*args: str) -> str:
    """
    Get the path to the data directory.

    Parameters
    ----------
    args : str
        The path to the data directory.

    Returns
    -------
    str
        The path to the data directory.s
    """
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', '..', 'transcriptions', *args), exist_ok=True)

    return os.path.join(os.path.dirname(__file__), '..', '..', 'transcriptions', *args)


def clear_console() -> None:
    """Clear the console in a cross-platform way."""
    os.system('cls' if os.name == 'nt' else 'clear')


def initialize_microphone(args: argparse.Namespace) -> sr.Microphone:
    """Initialize and return the microphone source."""
    if 'linux' in sys.platform and args.default_microphone == 'list':
        print("Available microphone devices are: ")
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f"{index}: Microphone with name \"{name}\" found")
        sys.exit(0)

    mic_index = None
    if 'linux' in sys.platform:
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            if args.default_microphone in name:
                mic_index = index
                break

    if mic_index is not None:
        return sr.Microphone(sample_rate=16000, device_index=mic_index)
    else:
        return sr.Microphone(sample_rate=16000)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", default="medium", help="Model to use", choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("-l", "--language", default="en", help="Language to use")
    parser.add_argument("-e", "--energy_threshold", default=1000, type=int, help="Energy level for mic to detect.")
    parser.add_argument("-rt", "--record_timeout", default=2, type=float, help="How real time the recording is in seconds.")
    parser.add_argument("-pt", "--phrase_timeout", default=3, type=float, help="Pause length before considering it a new phrase.")
    if 'linux' in sys.platform:
        parser.add_argument("--default_microphone", default='pulse', help="Default microphone name for SpeechRecognition.")
    return parser.parse_args()


def load_whisper_model(args: argparse.Namespace) -> whisper.Whisper:
    """Load and return the Whisper model based on the arguments."""
    model_name = args.model if args.language == "any" else f"{args.model}.{args.language}"
    return whisper.load_model(model_name)


def transcribe_audio(args: argparse.Namespace, model: whisper.Whisper, source: sr.Microphone, recorder: sr.Recognizer) -> None:
    """Transcribe audio from the microphone source using the Whisper model."""
    data_queue: Queue[bytes] = Queue()
    transcription = ['']
    phrase_time = None

    def record_callback(recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
        """Callback function to receive audio data."""
        data_queue.put(audio.get_raw_data())

    recorder.listen_in_background(source, record_callback, phrase_time_limit=args.record_timeout)
    print("Recording started. Press Ctrl+C to stop.")

    try:
        while True:
            try:
                audio_data = data_queue.get(timeout=args.phrase_timeout)
                now = datetime.utcnow()
                phrase_complete = False
                if phrase_time and now - phrase_time > timedelta(seconds=args.phrase_timeout):
                    phrase_complete = True
                phrase_time = now

                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                result = model.transcribe(audio_np, fp16=torch.cuda.is_available())
                text = result['text'].strip()

                if phrase_complete:
                    transcription.append(text)
                else:
                    transcription[-1] += " " + text

                clear_console()
                for line in transcription:
                    print(line)

            except Empty:
                sleep(0.1)  # Short sleep to reduce CPU usage
    except KeyboardInterrupt:
        print("\n\nTranscription:")
        for line in transcription:
            print(line)
