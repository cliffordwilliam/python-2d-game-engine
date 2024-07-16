from json import dump
from json import load
from typing import Any
from typing import Type

from constants import DEFAULT_SETTINGS_DICT
from constants import JSONS_PATHS_DICT
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
from scenes.sprite_sheet_json_generator import SpriteSheetJsonGenerator
from scenes.title_screen import TitleScreen
from typeguard import typechecked


@typechecked
class Game:
    def __init__(self, initial_scene: str):
        # Prepare local settings data.
        self.local_settings_dict: dict[str, Any] = {}

        # Update local settings dict.
        self.load_or_create_settings()

        # Flags.
        # Options menu flag, toggle options menu mode.
        self.is_options_menu_active: bool = False
        # REMOVE IN BUILD
        # Toggle drawing debug data.
        self.is_debug: bool = False
        # REMOVE IN BUILD
        # The thing that does the actual debug data drawing.
        self.debug_draw: DebugDraw = DebugDraw()
        # REMOVE IN BUILD
        # Toggle frame per frame debug mode.
        self.is_per_frame: bool = False

        # Window resolution scale, size, y offset.
        # Y offset because native is shorter than window.
        # Default values.
        self.window_width: int = WINDOW_WIDTH * self.local_settings_dict["resolution_scale"]
        self.window_height: int = WINDOW_HEIGHT * self.local_settings_dict["resolution_scale"]
        self.window_surf: Any | pg.Surface = None
        self.set_resolution_index(self.local_settings_dict["resolution_index"])

        # Handles sounds.
        self.sound_manager: SoundManager = SoundManager()
        self.music_manager: MusicManager = MusicManager()

        # Load all oggs.
        # TODO: Load when needed only in each scenes
        for ogg_name, ogg_path in OGGS_PATHS_DICT.items():
            self.sound_manager.load_sound(ogg_name, ogg_path)

        # Handle events
        self.event_handler: EventHandler = EventHandler(self)

        # TODO: key is sprite sheet name and value is mem
        # TODO: do the above for bg classes also
        # All actors dict, name to memory.
        self.actors: dict[str, Type[Any]] = {
            # "fire": Fire,
        }

        # All scenes dict, name to memory.
        self.scenes: dict[str, Type[Any]] = {
            "CreatedBySplashScreen": CreatedBySplashScreen,
            "MadeWithSplashScreen": MadeWithSplashScreen,
            "TitleScreen": TitleScreen,
            "MainMenu": MainMenu,
            "AnimationJsonGenerator": AnimationJsonGenerator,
            "SpriteSheetJsonGenerator": SpriteSheetJsonGenerator,
        }

        # Keeps track of current scene.
        self.current_scene: Any = self.scenes[initial_scene](self)

    def load_or_create_settings(self) -> None:
        """
        Load to local or create and then load.
        """

        # TODO: Deal with different OS. AppData.

        # Got settings file on disk?
        try:
            # Load it.
            with open(JSONS_PATHS_DICT["settings.json"], "r") as settings_json:
                self.local_settings_dict = load(settings_json)
        # No settings file on disk?
        except FileNotFoundError:
            # Create one to disk. Load to local.
            self.local_settings_dict = DEFAULT_SETTINGS_DICT
            with open(JSONS_PATHS_DICT["settings.json"], "w") as settings_json:
                dump(self.local_settings_dict, settings_json)

    def save_settings(self) -> None:
        """
        Dump my local saves to disk.
        """

        with open(JSONS_PATHS_DICT["settings.json"], "w") as settings_json:
            dump(self.local_settings_dict, settings_json)

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

        # Full screen.
        if value == 6:
            self.local_settings_dict["resolution_index"] = value
            # Set window surf to be fullscreen size.
            self.window_surf = pg.display.set_mode(
                (self.window_width, self.window_height),
                pg.FULLSCREEN | pg.SCALED,
            )
            # Update self.local_settings_dict["resolution_scale"]
            self.local_settings_dict["resolution_scale"] = self.window_surf.get_width() // NATIVE_WIDTH
            # Update window size, surf and y offset
            self.window_width = self.window_surf.get_width()
            self.window_height = self.window_surf.get_height()
            return

        # Not fullscreen.
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
