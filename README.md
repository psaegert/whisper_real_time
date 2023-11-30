<h1 align="center" style="margin-top: 0px;">Real Time Whisper Transcription</h1>

![Demo gif](demo.gif)

This is a demo of real time speech to text with OpenAI's [Whisper](https://github.com/openai/whisper) model. It works by constantly recording audio in a thread and concatenating the raw bytes over multiple recordings.


# Requirements

## Software
- Python >=3.10
- `pip` >= [21.3](https://pip.pypa.io/en/stable/news/#v21-3)
- `portaudio19-dev`
- [`ffmpeg`](https://ffmpeg.org/)


# Getting Started
## 1. Clone the repository

```sh
git clone https://github.com/psaegert/whisper_real_time
cd whisper_real_time
```

## 2. Install the package

### Optional: Create a virtual environment:

**conda:**

```sh
conda create -n wrt python=3.11
conda activate wrt
```

**venv:**

```bash
python3 -m venv wrt_venv
source wrt_venv/bin/activate
```

### Install the dependencies:

```sh
sudo apt-get install portaudio19-dev
```

### Install the package:

```sh
pip install -e .
```

## 3. Run the transcription

To start the chat interface, run

```sh
wrt [-h] [-m {tiny,base,small,medium,large}] [-l LANGUAGE] [-e ENERGY_THRESHOLD] [-rt RECORD_TIMEOUT] [-pt PHRASE_TIMEOUT] [--default_microphone DEFAULT_MICROPHONE]
```

and start asking questions!


# Development

## Setup
To set up the development environment, run

```
pip install -e .[dev]
pre-commit install
```