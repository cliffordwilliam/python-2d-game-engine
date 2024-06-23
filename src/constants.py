from os.path import join  # for OS agnostic paths.
from typing import Dict
from typing import List

import pygame as pg
import pygame.freetype as font

# Everything here never changes ever.

# Initialize pygame.
pg.init()

# Path dictionaries.
PNGS_DIR_PATH: str = "pngs"
PNGS_PATHS: Dict[str, str] = {
    "main_menu_background.png": join(
        PNGS_DIR_PATH, "main_menu_background.png"
    ),
    "gestalt_illusion_logo.png": join(
        PNGS_DIR_PATH, "gestalt_illusion_logo.png"
    ),
}

JSONS_DIR_PATH: str = "jsons"
JSONS_PATHS: Dict[str, str] = {
    # "fire_animation.json":
    # join(JSONS_DIR_PATH, "fire_animation.json"),
}

WAVS_DIR_PATH: str = "wavs"
WAVS_PATHS: Dict[str, str] = {
    # "cursor.wav":
    # join(WAVS_DIR_PATH, "cursor.wav"),
}

# FPS.
FPS: int = 60

# Fixed dimensions.
TILE_W: int = 16
TILE_H: int = 16

WINDOW_W: int = 320
WINDOW_H: int = 180

NATIVE_W: int = 320
NATIVE_H: int = 160

# Native surf and rect will never be mutated.
NATIVE_SURF: pg.Surface = pg.Surface((NATIVE_W, NATIVE_H))
NATIVE_RECT: pg.Rect = NATIVE_SURF.get_rect()

# Clock never changes.
CLOCK: pg.time.Clock = pg.time.Clock()

# Event ints list (used by event for loop).
EVENTS: List[int] = [
    pg.KEYDOWN,
    pg.KEYUP,
    pg.QUIT,
    # REMOVE IN BUILD
    # Because production don't use the mouse.
    pg.MOUSEBUTTONUP,
    pg.MOUSEBUTTONDOWN,
]

# Font dimensions and instance.
FONT_H: int = 5
FONT_W: int = 3
FONT: font.Font = font.Font(
    join("ttf", "cg_pixel_3x5_mono.ttf"),
    FONT_H,
)

# Quadtree recursion limit.
MAX_QUADTREE_DEPTH: int = 8

# REMOVE IN BUILD
# This is for room editor autotile mapping.
MASK_ID_TO_INDEX: Dict[str, int] = {
    "208": 0,
    "248": 1,
    "104": 2,
    "64": 3,
    "80": 4,
    "120": 5,
    "216": 6,
    "72": 7,
    "88": 8,
    "219": 9,
    "214": 10,
    "255": 11,
    "107": 12,
    "66": 13,
    "86": 14,
    "127": 15,
    "223": 16,
    "75": 17,
    "95": 18,
    "126": 19,
    "22": 20,
    "31": 21,
    "11": 22,
    "2": 23,
    "210": 24,
    "251": 25,
    "254": 26,
    "106": 27,
    "250": 28,
    "218": 29,
    "122": 30,
    "16": 31,
    "24": 32,
    "8": 33,
    "0": 34,
    "18": 35,
    "27": 36,
    "30": 37,
    "10": 38,
    "26": 39,
    "94": 40,
    "91": 41,
    "82": 42,
    "123": 43,
    "222": 44,
    "74": 45,
    "90": 46,
}

# REMOVE IN BUILD
# This is for frame by frame debug tool.
NEXT_FRAME: int = pg.K_8
