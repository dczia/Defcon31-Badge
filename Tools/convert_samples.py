#!/usr/bin/env python3
"""Convert WAV files to the format the badge's audio mixer expects.

The sampler builds its audiomixer.Mixer with a fixed format, so every sample it
plays has to match it exactly:

    22050 Hz, 1 channel (mono), 16-bit signed PCM

A file at any other rate or channel count either plays at the wrong pitch or is
rejected outright. The 909 pack under "Samples/909 Samples" ships as 44100 Hz
stereo, which is why those files cannot be dropped straight into /samples/.

Usage:
    python3 Tools/convert_samples.py INPUT [INPUT ...] -o OUTPUT_DIR

Example:
    python3 Tools/convert_samples.py "Samples/909 Samples"/*.wav -o /tmp/909

Only the Python standard library is used, so this runs anywhere without a
virtualenv.
"""

import argparse
import os
import struct
import sys
import wave

TARGET_RATE = 22050
TARGET_CHANNELS = 1
TARGET_WIDTH = 2  # bytes per sample, i.e. 16-bit


def read_frames(path):
    """Return (samples, rate) with samples as a flat list of per-channel ints."""
    with wave.open(path, "rb") as source:
        channels = source.getnchannels()
        width = source.getsampwidth()
        rate = source.getframerate()
        raw = source.readframes(source.getnframes())

    if width == 1:
        # 8-bit WAV is unsigned; centre it and scale up to 16-bit.
        values = [(byte - 128) * 256 for byte in raw]
    elif width == 2:
        values = list(struct.unpack("<%dh" % (len(raw) // 2), raw))
    elif width == 4:
        values = [v >> 16 for v in struct.unpack("<%di" % (len(raw) // 4), raw)]
    else:
        raise ValueError("unsupported sample width: %d bytes" % width)

    return values, rate, channels


def to_mono(values, channels):
    """Average interleaved channels down to one."""
    if channels == 1:
        return values
    mono = []
    for index in range(0, len(values) - channels + 1, channels):
        mono.append(sum(values[index : index + channels]) // channels)
    return mono


def resample(values, source_rate, target_rate):
    """Linearly interpolate to the target rate."""
    if source_rate == target_rate or not values:
        return values
    ratio = source_rate / target_rate
    count = int(len(values) / ratio)
    out = []
    for index in range(count):
        position = index * ratio
        left = int(position)
        right = min(left + 1, len(values) - 1)
        weight = position - left
        out.append(int(values[left] * (1.0 - weight) + values[right] * weight))
    return out


def clamp(values):
    return [max(-32768, min(32767, value)) for value in values]


def convert(in_path, out_path):
    values, rate, channels = read_frames(in_path)
    values = to_mono(values, channels)
    values = resample(values, rate, TARGET_RATE)
    values = clamp(values)

    with wave.open(out_path, "wb") as target:
        target.setnchannels(TARGET_CHANNELS)
        target.setsampwidth(TARGET_WIDTH)
        target.setframerate(TARGET_RATE)
        target.writeframes(struct.pack("<%dh" % len(values), *values))

    return rate, channels, len(values)


def main():
    parser = argparse.ArgumentParser(
        description="Convert WAV files to 22050 Hz mono 16-bit for the badge."
    )
    parser.add_argument("inputs", nargs="+", help="WAV files to convert")
    parser.add_argument(
        "-o", "--output-dir", required=True, help="directory to write converted files"
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    failures = 0
    for in_path in args.inputs:
        name = os.path.basename(in_path)
        out_path = os.path.join(args.output_dir, name)
        try:
            rate, channels, frames = convert(in_path, out_path)
        except (OSError, ValueError, wave.Error) as error:
            print("SKIP %s: %s" % (name, error), file=sys.stderr)
            failures += 1
            continue
        layout = "mono" if channels == 1 else "%dch" % channels
        print(
            "%-28s %5d Hz %-5s -> %d Hz mono, %d frames"
            % (name, rate, layout, TARGET_RATE, frames)
        )

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
