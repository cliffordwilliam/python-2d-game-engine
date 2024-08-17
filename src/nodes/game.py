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
from constants import JSONS_REPO_DIR_PATH
from constants import JSONS_ROOMS_DIR_PATH
from constants import JSONS_USER_DIR_PATH
from constants import MAX_RESOLUTION_INDEX
from constants import NATIVE_WIDTH
from constants import OGGS_PATHS_DICT
from constants import pg
from constants import SETTINGS_FILE_NAME
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

        # Dynamic dict paths (save data, room editor, so on)
        self.jsons_user_pahts_dict: dict[str, str] = create_paths_dict(JSONS_USER_DIR_PATH)
        self.jsons_repo_pahts_dict: dict[str, str] = create_paths_dict(JSONS_REPO_DIR_PATH)
        self.jsons_repo_rooms_pahts_dict: dict[str, str] = create_paths_dict(JSONS_ROOMS_DIR_PATH)

        # Event handler
        self.event_handler: EventHandler = EventHandler(self)

        # Update local settings dict
        self.GET_or_POST_settings_json_from_disk()

        # Window resolution scale and size
        self.window_width: int = WINDOW_WIDTH * self.get_one_local_settings_dict_value("resolution_scale")
        self.window_height: int = WINDOW_HEIGHT * self.get_one_local_settings_dict_value("resolution_scale")
        self.window_surf: (None | pg.Surface) = None
        self.set_resolution_index(self.get_one_local_settings_dict_value("resolution_index"))

        # Flags
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

        # Sound and music managers
        self.sound_manager: SoundManager = SoundManager()
        self.music_manager: MusicManager = MusicManager()

        # Load all oggs
        # TODO: Load when needed only in each scenes
        for ogg_name, ogg_path in OGGS_PATHS_DICT.items():
            self.sound_manager.load_sound(ogg_name, ogg_path)

        # Bind each actor mems to the stage sprite sheet name
        self.stage_actors: dict[str, dict[str, Any]] = {
            "stage_1_sprite_sheet.png": {
                "Fire": CreatedBySplashScreen,
            }
        }

        # Bind each sprite sheet names to the stage sprite sheet name
        self.stage_surf_names: dict[str, dict[str, str]] = {"stage_1_sprite_sheet.png": {"Fire": "thin_fire_sprite_sheet.png"}}

        # Bind each sprite animation json names to the stage sprite sheet name
        self.stage_animation_jsons: dict[str, dict[str, str]] = {"stage_1_sprite_sheet.png": {"Fire": "thin_fire_animation.json"}}

        # Bind each parallax mems to the stage sprite sheet name
        self.stage_parallax_background_memory_dict: dict[str, dict[str, Any]] = {
            "stage_1_sprite_sheet.png": {
                "clouds": Stage1Clouds,
                "colonnade": Stage1Colonnade,
                "glow": Stage1Glow,
                "pine_trees": Stage1PineTrees,
                "sky": Stage1Sky,
            }
        }

        # All screen scenes dict, its name to its memory
        self.scenes: dict[str, Any] = {
            "CreatedBySplashScreen": CreatedBySplashScreen,
            "MadeWithSplashScreen": MadeWithSplashScreen,
            "TitleScreen": TitleScreen,
            "MainMenu": MainMenu,
            # REMOVE IN BUILD
            "AnimationJsonGenerator": AnimationJsonGenerator,
            "SpriteSheetJsonGenerator": SpriteSheetJsonGenerator,
            "RoomJsonGenerator": RoomJsonGenerator,
        }

        # Keeps track of current scene instance
        self.current_scene: Any = self.scenes[initial_scene](self)

    def _update_dynamic_paths_dict(self) -> None:
        """
        Called by POST and DELETE to disk.
        Reread current dynamic dir, adds new state to dict path.
        Content may have been added or deleted.
        """

        self.jsons_user_pahts_dict = create_paths_dict(JSONS_USER_DIR_PATH)
        self.jsons_repo_pahts_dict = create_paths_dict(JSONS_REPO_DIR_PATH)
        self.jsons_repo_rooms_pahts_dict = create_paths_dict(JSONS_ROOMS_DIR_PATH)

    def GET_or_POST_settings_json_from_disk(self) -> None:
        """
        GET prev saved disk.
        Or.
        Post default to disk.
        Overwrites game local settings with defaut.
        """

        # If that file is not in dynamic dict, it has not been POST yet
        # Because only POST updates dynamic dict
        if SETTINGS_FILE_NAME in self.jsons_user_pahts_dict:
            value = self.GET_file_from_disk_dynamic_path(self.jsons_user_pahts_dict[SETTINGS_FILE_NAME])
            self.overwriting_local_settings_dict(value)
        else:
            # POST new settings with game local settings (game local starts off defaullt always)
            self.POST_file_to_disk_dynamic_path(
                join(JSONS_USER_DIR_PATH, SETTINGS_FILE_NAME),
                self.get_local_settings_dict(),
            )

    def GET_file_from_disk_dynamic_path(self, existing_dynamic_path: str) -> Any:
        """
        GET file to user disk.
        """
        is_in_jsons_user_pahts_dict = existing_dynamic_path in self.jsons_user_pahts_dict.values()
        is_in_jsons_repo_pahts_dict = existing_dynamic_path in self.jsons_repo_pahts_dict.values()
        is_in_jsons_repo_rooms_pahts_dict = existing_dynamic_path in self.jsons_repo_rooms_pahts_dict.values()

        if not is_in_jsons_user_pahts_dict and not is_in_jsons_repo_pahts_dict and not is_in_jsons_repo_rooms_pahts_dict:
            raise KeyError("Path does not exists")

        with open(existing_dynamic_path, "r") as file:
            data = load(file)
            return data

    def PATCH_file_to_disk_dynamic_path(self, existing_dynamic_path: str, file_content: Any) -> None:
        """
        POST file to user disk.
        """

        is_in_jsons_user_pahts_dict = existing_dynamic_path in self.jsons_user_pahts_dict.values()
        is_in_jsons_repo_pahts_dict = existing_dynamic_path in self.jsons_repo_pahts_dict.values()
        is_in_jsons_repo_rooms_pahts_dict = existing_dynamic_path in self.jsons_repo_rooms_pahts_dict.values()

        if not is_in_jsons_user_pahts_dict and not is_in_jsons_repo_pahts_dict and not is_in_jsons_repo_rooms_pahts_dict:
            raise KeyError("Path does not exists")

        with open(
            existing_dynamic_path,
            "w",
        ) as file:
            # POST to user disk
            dump(file_content, file, separators=(",", ":"))
        # After POST / DELETE in user disk, call this
        self._update_dynamic_paths_dict()

    def POST_file_to_disk_dynamic_path(self, new_dynamic_path: str, file_content: Any) -> None:
        """
        POST file to user disk.
        """

        with open(
            new_dynamic_path,
            "w",
        ) as file:
            # POST to user disk
            dump(file_content, file, separators=(",", ":"))
        # After POST / DELETE in user disk, call this
        self._update_dynamic_paths_dict()

    def overwriting_local_settings_dict(self, new_settings: dict) -> None:
        """
        Overwrite local settings dict, need exact same shape.
        """

        # Ensure that all required keys are present
        for key in DEFAULT_SETTINGS_DICT:
            if key not in new_settings:
                raise KeyError(f"Missing required key: '{key}'")

        # Ensure that no extra keys are present
        for key in new_settings:
            if key not in DEFAULT_SETTINGS_DICT:
                raise KeyError(f"Invalid key: '{key}'")

        # Ensure that the new dictionary has valid values
        for key, value in new_settings.items():
            # Get the expected type from DEFAULT_SETTINGS_DICT
            expected_type = type(DEFAULT_SETTINGS_DICT[key])

            # Check if the value matches the expected type
            if not isinstance(value, expected_type):
                raise TypeError(f"Key '{key}' expects a value of type {expected_type.__name__}, but got {type(value).__name__}.")

        # If all checks pass, overwrite the current settings
        self.local_settings_dict.update(new_settings)

        # Update event handler function binds, in case event key was changed
        self.event_handler.bind_game_local_setting_key_with_input_flag_setter()

    def set_one_local_settings_dict_value(self, key: str, value: Any) -> None:
        """
        Set a value to local settings dict. Need to be same type.
        """

        # Check if the key exists in the DEFAULT_SETTINGS_DICT
        if key not in DEFAULT_SETTINGS_DICT:
            raise KeyError(f"Invalid key: '{key}'")

        # Get the expected type from DEFAULT_SETTINGS_DICT
        expected_type = type(DEFAULT_SETTINGS_DICT[key])

        # Check if the value matches the expected type
        if not isinstance(value, expected_type):
            raise TypeError(f"Key '{key}' expects a value of type {expected_type.__name__}, but got {type(value).__name__}.")

        # Set the new value
        self.local_settings_dict[key] = value

        # Update event handler function binds, in case event key was changed
        self.event_handler.bind_game_local_setting_key_with_input_flag_setter()

    def get_one_local_settings_dict_value(self, key: str) -> Any:
        """
        Get a value from local settings dict.
        """

        # Check if the key exists in the DEFAULT_SETTINGS_DICT
        if key not in DEFAULT_SETTINGS_DICT:
            raise KeyError(f"Invalid key: '{key}'")

        # Return the value for the key
        return self.local_settings_dict.get(key, None)

    def get_local_settings_dict(self) -> Any:
        """
        Get local settings dict.
        """

        return self.local_settings_dict

    def set_is_options_menu_active(self, value: bool) -> None:
        """
        Toggle options screen on / off.
        If options screen is active, current scene is not updated.
        """

        self.is_options_menu_active = value

    def set_resolution_index(self, value: int) -> None:
        """
        Sets the resolution scale of the window.
        Takes int parameter, 0 - 6 only.
        Updates:
        - window surf prop.
        - window size prop.
        - game local settings.
        """

        # Keeps safe
        value = int(clamp(value, 0, MAX_RESOLUTION_INDEX))

        # Get scale and index
        value_index = value
        value_scale = value + 1

        # Full screen
        if value == MAX_RESOLUTION_INDEX:
            # Set window surf size
            self.window_surf = pg.display.set_mode(
                (0, 0),
                pg.FULLSCREEN,
            )
            # Update window size
            self.window_width = self.window_surf.get_width()
            self.window_height = self.window_surf.get_height()
            # Update game local settings
            self.set_one_local_settings_dict_value("resolution_index", value_index)
            self.set_one_local_settings_dict_value("resolution_scale", self.window_surf.get_width() // NATIVE_WIDTH)
            return

        # Not fullscreen
        # Set window surf size
        self.window_surf = pg.display.set_mode(
            (
                WINDOW_WIDTH * value_scale,
                WINDOW_HEIGHT * value_scale,
            )
        )
        # Update window size
        self.window_width = self.window_surf.get_width()
        self.window_height = self.window_surf.get_height()
        # Update game local settings
        self.set_one_local_settings_dict_value("resolution_index", value_index)
        self.set_one_local_settings_dict_value("resolution_scale", value_scale)

    def set_scene(self, value: str) -> None:
        """
        Sets the current scene with a new scene instance.
        """

        self.current_scene = self.scenes[value](self)
