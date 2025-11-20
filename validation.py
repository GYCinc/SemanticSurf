import pyaudio
import logging

logger = logging.getLogger(__name__)

def validate_audio_device(device_index):
    """Validate audio device exists and has input channels - FAIL LOUDLY if not"""
    p = pyaudio.PyAudio()
    try:
        # Get total device count
        device_count = p.get_device_count()
        
        # Check if device index is out of range
        if device_index >= device_count or device_index < 0:
            print("\n" + "="*70)
            print("❌ AUDIO DEVICE ERROR")
            print("="*70)
            print(f"Device index {device_index} does not exist!")
            print(f"\n📋 Available input devices:")
            print(f"{'Index':<8} {'Name':<45} {'Channels':<10}")
            print("-" * 70)
            
            for i in range(device_count):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    marker = " ← RECOMMENDED" if "Aggregate" in info['name'] else ""
                    print(f"{i:<8} {info['name']:<45} {info['maxInputChannels']:<10}{marker}")
            
            print("\n💡 Fix: Update config.json with a valid device_index")
            print("="*70 + "\n")
            return False
        
        # Check if device has input channels
        device_info = p.get_device_info_by_index(device_index)
        if device_info['maxInputChannels'] == 0:
            print("\n" + "="*70)
            print("❌ AUDIO DEVICE ERROR")
            print("="*70)
            print(f"Device {device_index} ({device_info['name']}) has NO input channels!")
            print(f"\n📋 Available input devices:")
            print(f"{'Index':<8} {'Name':<45} {'Channels':<10}")
            print("-" * 70)
            
            for i in range(device_count):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    marker = " ← RECOMMENDED" if "Aggregate" in info['name'] else ""
                    print(f"{i:<8} {info['name']:<45} {info['maxInputChannels']:<10}{marker}")
            
            print("\n💡 Fix: Update config.json with a valid input device")
            print("="*70 + "\n")
            return False
        
        # Device is valid!
        print(f"✅ Audio device validated: [{device_index}] {device_info['name']} ({device_info['maxInputChannels']} channels)")
        return True
    finally:
        p.terminate()
