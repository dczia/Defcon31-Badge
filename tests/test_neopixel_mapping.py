"""Regression tests for the key-to-NeoPixel mapping.

neoindex() used to map key 8 (Play) and key 9 (Function) to pixel indices 10 and
11, but the front board carries exactly ten LEDs. HIDState gates on
key_number < 10, so pressing Play or Function in USB HID mode assigned to
neopixels[10] and raised IndexError, dropping the badge to the REPL.

The stub NeoPixel enforces its length exactly as hardware does, so these tests
fail against the original mapping.
"""

import pytest

import setup
import utils
from utils import neoindex

PIXEL_COUNT = 10

# Physical layout, read off Hardware/Final/dc31-front.kicad_pcb and
# Hardware/Final/dc31.kicad_pcb by matching X coordinates:
#   D105-D108 sit above pads 1-4     -> pixels 4,5,6,7
#   D104-D101 sit below pads 5-8     -> pixels 3,2,1,0
#   D109, D110 sit at Play, Function -> pixels 8,9
EXPECTED_MAPPING = {
    0: 4,
    1: 5,
    2: 6,
    3: 7,
    4: 3,
    5: 2,
    6: 1,
    7: 0,
    8: 8,
    9: 9,
}


def test_strip_is_ten_pixels():
    """The mapping is only correct relative to the real strip length."""
    assert len(setup.neopixels) == PIXEL_COUNT


@pytest.mark.parametrize("key_number,pixel", sorted(EXPECTED_MAPPING.items()))
def test_each_key_maps_to_its_own_pixel(key_number, pixel):
    assert neoindex(key_number) == pixel


def test_play_and_function_have_their_own_pixels():
    """The specific regression: keys 8 and 9 pointed at 10 and 11."""
    assert neoindex(8) == 8
    assert neoindex(9) == 9


def test_pad_keys_map_onto_distinct_pixels():
    pads = [neoindex(key) for key in range(8)]
    assert sorted(pads) == list(range(8))


def test_every_mapped_index_is_addressable():
    """The failure mode itself: assigning must not raise for any real key.

    The keypad matrix produces key numbers 0-11 (8 pads, Play, Function, and
    both encoder buttons), and HIDState passes anything under 10 through to the
    strip. Against the old mapping this raises IndexError at key 8.
    """
    for key_number in range(12):
        setup.neopixels[neoindex(key_number)] = (1, 2, 3)


def test_out_of_range_key_falls_back_to_a_valid_pixel():
    assert 0 <= neoindex(99) < PIXEL_COUNT


def test_utils_exposes_neoindex():
    assert utils.neoindex is neoindex
