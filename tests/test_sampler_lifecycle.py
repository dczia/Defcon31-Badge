"""Regression tests for sampler state, audio teardown and sample loading.

Covers three separate bugs:

* sampler_files and sampler_voices were class attributes that enter() appended
  to without clearing, so every visit leaked file handles, desynchronised voice
  indices, and eventually indexed past the ten-voice mixer.
* audio.deinit() ran only on one exit path, so leaving any other way left I2S
  allocated and re-entering raised RuntimeError.
* Loading a deleted or malformed sample raised straight through to the main
  loop, halting the badge.
"""

import struct

import pytest

import circuitpython_stubs
import SequencerState
from SequencerState import SamplerMenuState, SequencerPlayState, file_sequences


class FakeMachine:
    def __init__(self, last_state="sampler_menu"):
        self.animation = None
        self.last_state = last_state
        self.transitions = []

    def go_to_state(self, name):
        self.transitions.append(name)


def write_wav(path, frames=32):
    """A minimal but valid 22050 Hz mono 16-bit WAV."""
    data = struct.pack("<%dh" % frames, *([0] * frames))
    header = (
        b"RIFF"
        + struct.pack("<I", 36 + len(data))
        + b"WAVEfmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, 22050, 44100, 2, 16)
        + b"data"
        + struct.pack("<I", len(data))
    )
    path.write_bytes(header + data)
    return path


@pytest.fixture(autouse=True)
def reset_sequences():
    file_sequences.files.clear()
    file_sequences.sequences.clear()
    yield
    file_sequences.files.clear()
    file_sequences.sequences.clear()


@pytest.fixture
def samples(tmp_path, monkeypatch):
    """Point the firmware's /samples/ reads at a temporary directory."""
    directory = tmp_path / "samples"
    directory.mkdir()
    real_open = open

    def fake_open(path, *args, **kwargs):
        if isinstance(path, str) and path.startswith("/samples/"):
            path = str(directory / path[len("/samples/") :])
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(SequencerState, "open", fake_open, raising=False)
    return directory


def test_release_audio_is_safe_before_anything_is_allocated():
    state = SequencerPlayState()
    state.release_audio()
    assert state.audio is None
    assert state.sampler_files == []


def test_release_audio_deinits_and_clears(samples):
    state = SequencerPlayState()
    state.audio = circuitpython_stubs.I2SOut()
    handle = open(write_wav(samples / "a.wav"), "rb")
    state.sampler_files = [handle]
    state.sampler_voices = ["voice"]

    audio = state.audio
    state.release_audio()

    assert audio.deinited
    assert state.audio is None
    assert state.mixer is None
    assert state.sampler_files == []
    assert state.sampler_voices == []
    assert handle.closed


def test_release_audio_is_idempotent():
    state = SequencerPlayState()
    state.audio = circuitpython_stubs.I2SOut()
    state.release_audio()
    state.release_audio()
    assert state.audio is None


def test_voices_do_not_accumulate_across_entries(samples):
    """The leak: three visits used to leave three copies of every voice."""
    write_wav(samples / "kick.wav")
    file_sequences.add_sequence("kick.wav")

    state = SequencerPlayState()
    for _ in range(3):
        state.enter(FakeMachine())
        assert len(state.sampler_voices) == len(file_sequences.files)
        state.exit(FakeMachine())

    assert state.sampler_voices == []


def test_exit_releases_audio_on_every_path(samples):
    write_wav(samples / "kick.wav")
    file_sequences.add_sequence("kick.wav")

    state = SequencerPlayState()
    state.enter(FakeMachine())
    audio = state.audio
    assert audio is not None
    state.exit(FakeMachine())
    assert audio.deinited


def test_missing_sample_does_not_raise(samples):
    """A sample deleted after its sequence was created must not halt the badge."""
    file_sequences.add_sequence("gone.wav")
    state = SequencerPlayState()
    state.enter(FakeMachine())
    assert state.sampler_voices == [None]


def test_malformed_sample_does_not_raise(samples):
    (samples / "broken.wav").write_bytes(b"this is not a wav file at all")
    file_sequences.add_sequence("broken.wav")
    state = SequencerPlayState()
    state.enter(FakeMachine())
    assert state.sampler_voices == [None]


def test_failed_load_keeps_voice_indices_aligned(samples):
    """Placeholders matter: skipping would shift later samples onto wrong tracks."""
    write_wav(samples / "one.wav")
    write_wav(samples / "three.wav")
    for name in ("one.wav", "missing.wav", "three.wav"):
        file_sequences.add_sequence(name)

    state = SequencerPlayState()
    state.enter(FakeMachine())

    assert len(state.sampler_voices) == 3
    assert state.sampler_voices[0] is not None
    assert state.sampler_voices[1] is None
    assert state.sampler_voices[2] is not None


def test_add_sequence_requires_a_filename():
    with pytest.raises(TypeError):
        file_sequences.add_sequence()


def test_add_sequence_creates_eight_steps():
    file_sequences.add_sequence("kick.wav")
    assert len(file_sequences.sequences[0]) == 8


def test_select_wav_returns_none_when_no_samples_exist():
    """Without this guard, opening Add Sequence on an empty card crashes."""
    menu = SamplerMenuState()
    menu.samples = []
    assert menu.select_wav() is None


def test_sampler_menu_survives_a_missing_samples_directory():
    """__init__ runs at import time in main.py, so this must not raise."""
    menu = SamplerMenuState()
    assert isinstance(menu.samples, list)
