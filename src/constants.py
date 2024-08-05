from os import environ
from os import getenv
from os import listdir
from os import makedirs
from os.path import exists
from os.path import expanduser
from os.path import isfile
from os.path import join  # for OS agnostic paths
from platform import system
from typing import Any

import pygame as pg
import pygame.freetype as font

# Everything here never changes ever

environ["SDL_VIDEO_CENTERED"] = "1"

# Initialize pygame.
pg.init()

# Default settings to be written
DEFAULT_SETTINGS_DICT: dict[str, int] = {
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


# Function to create a dictionary of file paths
def create_paths_dict(directory: str) -> dict[str, str]:
    paths_dict = {}
    for filename in listdir(directory):
        if isfile(join(directory, filename)):
            paths_dict[filename] = join(directory, filename)
    return paths_dict


# Get the OS-specific directory for storing application data
def get_os_specific_directory(app_name: Any) -> str:
    user_home = expanduser("~")
    sys = system()

    if sys == "Windows":
        appdata_path = getenv("APPDATA", user_home)
        directory = join(appdata_path, app_name)
    elif sys == "Darwin":  # macOS
        directory = join(user_home, "Library", "Application Support", app_name)
    else:  # Assume Linux or other Unix-like OS
        directory = join(user_home, ".config", app_name)

    # Ensure the directory exists
    if not exists(directory):
        makedirs(directory)

    return directory


APP_NAME = "python_2d_game_engine"

# Directory paths
JSONS_DIR_PATH: str = get_os_specific_directory(APP_NAME)
JSONS_PROJ_DIR_PATH: str = "jsons"
JSONS_ROOMS_PROJ_SUB_DIR_PATH: str = "rooms"
JSONS_ROOMS_DIR_PATH = join(JSONS_PROJ_DIR_PATH, JSONS_ROOMS_PROJ_SUB_DIR_PATH)
PNGS_DIR_PATH: str = "pngs"
OGGS_DIR_PATH: str = "oggs"

# Creating the dictionaries
PNGS_PATHS_DICT: dict[str, str] = create_paths_dict(PNGS_DIR_PATH)
OGGS_PATHS_DICT: dict[str, str] = create_paths_dict(OGGS_DIR_PATH)

# FPS
FPS: int = 60

# Fixed dimensions
TILE_SIZE: int = 16

WORLD_CELL_SIZE: int = 8
WORLD_WIDTH_RU: int = 35
WORLD_HEIGHT_RU: int = 22
WORLD_WIDTH: int = WORLD_WIDTH_RU * WORLD_CELL_SIZE
WORLD_HEIGHT: int = WORLD_HEIGHT_RU * WORLD_CELL_SIZE

WINDOW_WIDTH: int = 320
WINDOW_HEIGHT: int = 180

NATIVE_WIDTH: int = 320
NATIVE_HEIGHT: int = 180

NATIVE_HALF_WIDTH: int = int(WINDOW_WIDTH // 2)
NATIVE_HALF_HEIGHT: int = int(WINDOW_HEIGHT // 2)

NATIVE_WIDTH_TU: int = int(NATIVE_WIDTH // TILE_SIZE)

ROOM_WIDTH_TU: int = 20
ROOM_HEIGHT_TU: int = 11
ROOM_WIDTH: int = ROOM_WIDTH_TU * TILE_SIZE
ROOM_HEIGHT: int = ROOM_HEIGHT_TU * TILE_SIZE

# Native surf and rect will never be mutated
NATIVE_SURF: pg.Surface = pg.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
NATIVE_RECT: pg.Rect = NATIVE_SURF.get_rect()

# Clock never changes
CLOCK: pg.time.Clock = pg.time.Clock()

# Event ints list (used by event for loop)
EVENTS: list[int] = [
    pg.KEYDOWN,
    pg.KEYUP,
    pg.QUIT,
    # REMOVE IN BUILD
    # Because production don't use the mouse
    pg.MOUSEBUTTONUP,
    pg.MOUSEBUTTONDOWN,
]

# Font dimensions and instance
FONT_HEIGHT: int = 5
FONT_WIDTH: int = 3
FONT: font.Font = font.Font(
    join("ttf", "cg_pixel_3x5_mono.ttf"),
    FONT_HEIGHT,
)

# Quadtree recursion limit
MAX_QUADTREE_DEPTH: int = 8

# REMOVE IN BUILD
# This is for room editor autotile mapping
SPRITE_TILE_TYPE_NORMAL_BINARY_VALUE_TO_OFFSET_DICT: dict[int, dict[str, int]] = {
    208: {
        "x": TILE_SIZE * 0,
        "y": TILE_SIZE * 0,
    },
    248: {
        "x": TILE_SIZE * 1,
        "y": TILE_SIZE * 0,
    },
    104: {
        "x": TILE_SIZE * 2,
        "y": TILE_SIZE * 0,
    },
    64: {
        "x": TILE_SIZE * 3,
        "y": TILE_SIZE * 0,
    },
    80: {
        "x": TILE_SIZE * 4,
        "y": TILE_SIZE * 0,
    },
    120: {
        "x": TILE_SIZE * 5,
        "y": TILE_SIZE * 0,
    },
    216: {
        "x": TILE_SIZE * 6,
        "y": TILE_SIZE * 0,
    },
    72: {
        "x": TILE_SIZE * 7,
        "y": TILE_SIZE * 0,
    },
    88: {
        "x": TILE_SIZE * 8,
        "y": TILE_SIZE * 0,
    },
    219: {
        "x": TILE_SIZE * 9,
        "y": TILE_SIZE * 0,
    },
    214: {
        "x": TILE_SIZE * 0,
        "y": TILE_SIZE * 1,
    },
    255: {
        "x": TILE_SIZE * 1,
        "y": TILE_SIZE * 1,
    },
    107: {
        "x": TILE_SIZE * 2,
        "y": TILE_SIZE * 1,
    },
    66: {
        "x": TILE_SIZE * 3,
        "y": TILE_SIZE * 1,
    },
    86: {
        "x": TILE_SIZE * 4,
        "y": TILE_SIZE * 1,
    },
    127: {
        "x": TILE_SIZE * 5,
        "y": TILE_SIZE * 1,
    },
    223: {
        "x": TILE_SIZE * 6,
        "y": TILE_SIZE * 1,
    },
    75: {
        "x": TILE_SIZE * 7,
        "y": TILE_SIZE * 1,
    },
    95: {
        "x": TILE_SIZE * 8,
        "y": TILE_SIZE * 1,
    },
    126: {
        "x": TILE_SIZE * 9,
        "y": TILE_SIZE * 1,
    },
    22: {
        "x": TILE_SIZE * 0,
        "y": TILE_SIZE * 2,
    },
    31: {
        "x": TILE_SIZE * 1,
        "y": TILE_SIZE * 2,
    },
    11: {
        "x": TILE_SIZE * 2,
        "y": TILE_SIZE * 2,
    },
    2: {
        "x": TILE_SIZE * 3,
        "y": TILE_SIZE * 2,
    },
    210: {
        "x": TILE_SIZE * 4,
        "y": TILE_SIZE * 2,
    },
    251: {
        "x": TILE_SIZE * 5,
        "y": TILE_SIZE * 2,
    },
    254: {
        "x": TILE_SIZE * 6,
        "y": TILE_SIZE * 2,
    },
    106: {
        "x": TILE_SIZE * 7,
        "y": TILE_SIZE * 2,
    },
    250: {
        "x": TILE_SIZE * 8,
        "y": TILE_SIZE * 2,
    },
    218: {
        "x": TILE_SIZE * 9,
        "y": TILE_SIZE * 2,
    },
    122: {
        "x": TILE_SIZE * 10,
        "y": TILE_SIZE * 2,
    },
    16: {
        "x": TILE_SIZE * 0,
        "y": TILE_SIZE * 3,
    },
    24: {
        "x": TILE_SIZE * 1,
        "y": TILE_SIZE * 3,
    },
    8: {
        "x": TILE_SIZE * 2,
        "y": TILE_SIZE * 3,
    },
    0: {
        "x": TILE_SIZE * 3,
        "y": TILE_SIZE * 3,
    },
    18: {
        "x": TILE_SIZE * 4,
        "y": TILE_SIZE * 3,
    },
    27: {
        "x": TILE_SIZE * 5,
        "y": TILE_SIZE * 3,
    },
    30: {
        "x": TILE_SIZE * 6,
        "y": TILE_SIZE * 3,
    },
    10: {
        "x": TILE_SIZE * 7,
        "y": TILE_SIZE * 3,
    },
    26: {
        "x": TILE_SIZE * 8,
        "y": TILE_SIZE * 3,
    },
    94: {
        "x": TILE_SIZE * 9,
        "y": TILE_SIZE * 3,
    },
    91: {
        "x": TILE_SIZE * 10,
        "y": TILE_SIZE * 3,
    },
    82: {
        "x": TILE_SIZE * 4,
        "y": TILE_SIZE * 4,
    },
    123: {
        "x": TILE_SIZE * 5,
        "y": TILE_SIZE * 4,
    },
    222: {
        "x": TILE_SIZE * 6,
        "y": TILE_SIZE * 4,
    },
    74: {
        "x": TILE_SIZE * 7,
        "y": TILE_SIZE * 4,
    },
    90: {
        "x": TILE_SIZE * 8,
        "y": TILE_SIZE * 4,
    },
}

SPRITE_TILE_TYPE_TOP_BOTTOM_BINARY_VALUE_TO_OFFSET_DICT: dict[int, dict[str, int]] = {
    208: {
        "x": TILE_SIZE * 0,
        "y": TILE_SIZE * 0,
    },
    248: {
        "x": TILE_SIZE * 1,
        "y": TILE_SIZE * 0,
    },
    104: {
        "x": TILE_SIZE * 2,
        "y": TILE_SIZE * 0,
    },
    214: {
        "x": TILE_SIZE * 0,
        "y": TILE_SIZE * 1,
    },
    255: {
        "x": TILE_SIZE * 1,
        "y": TILE_SIZE * 1,
    },
    107: {
        "x": TILE_SIZE * 2,
        "y": TILE_SIZE * 1,
    },
    22: {
        "x": TILE_SIZE * 0,
        "y": TILE_SIZE * 1,
    },
    31: {
        "x": TILE_SIZE * 1,
        "y": TILE_SIZE * 1,
    },
    11: {
        "x": TILE_SIZE * 2,
        "y": TILE_SIZE * 1,
    },
}

# REMOVE IN BUILD
# This is for frame by frame debug tool
NEXT_FRAME: int = pg.K_8
