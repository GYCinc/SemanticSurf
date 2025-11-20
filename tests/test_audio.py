import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audio import MonoMicrophoneStream

class TestMonoMicrophoneStream(unittest.TestCase):

    @patch('pyaudio.PyAudio')
    def test_mono_conversion(self, mock_pyaudio):
        """Test that multi-channel audio is correctly converted to mono."""
        # Arrange
        mock_audio = mock_pyaudio.return_value
        mock_stream = MagicMock()
        mock_audio.open.return_value = mock_stream

        # Simulate 2-channel audio data
        stereo_data = np.array([10, 20, 30, 40], dtype=np.int16).tobytes()
        mock_stream.read.return_value = stereo_data

        mock_audio.get_device_info_by_index.return_value = {
            'maxInputChannels': 2,
            'name': 'mock_device'
        }

        # Act
        stream = MonoMicrophoneStream(device_index=0)
        mono_data = next(stream)
        stream.close()

        # Assert
        expected_mono_data = np.array([15, 35], dtype=np.int16).tobytes()
        self.assertEqual(mono_data, expected_mono_data)

    @patch('pyaudio.PyAudio')
    def test_channel_selection(self, mock_pyaudio):
        """Test that the correct channel is selected from a multi-channel stream."""
        # Arrange
        mock_audio = mock_pyaudio.return_value
        mock_stream = MagicMock()
        mock_audio.open.return_value = mock_stream

        # Simulate 3-channel audio data
        three_channel_data = np.array([1, 2, 3, 4, 5, 6], dtype=np.int16).tobytes()
        mock_stream.read.return_value = three_channel_data

        mock_audio.get_device_info_by_index.return_value = {
            'maxInputChannels': 3,
            'name': 'mock_device'
        }

        # Act
        stream = MonoMicrophoneStream(device_index=0, channel_indices=[1])
        selected_channel_data = next(stream)
        stream.close()

        # Assert
        expected_channel_data = np.array([2, 5], dtype=np.int16).tobytes()
        self.assertEqual(selected_channel_data, expected_channel_data)

    @patch('pyaudio.PyAudio')
    def test_invalid_device(self, mock_pyaudio):
        """Test that a ValueError is raised for a device with no input channels."""
        # Arrange
        mock_audio = mock_pyaudio.return_value
        mock_audio.get_device_info_by_index.return_value = {
            'maxInputChannels': 0,
            'name': 'mock_device'
        }

        # Act & Assert
        with self.assertRaises(ValueError):
            MonoMicrophoneStream(device_index=0)

if __name__ == '__main__':
    unittest.main()