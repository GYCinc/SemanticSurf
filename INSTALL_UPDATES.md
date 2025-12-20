# Required System and Python Updates

To fully enable the enhanced audio pipeline (Live + High-Definition Post-Processing), please install the following updates.

## 1. System Dependencies (macOS)
The `pyaudio` library requires the `portaudio` system header files to compile correctly.

```bash
brew install portaudio
```

*(If you don't have Homebrew installed, visit https://brew.sh/)*

## 2. Python Dependencies
The enhanced pipeline adds `nltk` for POS tagging and `textblob` for advanced metrics, alongside `pyaudio` for audio capture.

```bash
source venv/bin/activate  # Make sure your virtualenv is active
pip install pyaudio nltk textblob assemblyai httpx python-dotenv
```

## 3. NLTK Data (One-Time Setup)
The Natural Language Toolkit needs specific data packs (Corpora) to function.

```bash
python3 -m nltk.downloader punkt averaged_perceptron_tagger brown wordnet
```
