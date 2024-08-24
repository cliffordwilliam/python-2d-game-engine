from os import environ
from os.path import join
from typing import Any

import pygame as pg
import pygame.freetype as font
from utils import create_paths_dict
from utils import get_os_specific_directory

# Setting to center window
environ["SDL_VIDEO_CENTERED"] = "1"

# Initialize pygame
pg.init()

# Default game settings
DEFAULT_SETTINGS_DICT: dict[str, Any] = {
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

SETTINGS_FILE_NAME: str = "settings.json"


# This repo name, saved in user machine
APP_NAME = "python_2d_game_engine"

# Dir paths
JSONS_USER_DIR_PATH: str = get_os_specific_directory(APP_NAME)
JSONS_REPO_DIR_PATH: str = "jsons"
JSONS_ROOMS_REPO_SUB_DIR_PATH: str = "rooms"
JSONS_ROOMS_DIR_PATH = join(JSONS_REPO_DIR_PATH, JSONS_ROOMS_REPO_SUB_DIR_PATH)
PNGS_DIR_PATH: str = "pngs"
OGGS_DIR_PATH: str = "oggs"

# Creating the constant path dicts, the dynamic ones are made in game as its prop
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

MAX_RESOLUTION_INDEX: int = 6

# Native surf and rect are never changes
NATIVE_SURF: pg.Surface = pg.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
NATIVE_RECT: pg.Rect = NATIVE_SURF.get_rect()

# Clock never changes
CLOCK: pg.time.Clock = pg.time.Clock()

# List of events to listen to (used by game event for loop)
EVENTS: list[int] = [
    pg.KEYDOWN,
    pg.KEYUP,
    pg.QUIT,
    # REMOVE IN BUILD
    # Because production don't use the mouse
    pg.MOUSEBUTTONUP,
    pg.MOUSEBUTTONDOWN,
]

# Font dimensions and instance, this game uses 1 font
FONT_HEIGHT: int = 5
FONT_WIDTH: int = 3
FONT: font.Font = font.Font(
    join("ttf", "cg_pixel_3x5_mono.ttf"),
    FONT_HEIGHT,
)

# Quadtree recursion limit
MAX_QUADTREE_DEPTH: int = 8

# REMOVE IN BUILD
# This is binary mapped to offset, for normal blob autotiles
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

# This is binary mapped to offset, for square blob autotiles
SPRITE_TILE_TYPE_SQUARE_BINARY_VALUE_TO_OFFSET_DICT: dict[int, dict[str, int]] = {
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

# This is binary mapped to offset, for vertical autotiles
SPRITE_TILE_TYPE_VERTICAL_BINARY_VALUE_TO_OFFSET_DICT: dict[int, dict[str, int]] = {
    64: {
        "x": TILE_SIZE * 0,
        "y": TILE_SIZE * 0,
    },
    66: {
        "x": TILE_SIZE * 0,
        "y": TILE_SIZE * 1,
    },
    2: {
        "x": TILE_SIZE * 0,
        "y": TILE_SIZE * 2,
    },
}

# This is binary mapped to offset, for horizontal blob autotiles
SPRITE_TILE_TYPE_HORIZONTAL_BINARY_VALUE_TO_OFFSET_DICT: dict[int, dict[str, int]] = {
    16: {
        "x": TILE_SIZE * 0,
        "y": TILE_SIZE * 0,
    },
    24: {
        "x": TILE_SIZE * 1,
        "y": TILE_SIZE * 0,
    },
    8: {
        "x": TILE_SIZE * 2,
        "y": TILE_SIZE * 0,
    },
}

# For easy access, name mapped to binary offset dict above
SPRITE_TILE_TYPE_BINARY_TO_OFFSET_DICT: dict[str, dict[int, dict[str, int]]] = {
    "normal": SPRITE_TILE_TYPE_NORMAL_BINARY_VALUE_TO_OFFSET_DICT,
    "square": SPRITE_TILE_TYPE_SQUARE_BINARY_VALUE_TO_OFFSET_DICT,
    "vertical": SPRITE_TILE_TYPE_VERTICAL_BINARY_VALUE_TO_OFFSET_DICT,
    "horizontal": SPRITE_TILE_TYPE_HORIZONTAL_BINARY_VALUE_TO_OFFSET_DICT,
}

# To check neighbor in all direction
SPRITE_ALL_ADJACENT_NEIGHBOR_DIRECTIONS: list[tuple[tuple[int, int], int]] = [
    ((-1, -1), 1),  # North West
    ((0, -1), 2),  # North
    ((1, -1), 4),  # North East
    ((-1, 0), 8),  # West
    ((1, 0), 16),  # East
    ((-1, 1), 32),  # South West
    ((0, 1), 64),  # South
    ((1, 1), 128),  # South East
]

# To check neighbor in top and bottom
SPRITE_TOP_BOTTOM_ADJACENT_NEIGHBOR_DIRECTIONS: list[tuple[tuple[int, int], int]] = [
    ((0, -1), 2),  # North
    ((0, 1), 64),  # South
]

# To check neighbor in left and right
SPRITE_LEFT_RIGHT_ADJACENT_NEIGHBOR_DIRECTIONS: list[tuple[tuple[int, int], int]] = [
    ((-1, 0), 8),  # West
    ((1, 0), 16),  # East
]

# For easy access, name mapped to neighbor direction checks above
SPRITE_TILE_TYPE_SPRITE_ADJACENT_NEIGHBOR_DIRECTIONS_LIST: dict[str, list[tuple[tuple[int, int], int]]] = {
    "normal": SPRITE_ALL_ADJACENT_NEIGHBOR_DIRECTIONS,
    "square": SPRITE_ALL_ADJACENT_NEIGHBOR_DIRECTIONS,
    "vertical": SPRITE_TOP_BOTTOM_ADJACENT_NEIGHBOR_DIRECTIONS,
    "horizontal": SPRITE_LEFT_RIGHT_ADJACENT_NEIGHBOR_DIRECTIONS,
}

# REMOVE IN BUILD
# This is for frame by frame debug tool next frame key trigger
NEXT_FRAME: int = pg.K_8
