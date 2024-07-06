from os import environ
from os.path import join  # for OS agnostic paths.
from typing import Dict
from typing import List

import pygame as pg
import pygame.freetype as font

# Everything here never changes ever.

environ["SDL_VIDEO_CENTERED"] = "1"

# Initialize pygame.
pg.init()

# Default settings to be written.
DEFAULT_SETTINGS_DICT: Dict[str, int] = {
    "resolution_index": 2,
    "resolution_scale": 3,
    "up": 1073741906,
    "down": 1073741905,
    "left": 1073741904,
    "right": 1073741903,
    "enter": 13,
    "pause": 27,
    "jump": 99,
    "attack": 120,
    # REMOVE IN BUILD
    "lmb": 1,
    "mmb": 2,
    "rmb": 3,
}

# Path dictionaries.
JSONS_DIR_PATH: str = "jsons"
JSONS_PATHS_DICT: Dict[str, str] = {
    "settings.json": join(JSONS_DIR_PATH, "settings.json"),
}

PNGS_DIR_PATH: str = "pngs"
PNGS_PATHS_DICT: Dict[str, str] = {
    "main_menu_background.png": join(
        PNGS_DIR_PATH, "main_menu_background.png"
    ),
    "gestalt_illusion_logo.png": join(
        PNGS_DIR_PATH, "gestalt_illusion_logo.png"
    ),
}

OGGS_DIR_PATH: str = "oggs"
OGGS_PATHS_DICT: Dict[str, str] = {
    "xdeviruchi_title_theme.ogg": join(
        OGGS_DIR_PATH, "xdeviruchi_title_theme.ogg"
    ),
    "001_hover_01.ogg": join(OGGS_DIR_PATH, "001_hover_01.ogg"),
    "confirm.ogg": join(OGGS_DIR_PATH, "confirm.ogg"),
}

# FPS.
FPS: int = 60

# Fixed dimensions.
TILE_WIDTH: int = 16
TILE_HEIGHT: int = 16

WINDOW_WIDTH: int = 320
WINDOW_HEIGHT: int = 180

NATIVE_WIDTH: int = 320
NATIVE_HEIGHT: int = 160

NATIVE_HALF_WIDTH: int = 160
NATIVE_HALF_HEIGHT: int = 80

NATIVE_WIDTH_TU: int = 20
NATIVE_HEIGHT_TU: int = 10

# Native surf and rect will never be mutated.
NATIVE_SURF: pg.Surface = pg.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
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
FONT_HEIGHT: int = 5
FONT_WIDTH: int = 3
FONT: font.Font = font.Font(
    join("ttf", "cg_pixel_3x5_mono.ttf"),
    FONT_HEIGHT,
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
