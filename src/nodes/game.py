from json import dump
from json import load
from os.path import join
from typing import Any

from actors.stage_1_clouds import Stage1Clouds
from actors.stage_1_colonnade import Stage1Colonnade
from actors.stage_1_glow import Stage1Glow
from actors.stage_1_pine_trees import Stage1PineTrees
from actors.stage_1_sky import Stage1Sky
from constants import DEFAULT_SETTINGS_DICT
from constants import JSONS_REPO_DIR_PATH
from constants import JSONS_ROOMS_DIR_PATH
from constants import JSONS_USER_DIR_PATH
from constants import MAX_RESOLUTION_INDEX
from constants import NATIVE_WIDTH
from constants import OGGS_PATHS_DICT
from constants import pg
from constants import PNGS_PATHS_DICT
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
from schemas import AnimationMetadata
from schemas import instance_animation_metadata
from schemas import SETTINGS_SCHEMA
from schemas import validate_json
from typeguard import typechecked
from utils import create_paths_dict
from utils import get_one_target_dict_value


@typechecked
class Game:
    def __init__(self, initial_scene: str):
        # Prepare local settings with default settings
        self.local_settings_dict: dict[str, int] = DEFAULT_SETTINGS_DICT

        # Dynamic paths dict (for player save data slot, room JSON metadata, animation JSON metadata, ...)
        self.jsons_user_pahts_dict: dict[str, str] = create_paths_dict(JSONS_USER_DIR_PATH)
        self.jsons_repo_pahts_dict: dict[str, str] = create_paths_dict(JSONS_REPO_DIR_PATH)
        self.jsons_repo_rooms_pahts_dict: dict[str, str] = create_paths_dict(JSONS_ROOMS_DIR_PATH)

        # Event handler
        self.event_handler: EventHandler = EventHandler(self)

        # Update local settings dict with disk settings
        self.GET_or_POST_settings_json_from_disk()

        # Window size, surf and resolution scale
        self.window_width: int = WINDOW_WIDTH * self.get_one_local_settings_dict_value("resolution_scale")
        self.window_height: int = WINDOW_HEIGHT * self.get_one_local_settings_dict_value("resolution_scale")
        self.window_surf: (None | pg.Surface) = None
        self.set_resolution_index(self.get_one_local_settings_dict_value("resolution_index"))

        # Flags
        self.is_options_menu_active: bool = False
        # REMOVE IN BUILD
        self.is_per_frame_debug: bool = False

        # REMOVE IN BUILD
        self.debug_draw: DebugDraw = DebugDraw()

        # Sound and music managers
        self.sound_manager: SoundManager = SoundManager()
        self.music_manager: MusicManager = MusicManager()

        # Load all oggs
        # TODO: Load when needed only in each scenes
        for ogg_name, ogg_path in OGGS_PATHS_DICT.items():
            self.sound_manager.load_sound(ogg_name, ogg_path)

        # Map sprite sheet names to stage sprite sheet name
        self.sprite_sheet_static_actor_surfs_dict: dict[str, dict[str, str]] = {
            "stage_1_sprite_sheet.png": {
                # Static actor name : static actor surf name
                "thin_fire": "thin_fire_sprite_sheet.png",
                "thin_waterfall": "thin_waterfall_sprite_sheet.png",
            }
        }

        # Map sprite animation JSON names to stage sprite sheet name
        self.sprite_sheet_static_actor_jsons_dict: dict[str, dict[str, str]] = {
            "stage_1_sprite_sheet.png": {
                # Static actor name : static actor JSON name
                "thin_fire": "thin_fire_animation.json",
                "thin_waterfall": "thin_waterfall_animation.json",
            }
        }

        # Map parallax memory to stage sprite sheet name
        self.sprite_sheet_parallax_background_mems_dict: dict[str, dict[str, Any]] = {
            "stage_1_sprite_sheet.png": {
                "clouds": Stage1Clouds,
                "colonnade": Stage1Colonnade,
                "glow": Stage1Glow,
                "pine_trees": Stage1PineTrees,
                "sky": Stage1Sky,
            }
        }

        # All scenes dict, name key to memory
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

        # Current scene instance
        self.current_scene: Any = self.scenes[initial_scene](self)

    # Helper
    def _update_dynamic_paths_dict(self) -> None:
        """
        Called by POST or DELETE to disk dir.

        Reread edited disk dir content, repopulate dynamic paths dict.
        """

        self.jsons_user_pahts_dict = create_paths_dict(JSONS_USER_DIR_PATH)
        self.jsons_repo_pahts_dict = create_paths_dict(JSONS_REPO_DIR_PATH)
        self.jsons_repo_rooms_pahts_dict = create_paths_dict(JSONS_ROOMS_DIR_PATH)

    # Abilities
    def get_sprite_sheet_static_actor_jsons_dict(self, stage_sprite_sheet_name: str) -> dict[str, dict[str, AnimationMetadata]]:
        """
        | Stage sprite sheet name is key
        | Key for a dict filled with {actor names : JSON names}
        |
        | Raises exception if passed stage sprite sheet name is invalid
        |
        | I turn {actor names : JSON names} into {actor names : {animation names : metadata}} as output
        """

        # {actor names : JSON names}
        actor_name_to_json_name_dict: dict[str, str] = get_one_target_dict_value(
            stage_sprite_sheet_name,
            self.sprite_sheet_static_actor_jsons_dict,
            "self.sprite_sheet_static_actor_jsons_dict",
        )

        # Prepare {actor names : {animation names: metadata}}
        out: dict[str, dict[str, AnimationMetadata]] = {}

        # Iter {actor names : JSON names}
        for actor_name, json_name in actor_name_to_json_name_dict.items():
            # Turn JSON names into JSON paths
            existing_json_dynamic_path: str = get_one_target_dict_value(
                json_name,
                self.jsons_repo_pahts_dict,
                "self.jsons_repo_pahts_dict",
            )
            # Turn JSON path into JSON dict (taken from disk)
            json_dict: dict = self.GET_file_from_disk_dynamic_path(existing_json_dynamic_path)
            # Convert JSON dict to dataclass (metadata), populate out
            out[actor_name] = instance_animation_metadata(json_dict)
        # Return {actor names : {animation names: metadata}}
        return out

    def get_sprite_sheet_static_actor_surfs_dict(self, stage_sprite_sheet_name: str) -> dict[str, pg.Surface]:
        """
        | Stage sprite sheet name is key
        | Key for a dict filled with {actor names : surf names}
        |
        | Raises exception if passed stage sprite sheet name is invalid
        |
        | I turn {actor names : surf names} into {actor names : surf} as output
        """

        # {actor names : surf names}
        data: dict[str, str] = get_one_target_dict_value(
            stage_sprite_sheet_name,
            self.sprite_sheet_static_actor_surfs_dict,
            "self.sprite_sheet_static_actor_surfs_dict",
        )

        # Prepare {actor names : Surface}
        out: dict[str, pg.Surface] = {}

        # Iter {actor names : surf names}
        for actor_name, surf_name in data.items():
            # Turn surf names into surf path
            surf_path: str = get_one_target_dict_value(
                surf_name,
                PNGS_PATHS_DICT,
                "PNGS_PATHS_DICT",
            )
            # Turn surf path into surf
            surf: pg.Surface = pg.image.load(surf_path).convert_alpha()
            # Rebind {actor name : surf}
            out[actor_name] = surf

        # Return {actor names : surf}
        return out

    def get_sprite_sheet_parallax_mems_dict(self, stage_sprite_sheet_name: str) -> dict[str, Any]:
        """
        Actors are binded to their stages.

        Pass the stage sprite sheet name to get its actors mem.

        You get a dict, key is actor str name, value is actor mem.

        It is easy to read this way.
        """

        return get_one_target_dict_value(
            stage_sprite_sheet_name,
            self.sprite_sheet_parallax_background_mems_dict,
            "self.sprite_sheet_parallax_background_mems_dict",
        )

    def GET_or_POST_settings_json_from_disk(self) -> None:
        """
        GET prev saved disk settings, then overwrites local settings with disk.

        Or.

        POST default settings to disk. local settings is already default at start.
        """

        # If that file is not in dynamic paths dict, it has not been POST yet, only POST updates dynamic paths dict
        if SETTINGS_FILE_NAME in self.jsons_user_pahts_dict:
            value = self.GET_file_from_disk_dynamic_path(self.jsons_user_pahts_dict[SETTINGS_FILE_NAME])
            self.overwriting_local_settings_dict(value)
        else:
            # POST new first disk settings with local settings (local starts off with defaullt settings)
            self.POST_file_to_disk_dynamic_path(
                join(JSONS_USER_DIR_PATH, SETTINGS_FILE_NAME),
                self.get_local_settings_dict(),
            )

    def GET_file_from_disk_dynamic_path(self, existing_dynamic_path_dict_value: str) -> dict:
        """
        | Makes sure path is in dynamic paths {json names : json paths}.
        | Raises exception on invalid key.
        |
        | Returns JSON dict from disk
        """

        # Collect all dynamic paths dict {json names : json paths}
        all_paths = {
            **self.jsons_user_pahts_dict,
            **self.jsons_repo_pahts_dict,
            **self.jsons_repo_rooms_pahts_dict,
        }
        # Path not found in dynamic paths dict?
        if existing_dynamic_path_dict_value not in all_paths.values():
            # Raise exception
            raise KeyError("Path does not exist")

        # Use path to GET JSON dict from disk
        with open(existing_dynamic_path_dict_value, "r") as file:
            # Return JSON dict
            data = load(file)
            return data

    def PATCH_file_to_disk_dynamic_path(self, existing_dynamic_path_dict_value: str, file_content: Any) -> None:
        """
        POST file to user disk.

        Use the dynamic paths dict path.

        Raises path does not exist exception.
        """

        # Handle not found path 404
        all_paths = {
            **self.jsons_user_pahts_dict,
            **self.jsons_repo_pahts_dict,
            **self.jsons_repo_rooms_pahts_dict,
        }
        if existing_dynamic_path_dict_value not in all_paths.values():
            raise KeyError("Path does not exist")

        # PATCH 200
        with open(
            existing_dynamic_path_dict_value,
            "w",
        ) as file:
            dump(file_content, file, separators=(",", ":"))

    def POST_file_to_disk_dynamic_path(self, new_dynamic_path: str, file_content: Any) -> None:
        """
        POST file to user disk.

        Use new path with join to be added to dynamic paths dict.
        """

        # POST 201
        with open(
            new_dynamic_path,
            "w",
        ) as file:
            dump(file_content, file, separators=(",", ":"))

        # After POST / DELETE, update dynamic path dict
        self._update_dynamic_paths_dict()

    # This does not use the general way to get dict, this way it is easy to know who mutates settings dict
    def overwriting_local_settings_dict(self, new_settings: dict) -> None:
        """
        Overwrite local settings dict, need exact same shape.

        Raises invalid new settings JSON against schema.
        """

        if not validate_json(new_settings, SETTINGS_SCHEMA):
            raise ValueError("Invalid new settings JSON against schema")

        # If all checks pass, overwrite the current settings
        self.local_settings_dict.update(new_settings)

        # Update event handler function binds, in case event key was changed
        self.event_handler.bind_game_local_setting_key_with_input_flag_setter()

    def set_one_local_settings_dict_value(self, key: str, value: Any) -> None:
        """
        Set a value to local settings dict. Need to be same type.

        Raises invalid new settings JSON against schema.
        """

        # Set the new value
        self.local_settings_dict[key] = value

        if not validate_json(self.local_settings_dict, SETTINGS_SCHEMA):
            raise ValueError("Invalid new settings JSON against schema")

        # Update event handler function binds, in case event key was changed
        self.event_handler.bind_game_local_setting_key_with_input_flag_setter()

    def get_one_local_settings_dict_value(self, key: str) -> Any:
        """
        Get a value from local settings dict.

        Raises invalid key.
        """

        # Check if the key exists in the self.local_settings_dict
        if key not in self.local_settings_dict:
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
