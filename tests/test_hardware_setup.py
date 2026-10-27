"""Tests pinning the hardware configuration in setup.py.

These guard the pin assignments and bus settings against silent regressions.
Pin numbers are cross-checked against the KiCad netlist in Hardware/Final:
each global label there maps to the Pico pad the firmware must drive.
"""

import setup


def test_display_i2c_runs_at_fast_mode():
    """100 kHz makes every full-frame redraw cost roughly 50 ms."""
    assert setup.i2c.frequency == 400_000


def test_display_i2c_uses_the_schematic_pins():
    # SCL -> GP15, SDA -> GP14 in dc31.kicad_sch
    assert setup.i2c.scl.name == "GP15"
    assert setup.i2c.sda.name == "GP14"


def test_display_is_the_128x32_panel():
    assert (setup.display.width, setup.display.height) == (128, 32)


def test_neopixels_match_the_front_board():
    assert len(setup.neopixels) == 10
    assert setup.neopixels.pin.name == "GP3"


def test_neopixels_do_not_auto_write():
    """auto_write pushes the whole strip on every single pixel assignment."""
    assert setup.neopixels.auto_write is False


def test_midi_uart_transmits_and_receives():
    """MIDI IN (J5 -> U5 TLP2361 -> GP9) was wired but never opened."""
    assert setup.midi_uart.tx.name == "GP8"
    assert setup.midi_uart.rx.name == "GP9"


def test_midi_uart_runs_at_the_midi_baud_rate():
    assert setup.midi_uart.baudrate == 31250


def test_serial_midi_is_configured_both_ways():
    assert setup.midi_serial.midi_out is setup.midi_uart
    assert setup.midi_serial.midi_in is setup.midi_uart


def test_serial_midi_channel_is_consistent_in_both_directions():
    expected = setup.midi_serial_channel - 1
    assert setup.midi_serial.out_channel == expected
    assert setup.midi_serial.in_channel == expected


def test_key_matrix_covers_twelve_keys():
    """8 pads, Play, Function, and both encoder buttons."""
    rows = len(setup.keys.row_pins)
    columns = len(setup.keys.column_pins)
    assert rows * columns == 12


def test_key_matrix_uses_the_schematic_pins():
    assert [pin.name for pin in setup.keys.row_pins] == ["GP27", "GP26", "GP18"]
    assert [pin.name for pin in setup.keys.column_pins] == [
        "GP20",
        "GP21",
        "GP22",
        "GP28",
    ]


def test_sync_pins_match_the_schematic():
    # SYNC_IN -> GP6 (via Q1 inverter), SYNC_OUT -> GP7 (via OPA341 buffer)
    assert setup.sync_in.pin.name == "GP6"
    assert setup.sync_out.pin.name == "GP7"
