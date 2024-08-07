from json import dump
from json import load
from os.path import join
from typing import Any

from actors.stage_1_clouds import Stage1Clouds
from actors.stage_1_colonnade import Stage1Colonnade
from actors.stage_1_glow import Stage1Glow
from actors.stage_1_pine_trees import Stage1PineTrees
from actors.stage_1_sky import Stage1Sky
from constants import create_paths_dict
from constants import DEFAULT_SETTINGS_DICT
from constants import JSONS_DIR_PATH
from constants import JSONS_PROJ_DIR_PATH
from constants import JSONS_ROOMS_DIR_PATH
from constants import NATIVE_WIDTH
from constants import OGGS_PATHS_DICT
from constants import pg
from constants import WINDOW_HEIGHT
from constants import WINDOW_WIDTH
from nodes.debug_draw import DebugDraw
from nodes.event_handler import EventHandler
from nodes.music_manager import MusicManager
from nodes.sound_manager import SoundManager
from pygame.math import clamp
from scenes.animation_json_generator import AnimationJsonGenerator
from scenes.created_by_splash_screen import CreatedBySplashScreen
from scenes.made_with_splash_screen import MadeWithSplashScreen
from scenes.main_menu import MainMenu
from scenes.room_json_generator import RoomJsonGenerator
from scenes.sprite_sheet_json_generator import SpriteSheetJsonGenerator
from scenes.title_screen import TitleScreen
from typeguard import typechecked


