"""Minimal fakes for the CircuitPython modules the firmware imports.

Software/Production is written against CircuitPython running on an RP2040. None
of board, busio, audiobusio, keypad and friends exist on a desktop Python, and
setup.py performs real hardware initialisation at import time, so nothing in the
firmware can be imported by a test runner as-is.

install() registers just enough of that surface in sys.modules for the firmware
to import and be exercised. The fakes are deliberately shallow, but where a
detail matters for correctness it is reproduced faithfully:

* NeoPixel enforces its length, so an out-of-range pixel index raises IndexError
  exactly as it does on hardware. This is what makes the neoindex regression
  test meaningful rather than decorative.
* Animation constructors set auto_write False on the pixel object, matching
  adafruit_led_animation, because the firmware's display behaviour depends on
  that side effect.
* Mixer exposes a fixed-length voice list, so indexing past voice_count raises.
"""

import sys
import types


class Pin:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Pin(%s)" % self.name


class _BoardModule(types.ModuleType):
    """Any attribute access yields a Pin, matching board's dynamic surface."""

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        pin = Pin(name)
        setattr(self, name, pin)
        return pin


class Event:
    def __init__(self, key_number, pressed, timestamp=0):
        self.key_number = key_number
        self.pressed = pressed
        self.released = not pressed
        self.timestamp = timestamp


class _EventQueue:
    def __init__(self):
        self._events = []

    def get(self):
        if not self._events:
            return None
        return self._events.pop(0)

    def clear(self):
        self._events = []

    def post(self, event):
        """Test helper: queue an event for the firmware to consume."""
        self._events.append(event)

    def __len__(self):
        return len(self._events)


class KeyMatrix:
    def __init__(self, row_pins=(), column_pins=(), columns_to_anodes=True):
        self.row_pins = row_pins
        self.column_pins = column_pins
        self.events = _EventQueue()


class IncrementalEncoder:
    def __init__(self, pin_a=None, pin_b=None):
        self.position = 0


class NeoPixel:
    """List-like pixel buffer that enforces its length, as hardware does."""

    def __init__(self, pin, n, brightness=1.0, auto_write=True):
        self.pin = pin
        self.n = n
        self.brightness = brightness
        self.auto_write = auto_write
        self._pixels = [(0, 0, 0)] * n
        self.show_count = 0

    def __len__(self):
        return self.n

    def _check(self, index):
        if not isinstance(index, int):
            raise TypeError("pixel index must be an int")
        if index < 0 or index >= self.n:
            raise IndexError("pixel index out of range")

    def __setitem__(self, index, value):
        self._check(index)
        self._pixels[index] = value
        if self.auto_write:
            self.show()

    def __getitem__(self, index):
        self._check(index)
        return self._pixels[index]

    def fill(self, color):
        self._pixels = [color] * self.n
        if self.auto_write:
            self.show()

    def show(self):
        self.show_count += 1


class DigitalInOut:
    def __init__(self, pin):
        self.pin = pin
        self.direction = None
        self.value = False


class _Direction:
    OUTPUT = "output"
    INPUT = "input"


class I2C:
    def __init__(self, scl=None, sda=None, frequency=100000):
        self.scl = scl
        self.sda = sda
        self.frequency = frequency


class SPI:
    def __init__(self, clock=None, MOSI=None, MISO=None):
        self.clock = clock


class UART:
    def __init__(self, tx=None, rx=None, baudrate=9600, **kwargs):
        self.tx = tx
        self.rx = rx
        self.baudrate = baudrate


class Group:
    def __init__(self, *args, **kwargs):
        self.items = []

    def append(self, item):
        self.items.append(item)

    def __len__(self):
        return len(self.items)


class Bitmap:
    def __init__(self, width, height, value_count):
        self.width = width
        self.height = height


class Palette:
    def __init__(self, count):
        self._colors = [0] * count

    def __setitem__(self, index, value):
        self._colors[index] = value


class TileGrid:
    def __init__(self, bitmap, pixel_shader=None, x=0, y=0):
        self.bitmap = bitmap
        self.x = x
        self.y = y


class I2CDisplay:
    def __init__(self, bus, device_address=0):
        self.bus = bus


class SSD1306:
    def __init__(self, bus, width=128, height=32):
        self.width = width
        self.height = height
        self.shown = None
        self.root_group = None

    def show(self, group):
        self.shown = group


