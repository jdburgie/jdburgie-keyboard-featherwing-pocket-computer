# Compact Gothic-inspired display font.
# Glyph body: 8 x 11 pixels, with a 9-pixel character cell.
# No external font file is required.

import displayio

_SOURCE_W = 5
_SOURCE_H = 7
_GLYPH_W = 8
_GLYPH_H = 11
_CELL_W = 9

from gothic_glyphs import _FONT


def _set_pixel(bitmap, x, y):
    if 0 <= x < bitmap.width and 0 <= y < bitmap.height:
        bitmap[x, y] = 1


def _tilegrid(text, color):
    text = str(text).upper()
    width = max(1, len(text) * _CELL_W - 1)
    height = _GLYPH_H

    bitmap = displayio.Bitmap(width, height, 2)
    palette = displayio.Palette(2)
    palette[0] = 0x000000
    palette[1] = color
    palette.make_transparent(0)

    for char_index, char in enumerate(text):
        rows = _FONT.get(char, _FONT["?"])
        cell_x = char_index * _CELL_W

        for source_y, row_bits in enumerate(rows):
            y0 = (source_y * _GLYPH_H) // _SOURCE_H
            y1 = ((source_y + 1) * _GLYPH_H) // _SOURCE_H
            waist_shift = 1 if 3 <= y0 <= 6 else 0

            for source_x in range(_SOURCE_W):
                if not (row_bits & (1 << (4 - source_x))):
                    continue

                x0 = (source_x * _GLYPH_W) // _SOURCE_W
                x1 = ((source_x + 1) * _GLYPH_W) // _SOURCE_W

                for py in range(y0, max(y0 + 1, y1)):
                    for px in range(x0, max(x0 + 1, x1)):
                        _set_pixel(bitmap, cell_x + px + waist_shift, py)

        if char not in (" ", ".", ":", "-", "/"):
            top_bits = rows[0]
            bottom_bits = rows[-1]

            if top_bits:
                first = 0
                while first < _SOURCE_W and not (top_bits & (1 << (4 - first))):
                    first += 1
                last = _SOURCE_W - 1
                while last >= 0 and not (top_bits & (1 << (4 - last))):
                    last -= 1
                if first < _SOURCE_W:
                    left = (first * _GLYPH_W) // _SOURCE_W
                    right = min(_GLYPH_W - 1, ((last + 1) * _GLYPH_W) // _SOURCE_W - 1)
                    _set_pixel(bitmap, cell_x + max(0, left - 1), 1)
                    _set_pixel(bitmap, cell_x + min(_GLYPH_W - 1, right + 1), 1)

            if bottom_bits:
                first = 0
                while first < _SOURCE_W and not (bottom_bits & (1 << (4 - first))):
                    first += 1
                last = _SOURCE_W - 1
                while last >= 0 and not (bottom_bits & (1 << (4 - last))):
                    last -= 1
                if first < _SOURCE_W:
                    left = (first * _GLYPH_W) // _SOURCE_W
                    right = min(_GLYPH_W - 1, ((last + 1) * _GLYPH_W) // _SOURCE_W - 1)
                    _set_pixel(bitmap, cell_x + max(0, left - 1), _GLYPH_H - 2)
                    _set_pixel(bitmap, cell_x + min(_GLYPH_W - 1, right + 1), _GLYPH_H - 2)

    return displayio.TileGrid(bitmap, pixel_shader=palette)


class GothicText:
    def __init__(self, parent, text, x, y, color=0xFFFFFF):
        self.group = displayio.Group(x=x, y=y)
        parent.append(self.group)
        self._text = ""
        self._color = color
        self.set(text, color)

    def set(self, text, color=None):
        if color is not None:
            self._color = color

        while len(self.group):
            self.group.pop()

        self._text = str(text)
        self.group.append(_tilegrid(self._text, self._color))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self.set(value)


def add_gothic_text(parent, text, x, y, color=0xFFFFFF):
    return GothicText(parent, text, x, y, color)
