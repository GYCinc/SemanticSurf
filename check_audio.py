#!/usr/bin/env python3
"""Quick audio device checker"""

import pyaudio

p = pyaudio.PyAudio()

print("\n🎤 Available Audio Input Devices:\n")
print(f"{'Index':<8} {'Name':<50} {'Channels':<10}")
print("-" * 70)

for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:  # Only show input devices
        print(f"{i:<8} {info['name']:<50} {info['maxInputChannels']:<10}")

print("\n" + "=" * 70)
print("\n💡 Quick Fix:")
print("   1. Find your device index above")
print("   2. Edit config.json file:")
print('      "device_index": YOUR_INDEX')
print("\n" + "=" * 70)
print("\n🎧 For Multi-Channel Devices (like Aggregate Device):")
print("   To combine specific channels (e.g., your microphone and system audio),")
print("   add the channel numbers to the 'channel_indices' list in your config.json file.")
print("\n   Example (mic on channel 0, system audio on 1 and 2):")
print('     "device_index": 7,')
print('     "channel_indices": [0, 1, 2]')
print("\n   To find the correct channels:")
print('   1. Start with an empty list: "channel_indices": [] (this will average all channels).')
print('   2. To isolate your microphone, try setting "channel_indices": [0], then [1], etc.')
print("   3. Once you find your microphone, add the system audio channels to the list.")

p.terminate()