class Label:
    def __init__(self, font, text="", color=None, x=0, y=0, **kwargs):
        self.font = font
        self.text = text
        self.color = color
        self.x = x
        self.y = y


class WaveFile:
    def __init__(self, file_obj):
        header = file_obj.read(12)
        if header[:4] != b"RIFF" or header[8:12] != b"WAVE":
            raise ValueError("not a RIFF/WAVE file")
        self.file = file_obj


class _Voice:
    def __init__(self):
        self.level = 1.0
        self.playing = False
        self.sample = None

    def play(self, sample, loop=False):
        self.sample = sample
        self.playing = True

    def stop(self):
        self.playing = False


class Mixer:
    def __init__(self, voice_count=1, **kwargs):
        self.voice_count = voice_count
        self.voice = [_Voice() for _ in range(voice_count)]
        self.config = kwargs


class I2SOut:
    def __init__(self, bit_clock=None, word_select=None, data=None):
        self.playing = False
        self.deinited = False
        self.deinit_count = 0

    def play(self, sample, loop=False):
        self.playing = True

    def stop(self):
        self.playing = False

    def deinit(self):
        self.deinited = True
        self.deinit_count += 1


class SDCard:
    def __init__(self, spi, cs):
        raise OSError("no SD card in the test environment")


class VfsFat:
    def __init__(self, sdcard):
        self.sdcard = sdcard


class MIDI:
    def __init__(
        self,
        midi_in=None,
        midi_out=None,
        in_channel=None,
        out_channel=0,
        **kwargs,
    ):
        self.midi_in = midi_in
        self.midi_out = midi_out
        self.in_channel = in_channel
        self.out_channel = out_channel
        self.sent = []

    def send(self, message):
        self.sent.append(message)

    def receive(self):
        return None


class _MidiMessage:
    def __init__(self, note, velocity=0):
        self.note = note
        self.velocity = velocity

    def __eq__(self, other):
        return (
            type(self) is type(other)
            and self.note == other.note
            and self.velocity == other.velocity
        )

    def __repr__(self):
        return "%s(%r, %r)" % (type(self).__name__, self.note, self.velocity)


class NoteOn(_MidiMessage):
    pass


class NoteOff(_MidiMessage):
    pass


class ControlChange:
    def __init__(self, control, value):
        self.control = control
        self.value = value


class Keyboard:
    def __init__(self, devices):
        self.pressed = []
        self.released = []

    def press(self, *keycodes):
        self.pressed.extend(keycodes)

    def release(self, *keycodes):
        self.released.extend(keycodes)

    def release_all(self):
        self.pressed = []


class ConsumerControl:
    def __init__(self, devices):
        self.sent = []

    def send(self, code):
        self.sent.append(code)


class Keycode:
    KEYPAD_ZERO = 98
    KEYPAD_ONE = 89
    KEYPAD_TWO = 90
    KEYPAD_THREE = 91
    KEYPAD_FOUR = 92
    KEYPAD_FIVE = 93
    KEYPAD_SIX = 94
    KEYPAD_SEVEN = 95
    KEYPAD_EIGHT = 96
    KEYPAD_NINE = 97
    KEYPAD_PLUS = 87
    KEYPAD_MINUS = 86


class ConsumerControlCode:
    VOLUME_INCREMENT = 233
    VOLUME_DECREMENT = 234
    MUTE = 226


class _Animation:
    """Mirrors adafruit_led_animation: takes ownership of auto_write."""

    def __init__(self, pixel_object, speed=0.1, **kwargs):
        self.pixel_object = pixel_object
        # The real library does this, and firmware behaviour depends on it.
        pixel_object.auto_write = False
        self.animate_count = 0

    def animate(self):
        self.animate_count += 1
        return True


class _Ticks:
    """Monotonic millisecond counter that advances on every read.

    The firmware busy-waits with `while ticks_ms() < deadline: pass`, so a
    constant would hang any test that reaches one. Advancing per read lets those
    loops terminate without the test needing to sleep.
    """

    def __init__(self, step=1):
        self.value = 0
        self.step = step

    def __call__(self):
        self.value += self.step
        return self.value

    def reset(self):
        self.value = 0


ticks = _Ticks()


def _module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


