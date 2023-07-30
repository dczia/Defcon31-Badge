import displayio
import terminalio
import time
from adafruit_display_text import label
from os import listdir

from setup import (
    display,
    enc_buttons,
    encoder_1,
    keys,
    line_height,
    offset,
    total_lines,
    width,
)


# Function to scroll through a list of menu items and return a selection on encoder press
def menu_select(last_position, menu_items):
    # Force last_position to not equal encoder_1.position and be % = 0
    last_position = -len(menu_items)
    encoder_1.position = 0
    item_selected = False
    while item_selected is False:
        current_position = encoder_1.position

        # Generate a valid index from the position
        if current_position != last_position:
            index = current_position % len(menu_items)
            # Display item
            pretty_name = menu_items[index]["pretty"]
            text = str.format("{}: {}", index, pretty_name)
            text_area = label.Label(
                terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15
            )
            display.show(text_area)
            last_position = current_position

        # Select item
        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            index = current_position % len(menu_items)
            return menu_items[index]["name"]


# Function to program sequence values, should be used after a keypress
# On key release toggle state
# On key held and encoder turned, value changed
def sequence_selector(value, min_val, max_val, increment, key_val):
    selection = True
    vel_change = False
    encoder_pos = encoder_1.position
    # Display current value
    while selection:
        text = f"Step {key_val}: {value[key_val][1]:.2f}"
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=5)
        display.show(text_area)
        key_event = keys.events.get()

        # Modify value on encoder input
        if encoder_pos is not encoder_1.position:
            if encoder_1.position < encoder_pos:
                if value[key_val][1] > min_val + increment:
                    value[key_val][1] = value[key_val][1] - increment
                else:
                    value[key_val][1] = min_val

            else:
                if value[key_val][1] < max_val - increment:
                    value[key_val][1] = value[key_val][1] + increment
                else:
                    value[key_val][1] = max_val
            encoder_pos = encoder_1.position
            vel_change = True

        # Exit selection menu if key released
        if key_event and key_event.released:
            if key_event.key_number == key_val:
                if not vel_change:
                    value[key_val][0] = not value[key_val][0]
                selection = False


# Menu Functions
def get_files():
    """Get a list of Python files in the root folder of the Pico"""

    files = listdir()
    menu = []
    for file in files:
        if file.endswith(".wav"):
            menu.append(file)

    return menu


def show_menu(menu, highlight, shift):
    """Shows the menu on the screen"""

    display_group = displayio.Group()
    # bring in the global variables

    # menu variables
    item = 1
    line = 0

    color_bitmap = displayio.Bitmap(width, line_height, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF  # White

    # Shift the list of files so that it shows on the display
    short_list = []
    for index in range(shift, shift + total_lines):
        short_list.append(menu[index]["pretty"])
    for item in short_list:
        if highlight == line:
            white_rectangle = displayio.TileGrid(
                color_bitmap,
                pixel_shader=color_palette,
                x=0,
                y=(line * line_height),
            )
            display_group.append(white_rectangle)
            text_arrow = ">"
            text_arrow = label.Label(
                terminalio.FONT,
                text=text_arrow,
                color=0x000000,
                x=0,
                y=(line * line_height) + offset,
            )
            display_group.append(text_arrow)
            text_item = label.Label(
                terminalio.FONT,
                text=item,
                color=0x000000,
                x=10,
                y=(line * line_height) + offset,
            )
            display_group.append(text_item)
        else:
            text_item = label.Label(
                terminalio.FONT,
                text=item,
                color=0xFFFFFF,
                x=10,
                y=(line * line_height) + offset,
            )
            display_group.append(text_item)
        line += 1
    display.show(display_group)


def launch(filename):
    """Launch the Python script <filename>"""
    global file_list
    time.sleep(3)
    exec(open(filename).read())
    show_menu(file_list)
