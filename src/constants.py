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

# Room json properties
ROOM_JSON_PROPERTIES = ["room_x_ru", "room_y_ru", "room_scale_x", "room_scale_y"]

# FPS
FPS: int = 60

# Fixed dimensions
TILE_SIZE: int = 16

WORLD_CELL_SIZE: int = 8
WORLD_WIDTH_TU: int = 35
WORLD_HEIGHT_TU: int = 22
WORLD_WIDTH: int = WORLD_WIDTH_TU * WORLD_CELL_SIZE
WORLD_HEIGHT: int = WORLD_HEIGHT_TU * WORLD_CELL_SIZE

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
MASK_ID_TO_INDEX: dict[str, int] = {
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
# This is for frame by frame debug tool
NEXT_FRAME: int = pg.K_8
