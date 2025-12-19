import assemblyai as aai
try:
    print(f"Version: {aai.__version__}")
    print(f"SpeechUnderstandingConfig exists: {hasattr(aai, 'SpeechUnderstandingConfig')}")
    print(f"SpeakerIdentificationConfig exists: {hasattr(aai, 'SpeakerIdentificationConfig')}")
except Exception as e:
    print(e)