def install():
    """Register the fake modules in sys.modules. Safe to call repeatedly."""
    board = _BoardModule("board")
    modules = {
        "board": board,
        "busio": _module("busio", I2C=I2C, SPI=SPI, UART=UART),
        "digitalio": _module(
            "digitalio", DigitalInOut=DigitalInOut, Direction=_Direction
        ),
        "keypad": _module("keypad", KeyMatrix=KeyMatrix, Event=Event),
        "rotaryio": _module("rotaryio", IncrementalEncoder=IncrementalEncoder),
        "neopixel": _module("neopixel", NeoPixel=NeoPixel),
        "displayio": _module(
            "displayio",
            release_displays=lambda: None,
            I2CDisplay=I2CDisplay,
            Group=Group,
            Bitmap=Bitmap,
            Palette=Palette,
            TileGrid=TileGrid,
        ),
        "terminalio": _module("terminalio", FONT=object()),
        "storage": _module(
            "storage",
            VfsFat=VfsFat,
            mount=lambda vfs, path: None,
            remount=lambda path, readonly=True: None,
        ),
        "usb_midi": _module("usb_midi", ports=[None, None]),
        "usb_hid": _module("usb_hid", devices=[]),
        "audiobusio": _module("audiobusio", I2SOut=I2SOut),
        "audiomixer": _module("audiomixer", Mixer=Mixer),
        "audiocore": _module("audiocore", WaveFile=WaveFile),
        "supervisor": _module("supervisor", ticks_ms=ticks),
        "adafruit_displayio_ssd1306": _module(
            "adafruit_displayio_ssd1306", SSD1306=SSD1306
        ),
        "adafruit_sdcard": _module("adafruit_sdcard", SDCard=SDCard),
        "adafruit_midi": _module("adafruit_midi", MIDI=MIDI),
        "adafruit_midi.note_on": _module("adafruit_midi.note_on", NoteOn=NoteOn),
        "adafruit_midi.note_off": _module("adafruit_midi.note_off", NoteOff=NoteOff),
        "adafruit_midi.control_change": _module(
            "adafruit_midi.control_change", ControlChange=ControlChange
        ),
        "adafruit_display_text": _module("adafruit_display_text"),
        "adafruit_display_text.label": _module(
            "adafruit_display_text.label", Label=Label
        ),
        "adafruit_hid": _module("adafruit_hid"),
        "adafruit_hid.keyboard": _module("adafruit_hid.keyboard", Keyboard=Keyboard),
        "adafruit_hid.keycode": _module("adafruit_hid.keycode", Keycode=Keycode),
        "adafruit_hid.consumer_control": _module(
            "adafruit_hid.consumer_control", ConsumerControl=ConsumerControl
        ),
        "adafruit_hid.consumer_control_code": _module(
            "adafruit_hid.consumer_control_code",
            ConsumerControlCode=ConsumerControlCode,
        ),
    }

    # adafruit_led_animation.animation.<name> — each exposes one animation class.
    animation_names = {
        "rainbow": "Rainbow",
        "rainbowchase": "RainbowChase",
        "rainbowcomet": "RainbowComet",
        "rainbowsparkle": "RainbowSparkle",
        "sparklepulse": "SparklePulse",
    }
    modules["adafruit_led_animation"] = _module("adafruit_led_animation")
    modules["adafruit_led_animation.animation"] = _module(
        "adafruit_led_animation.animation"
    )
    for module_name, class_name in animation_names.items():
        full = "adafruit_led_animation.animation." + module_name
        modules[full] = _module(
            full, **{class_name: type(class_name, (_Animation,), {})}
        )

    for name, module in modules.items():
        sys.modules[name] = module

    # adafruit_display_text is imported as `from adafruit_display_text import label`
    sys.modules["adafruit_display_text"].label = sys.modules[
        "adafruit_display_text.label"
    ]
    sys.modules["adafruit_midi"].note_on = sys.modules["adafruit_midi.note_on"]
    sys.modules["adafruit_midi"].note_off = sys.modules["adafruit_midi.note_off"]
    sys.modules["adafruit_midi"].control_change = sys.modules[
        "adafruit_midi.control_change"
    ]
    for submodule in (
        "keyboard",
        "keycode",
        "consumer_control",
        "consumer_control_code",
    ):
        setattr(
            sys.modules["adafruit_hid"],
            submodule,
            sys.modules["adafruit_hid." + submodule],
        )

    return board
