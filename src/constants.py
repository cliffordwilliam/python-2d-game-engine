from os.path import join
from typing import Dict
from typing import List

import pygame as pg
import pygame.freetype as font

pg.init()

PNGS_DIR_PATH: str = "pngs"
PNGS_PATHS: Dict[str, str] = {
    # "player_flip_sprite_sheet.png":
    # join(PNGS_DIR_PATH, "player_flip_sprite_sheet.png"),
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

TILE_S: int = 16

FPS: int = 60

WINDOW_W: int = 320
WINDOW_H: int = 180

NATIVE_W: int = 320
NATIVE_H: int = 160

NATIVE_W_TU: int = 20
NATIVE_H_TU: int = 10

NATIVE_W_TU_EXTRA_ONE: int = 21
NATIVE_H_TU_EXTRA_ONE: int = 11

NATIVE_SURF: pg.Surface = pg.Surface((NATIVE_W, NATIVE_H))
NATIVE_RECT: pg.Rect = NATIVE_SURF.get_rect()

CLOCK: pg.time.Clock = pg.time.Clock()

EVENTS: List[int] = [
    pg.KEYDOWN,
    pg.KEYUP,
    pg.QUIT,
    # REMOVE IN BUILD
    pg.MOUSEBUTTONUP,
    pg.MOUSEBUTTONDOWN,
]

FONT_H: int = 5
FONT_W: int = 3
FONT: font.Font = font.Font(
    join("ttf", "cg_pixel_3x5_mono.ttf"),
    FONT_H,
)

MAX_QUADTREE_DEPTH: int = 8

# REMOVE IN BUILD
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

NEXT_FRAME: int = pg.K_8
