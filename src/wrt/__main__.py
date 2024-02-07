import speech_recognition as sr

from .utils import initialize_microphone, load_whisper_model, parse_arguments, transcribe_audio


def main() -> None:
    args = parse_arguments()
    source = initialize_microphone(args)
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    recorder.dynamic_energy_threshold = False

    with source:
        recorder.adjust_for_ambient_noise(source)

    model = load_whisper_model(args)
    transcribe_audio(args, model, source, recorder)


if __name__ == "__main__":
    main()
