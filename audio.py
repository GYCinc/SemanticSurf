#!/usr/bin/env python3
import pyaudio
import numpy as np
import logging
import wave # <-- ADDED FOR .WAV SAVING

logger = logging.getLogger(__name__)

class MonoMicrophoneStream:
    """
    Custom microphone stream that converts multi-channel to mono
    AND saves the mono stream to a .wav file.
    """

    def __init__(self, sample_rate=16000, device_index=6, chunk_size=8000, channel_indices=None, output_filename=None): # <-- NEW param
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.chunk_size = chunk_size
        self.channel_indices = channel_indices
        self.p = pyaudio.PyAudio()

        # Get device info
        device_info = self.p.get_device_info_by_index(device_index)
        self.input_channels = int(device_info['maxInputChannels'])

        logger.info(f"🎤 Audio device: {device_info['name']}")
        logger.info(f"📊 Input channels: {self.input_channels}")

        if self.input_channels == 0:
            logger.error(f"❌ Device {device_index} has no input channels!")
            logger.error(f"💡 Run 'python check_audio.py' to find the correct device")
            raise ValueError(f"Device {device_index} ({device_info['name']}) has no input channels")

        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.input_channels,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk_size
        )

        # --- NEW: .wav file setup ---
        self.output_filename = output_filename
        self.wave_file = None
        if self.output_filename:
            try:
                self.wave_file = wave.open(self.output_filename, 'wb')
                self.wave_file.setnchannels(1) # We are saving the mono mix
                self.wave_file.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                self.wave_file.setframerate(self.sample_rate)
                logger.info(f"🎧 Recording audio to {self.output_filename}")
            except Exception as e:
                logger.error(f"Failed to open wave file {self.output_filename}: {e}")
                self.wave_file = None # Ensure it's None if setup fails
        # --- END NEW ---

    def __iter__(self):
        return self

    def __next__(self):
        data = self.stream.read(self.chunk_size, exception_on_overflow=False)

        # Convert to numpy array
        audio_data = np.frombuffer(data, dtype=np.int16)

        # If multi-channel, select specific channels or average them
        if self.input_channels > 1:
            audio_data = audio_data.reshape(-1, self.input_channels)
            if self.channel_indices:
                # Select and average the specified channels
                valid_indices = [i for i in self.channel_indices if 0 <= i < self.input_channels]
                if valid_indices:
                    selected_channels = audio_data[:, valid_indices]
                    audio_data = np.mean(selected_channels, axis=1).astype(np.int16)
                else:
                    # If no valid channels are selected, default to averaging all channels
                    logger.warning("Invalid channel_indices, averaging all channels.")
                    audio_data = audio_data.mean(axis=1).astype(np.int16)
            else:
                # Default to averaging all channels
                audio_data = audio_data.mean(axis=1).astype(np.int16)

        mono_bytes = audio_data.tobytes()

        # --- NEW: Write to .wav file ---
        if self.wave_file:
            try:
                self.wave_file.writeframes(mono_bytes)
            except Exception as e:
                logger.error(f"Failed to write to wave file: {e}")
                self.wave_file.close()
                self.wave_file = None # Stop trying to write
        # --- END NEW ---

        return mono_bytes

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

        # --- NEW: Close the .wav file ---
        if self.wave_file:
            try:
                self.wave_file.close()
                logger.info(f"✅ Audio save complete: {self.output_filename}")
            except Exception as e:
                logger.error(f"Failed to close wave file: {e}")
        # --- END NEW ---