@typechecked
class Game:
    def __init__(self, initial_scene: str):
        # Prepare local settings data
        self.local_settings_dict: dict[str, int] = DEFAULT_SETTINGS_DICT

        # jsons file paths dict, read disk and populate this dict, dynamic values
        self.jsons_pahts_dict: dict[str, str] = create_paths_dict(JSONS_DIR_PATH)
        self.jsons_proj_pahts_dict: dict[str, str] = create_paths_dict(JSONS_PROJ_DIR_PATH)
        self.jsons_proj_rooms_pahts_dict: dict[str, str] = create_paths_dict(JSONS_ROOMS_DIR_PATH)

        # Update local settings dict
        self.load_or_create_settings()

        # Flags.
        # Options menu flag, toggle options menu mode
        self.is_options_menu_active: bool = False
        # REMOVE IN BUILD
        # Toggle drawing debug data
        self.is_debug: bool = False
        # REMOVE IN BUILD
        # The thing that does the actual debug data drawing
        self.debug_draw: DebugDraw = DebugDraw()
        # REMOVE IN BUILD
        # Toggle frame per frame debug mode
        self.is_per_frame: bool = False

        # Window resolution scale, size, y offset
        # Y offset because native is shorter than window
        # Default values
        self.window_width: int = WINDOW_WIDTH * self.local_settings_dict["resolution_scale"]
        self.window_height: int = WINDOW_HEIGHT * self.local_settings_dict["resolution_scale"]
        self.window_surf: (None | pg.Surface) = None
        self.set_resolution_index(self.local_settings_dict["resolution_index"])

        # Handles sounds
        self.sound_manager: SoundManager = SoundManager()
        self.music_manager: MusicManager = MusicManager()

        # Load all oggs
        # TODO: Load when needed only in each scenes
        for ogg_name, ogg_path in OGGS_PATHS_DICT.items():
            self.sound_manager.load_sound(ogg_name, ogg_path)

        # Handle events
        self.event_handler: EventHandler = EventHandler(self)

        self.stage_actors: dict[str, dict[str, Any]] = {
            "stage_1_sprite_sheet.png": {
                "Fire": CreatedBySplashScreen,
            }
        }

        self.stage_surf_names: dict[str, list[str]] = {"stage_1_sprite_sheet.png": ["thin_fire_sprite_sheet.png"]}

        self.stage_animation_jsons: dict[str, list[str]] = {
            # sprite_sheet_png_name : surf name
            "stage_1_sprite_sheet.png": ["thin_fire_animation.json"]
        }

        self.stage_parallax_background_memory_dict: dict[str, dict[str, Any]] = {
            # sprite_sheet_png_name : surf name
            "stage_1_sprite_sheet.png": {
                "clouds": Stage1Clouds,
                "colonnade": Stage1Colonnade,
                "glow": Stage1Glow,
                "pine_trees": Stage1PineTrees,
                "sky": Stage1Sky,
            }
        }

        # All scenes dict, name to memory
        self.scenes: dict[str, Any] = {
            "CreatedBySplashScreen": CreatedBySplashScreen,
            "MadeWithSplashScreen": MadeWithSplashScreen,
            "TitleScreen": TitleScreen,
            "MainMenu": MainMenu,
            "AnimationJsonGenerator": AnimationJsonGenerator,
            "SpriteSheetJsonGenerator": SpriteSheetJsonGenerator,
            "RoomJsonGenerator": RoomJsonGenerator,
        }

        # Keeps track of current scene
        self.current_scene: Any = self.scenes[initial_scene](self)

    def update_jsons_proj_rooms_pahts_dict(self) -> None:
        self.jsons_proj_pahts_dict = create_paths_dict(JSONS_ROOMS_DIR_PATH)

    def update_jsons_proj_paths_dict(self) -> None:
        self.jsons_proj_pahts_dict = create_paths_dict(JSONS_PROJ_DIR_PATH)

    def update_jsons_paths_dict(self) -> None:
        self.jsons_pahts_dict = create_paths_dict(JSONS_DIR_PATH)

    def load_or_create_settings(self) -> None:
        """
        Load to local or create and then load.
        """

        # Got settings file on disk?
        try:
            # Load it
            exists = self.jsons_pahts_dict["settings.json"]
            with open(exists, "r") as settings_json:
                self.local_settings_dict = load(settings_json)
        # No settings file on disk?
        except (KeyError, FileNotFoundError):
            with open(
                # Create new file
                join(JSONS_DIR_PATH, "settings.json"),
                "w",
            ) as settings_json:
                # Create one to disk. Load to local
                self.local_settings_dict = DEFAULT_SETTINGS_DICT
                dump(self.local_settings_dict, settings_json, separators=(",", ":"))
            self.update_jsons_paths_dict()

    def save_settings(self) -> None:
        """
        Dump my local saves to disk.
        """

        with open(self.jsons_pahts_dict["settings.json"], "w") as settings_json:
            dump(self.local_settings_dict, settings_json, separators=(",", ":"))

    def set_is_options_menu_active(self, value: bool) -> None:
        """
        If options screen is active, current scene is not updated.
        """

        self.is_options_menu_active = value

    def set_resolution_index(self, value: int) -> None:
        """
        Sets the resolution scale of the window.
        Takes int parameter, 0 - 6 only.
        """

        # Keep safe
        value = int(clamp(value, 0.0, 6.0))

        # Full screen
        if value == 6:
            self.local_settings_dict["resolution_index"] = value
            # Set window surf to be fullscreen size
            self.window_surf = pg.display.set_mode(
                (0, 0),
                pg.FULLSCREEN,
            )
            # Update self.local_settings_dict["resolution_scale"]
            self.local_settings_dict["resolution_scale"] = self.window_surf.get_width() // NATIVE_WIDTH
            # Update window size, surf and y offset
            self.window_width = self.window_surf.get_width()
            self.window_height = self.window_surf.get_height()
            return

        # Not fullscreen
        # Update self.local_settings_dict["resolution_scale"]
        self.local_settings_dict["resolution_index"] = value
        self.local_settings_dict["resolution_scale"] = value + 1
        # Update window size, surf and y offset
        self.window_width = WINDOW_WIDTH * self.local_settings_dict["resolution_scale"]
        self.window_height = WINDOW_HEIGHT * self.local_settings_dict["resolution_scale"]
        self.window_surf = pg.display.set_mode((self.window_width, self.window_height))

    def set_scene(self, value: str) -> None:
        """
        Sets the current scene with a new scene instance.
        """

        self.current_scene = self.scenes[value](self)
