import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from validation import validate_audio_device

class TestValidation(unittest.TestCase):

    @patch('pyaudio.PyAudio')
    def test_valid_device(self, mock_pyaudio):
        """Test that a valid audio device is correctly identified."""
        # Arrange
        mock_audio = mock_pyaudio.return_value
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_device_info_by_index.return_value = {
            'maxInputChannels': 1,
            'name': 'mock_device'
        }

        # Act
        is_valid = validate_audio_device(device_index=0)

        # Assert
        self.assertTrue(is_valid)

    @patch('pyaudio.PyAudio')
    def test_invalid_device_index(self, mock_pyaudio):
        """Test that an invalid device index is correctly identified."""
        # Arrange
        mock_audio = mock_pyaudio.return_value
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_device_info_by_index.return_value = {
            'maxInputChannels': 1,
            'name': 'mock_device'
        }

        # Act
        is_valid = validate_audio_device(device_index=1)

        # Assert
        self.assertFalse(is_valid)

    @patch('pyaudio.PyAudio')
    def test_device_with_no_input_channels(self, mock_pyaudio):
        """Test that a device with no input channels is correctly identified as invalid."""
        # Arrange
        mock_audio = mock_pyaudio.return_value
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_device_info_by_index.return_value = {
            'maxInputChannels': 0,
            'name': 'mock_device'
        }

        # Act
        is_valid = validate_audio_device(device_index=0)

        # Assert
        self.assertFalse(is_valid)

if __name__ == '__main__':
    unittest.main()