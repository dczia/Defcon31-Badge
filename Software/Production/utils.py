import displayio
import terminalio
from adafruit_display_text import label

from setup import (
    display,
)


def neoindex(key_number):
    mapping = [4, 5, 6, 7, 3, 2, 1, 0, 10, 11]
    try:
        neopixel_index = mapping[key_number]
    except IndexError:
        neopixel_index = 0
    return neopixel_index


def selector_calcs(menu, highlight, shift, last_position, position):
    list_length = len(menu)
    total_lines = 3
    if position < last_position:
        if highlight > 1:
            highlight -= 1
        else:
            if shift > 0:
                shift -= 1
    else:
        if highlight < total_lines:
            highlight += 1
        else:
            if shift + total_lines < list_length:
                shift += 1
    return (highlight, shift)


def show_menu(menu, highlight, shift):
    """Shows the menu on the screen"""

    display_group = displayio.Group()
    # bring in the global variables

    # menu variables
    item = 1
    line = 1
    line_height = 10
    offset = 5
    total_lines = 3

    color_bitmap = displayio.Bitmap(display.width, line_height, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF  # White

    # Shift the list of files so that it shows on the display
    short_list = []
    for index in range(shift, shift + total_lines):
        try:
            short_list.append(menu[index]["pretty"])
        except IndexError:
            print("show_menu: Bad Index")
    for item in short_list:
        if highlight == line:
            white_rectangle = displayio.TileGrid(
                color_bitmap,
                pixel_shader=color_palette,
                x=0,
                y=((line - 1) * line_height),
            )
            display_group.append(white_rectangle)
            text_arrow = ">"
            text_arrow = label.Label(
                terminalio.FONT,
                text=text_arrow,
                color=0x000000,
                x=0,
                y=((line - 1) * line_height) + offset,
            )
            display_group.append(text_arrow)
            text_item = label.Label(
                terminalio.FONT,
                text=item,
                color=0x000000,
                x=10,
                y=((line - 1) * line_height) + offset,
            )
            display_group.append(text_item)
        else:
            text_item = label.Label(
                terminalio.FONT,
                text=item,
                x=10,
                y=((line - 1) * line_height) + offset,
            )
            display_group.append(text_item)
        line += 1
    display.show(display_group)
