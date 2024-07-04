from json import dump
from json import load
from typing import Any
from typing import Dict
from typing import Type

from constants import DEFAULT_SETTINGS_DICT
from constants import JSONS_PATHS_DICT
from constants import NATIVE_HEIGHT
from constants import NATIVE_WIDTH
from constants import pg
from constants import WINDOW_HEIGHT
from constants import WINDOW_WIDTH
from nodes.debug_draw import DebugDraw
from nodes.music_manager import MusicManager
from nodes.sound_manager import SoundManager
from scenes.created_by_splash_screen import CreatedBySplashScreen
from scenes.made_with_splash_screen import MadeWithSplashScreen
from scenes.main_menu import MainMenu
from scenes.title_screen import TitleScreen
from typeguard import typechecked


@typechecked
class Game:
    """
    Responsibility:
    - save.
    - set_is_options_menu_active.
    - set_resolution.
    - set_scene.
    - quit.
    - event.

    Properties:
    - local_settings_dict.
    - is_options_menu_active.
    - is_debug.
    - debug_draw.
    - is_per_frame.
    - resolution_scale.
    - window_width.
    - window_height.
    - window_surf.
    - native_y_offset.
    - input flags.
    - inputs dict, name to int. KEYBINDS
    - actors dict, name to memory.
    - scenes dict, name to memory.
    - sound_manager.
    - current_scene.
    """

    def __init__(self, initial_scene: str):
        # TODO: Use this instead of hard coding it.
        # print(pg.display.get_desktop_sizes())

        # Prepare local settings data.
        self.local_settings_dict: Dict[str, Any] = {}

        # Got load file on disk?
        try:
            # Load it.
            with open(JSONS_PATHS_DICT["settings.json"], "r") as settings_json:
                self.local_settings_dict = load(settings_json)
        # No load file on disk?
        except FileNotFoundError:
            # Create one to disk.
            self.local_settings_dict = DEFAULT_SETTINGS_DICT
            with open(JSONS_PATHS_DICT["settings.json"], "w") as settings_json:
                dump(self.local_settings_dict, settings_json)

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

        # Default.
        self.window_width: int = (
            WINDOW_WIDTH * self.local_settings_dict["resolution_scale"]
        )
        self.window_height: int = (
            WINDOW_HEIGHT * self.local_settings_dict["resolution_scale"]
        )
        self.window_surf: Any | pg.Surface = None
        self.native_y_offset: int = (
            (WINDOW_HEIGHT - NATIVE_HEIGHT) // 2
        ) * self.local_settings_dict["resolution_scale"]

        # Not fullscreen.
        if self.local_settings_dict["resolution_index"] != 6:
            # Update window size, surf and y offset
            self.window_width = (
                WINDOW_WIDTH * self.local_settings_dict["resolution_scale"]
            )
            self.window_height = (
                WINDOW_HEIGHT * self.local_settings_dict["resolution_scale"]
            )
            self.window_surf = pg.display.set_mode(
                (self.window_width, self.window_height)
            )
            self.native_y_offset = (
                (WINDOW_HEIGHT - NATIVE_HEIGHT) // 2
            ) * self.local_settings_dict["resolution_scale"]

        # Full screen.
        elif self.local_settings_dict["resolution_index"] == 6:
            # Set window surf to be fullscreen size.
            self.window_surf = pg.display.set_mode(
                (self.window_width, self.window_height), pg.FULLSCREEN
            )

            self.local_settings_dict["resolution_scale"] = (
                self.window_surf.get_width() // NATIVE_WIDTH
            )

            # Update window size, surf and y offset
            self.window_width = (
                WINDOW_WIDTH * self.local_settings_dict["resolution_scale"]
            )
            self.window_height = (
                WINDOW_HEIGHT * self.local_settings_dict["resolution_scale"]
            )
            self.native_y_offset = (
                (WINDOW_HEIGHT - NATIVE_HEIGHT) // 2
            ) * self.local_settings_dict["resolution_scale"]

        # All game input flags.
        self.is_any_key_just_pressed: bool = False
        self.this_frame_event: Any = None

        # Directions pressed.
        self.is_up_pressed: bool = False
        self.is_down_pressed: bool = False
        self.is_left_pressed: bool = False
        self.is_right_pressed: bool = False

        # Directions just pressed.
        self.is_up_just_pressed: bool = False
        self.is_down_just_pressed: bool = False
        self.is_left_just_pressed: bool = False
        self.is_right_just_pressed: bool = False

        # Directions just released.
        self.is_up_just_released: bool = False
        self.is_down_just_released: bool = False
        self.is_left_just_released: bool = False
        self.is_right_just_released: bool = False

        # REMOVE IN BUILD
        # Mouse pressed.
        self.is_lmb_pressed: bool = False
        self.is_rmb_pressed: bool = False
        self.is_mmb_pressed: bool = False

        # REMOVE IN BUILD
        # Mouse just pressed.
        self.is_lmb_just_pressed: bool = False
        self.is_rmb_just_pressed: bool = False
        self.is_mmb_just_pressed: bool = False

        # REMOVE IN BUILD
        # Mouse just released.
        self.is_lmb_just_released: bool = False
        self.is_rmb_just_released: bool = False
        self.is_mmb_just_released: bool = False

        # Actions pressed.
        self.is_enter_pressed: bool = False
        self.is_pause_pressed: bool = False
        self.is_jump_pressed: bool = False
        self.is_attack_pressed: bool = False

        # Actions just pressed.
        self.is_enter_just_pressed: bool = False
        self.is_pause_just_pressed: bool = False
        self.is_jump_just_pressed: bool = False
        self.is_attack_just_pressed: bool = False

        # Actions just released.
        self.is_enter_just_released: bool = False
        self.is_pause_just_released: bool = False
        self.is_jump_just_released: bool = False
        self.is_attack_just_released: bool = False

        # All actors dict, name to memory.
        self.actors: Dict[str, Type[Any]] = {
            # "fire": Fire,
        }

        # All scenes dict, name to memory.
        self.scenes: Dict[str, Type[Any]] = {
            "CreatedBySplashScreen": CreatedBySplashScreen,
            "MadeWithSplashScreen": MadeWithSplashScreen,
            "TitleScreen": TitleScreen,
            "MainMenu": MainMenu,
        }

        # Handles sounds.
        self.sound_manager: SoundManager = SoundManager()
        self.music_manager: MusicManager = MusicManager()

        # Keeps track of current scene.
        self.current_scene: Any = self.scenes[initial_scene](self)

    def load_or_create_settings(self) -> None:
        # Got load file on disk?
        try:
            # Load it.
            with open(JSONS_PATHS_DICT["settings.json"], "r") as settings_json:
                self.local_settings_dict = load(settings_json)
        # No load file on disk?
        except FileNotFoundError:
            # Create one to disk.
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
        Toggle options screen.
        If options screen is active, current scene is not updated.
        """

        self.is_options_menu_active = value

    def set_resolution_index(self, value: int) -> None:
        """
        Sets the resolution scale of the window.
        Called by options screen.

        Takes int parameter, 0 - 6 only.
        """

        # Not fullscreen.
        if value != 6:
            # Update self.local_settings_dict["resolution_scale"]
            self.local_settings_dict["resolution_index"] = value
            self.local_settings_dict["resolution_scale"] = value + 1

            # Update window size, surf and y offset
            self.window_width = (
                WINDOW_WIDTH * self.local_settings_dict["resolution_scale"]
            )
            self.window_height = (
                WINDOW_HEIGHT * self.local_settings_dict["resolution_scale"]
            )
            self.window_surf = pg.display.set_mode(
                (self.window_width, self.window_height)
            )
            self.native_y_offset = (
                (WINDOW_HEIGHT - NATIVE_HEIGHT) // 2
            ) * self.local_settings_dict["resolution_scale"]

        # Full screen.
        elif value == 6:
            self.local_settings_dict["resolution_index"] = value
            # Set window surf to be fullscreen size.
            self.window_surf = pg.display.set_mode(
                (self.window_width, self.window_height), pg.FULLSCREEN
            )

            self.local_settings_dict["resolution_scale"] = (
                self.window_surf.get_width() // NATIVE_WIDTH
            )

            # Update window size, surf and y offset
            self.window_width = (
                WINDOW_WIDTH * self.local_settings_dict["resolution_scale"]
            )
            self.window_height = (
                WINDOW_HEIGHT * self.local_settings_dict["resolution_scale"]
            )
            self.native_y_offset = (
                (WINDOW_HEIGHT - NATIVE_HEIGHT) // 2
            ) * self.local_settings_dict["resolution_scale"]

    def set_scene(self, value: str) -> None:
        """
        Sets the current scene with a new scene instance.
        """

        self.current_scene = self.scenes[value](self)

    def quit(self) -> None:
        """
        Exit the game.
        """

        pg.quit()
        exit()

    def event(self, event: pg.Event) -> None:
        """
        This is called by the main.py.
        Updates the input flags every frame.
        """

        # Handle window x button on click.
        if event.type == pg.QUIT:
            pg.quit()
            exit()

        # KEYDOWN.
        # Pressed True.
        # Just pressed True.
        elif event.type == pg.KEYDOWN:
            self.is_any_key_just_pressed = True
            self.this_frame_event = event

            if event.key == self.local_settings_dict["up"]:
                self.is_up_pressed = True
                self.is_up_just_pressed = True
            if event.key == self.local_settings_dict["down"]:
                self.is_down_pressed = True
                self.is_down_just_pressed = True
            if event.key == self.local_settings_dict["left"]:
                self.is_left_pressed = True
                self.is_left_just_pressed = True
            if event.key == self.local_settings_dict["right"]:
                self.is_right_pressed = True
                self.is_right_just_pressed = True
            if event.key == self.local_settings_dict["enter"]:
                self.is_enter_pressed = True
                self.is_enter_just_pressed = True
            if event.key == self.local_settings_dict["pause"]:
                self.is_pause_pressed = True
                self.is_pause_just_pressed = True
            if event.key == self.local_settings_dict["jump"]:
                self.is_jump_pressed = True
                self.is_jump_just_pressed = True
            if event.key == self.local_settings_dict["attack"]:
                self.is_attack_pressed = True
                self.is_attack_just_pressed = True

            # REMOVE IN BUILD
            # Toggle is debug for drawing and per frame.
            if event.key == pg.K_0:
                self.is_debug = not self.is_debug
            if event.key == pg.K_9:
                self.is_per_frame = not self.is_per_frame

        # KEYUP.
        # Pressed False.
        # Just released True.
        elif event.type == pg.KEYUP:
            if event.key == self.local_settings_dict["up"]:
                self.is_up_pressed = False
                self.is_up_just_released = True
            if event.key == self.local_settings_dict["down"]:
                self.is_down_pressed = False
                self.is_down_just_released = True
            if event.key == self.local_settings_dict["left"]:
                self.is_left_pressed = False
                self.is_left_just_released = True
            if event.key == self.local_settings_dict["right"]:
                self.is_right_pressed = False
                self.is_right_just_released = True
            if event.key == self.local_settings_dict["enter"]:
                self.is_enter_pressed = False
                self.is_enter_just_released = True
            if event.key == self.local_settings_dict["pause"]:
                self.is_pause_pressed = False
                self.is_pause_just_released = True
            if event.key == self.local_settings_dict["jump"]:
                self.is_jump_pressed = False
                self.is_jump_just_released = True
            if event.key == self.local_settings_dict["attack"]:
                self.is_attack_pressed = False
                self.is_attack_just_released = True

        # REMOVE IN BUILD
        # MOUSEBUTTONDOWN.
        # Pressed True.
        # Just pressed True.
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == self.local_settings_dict["lmb"]:
                self.is_lmb_pressed = True
                self.is_lmb_just_pressed = True
            if event.button == self.local_settings_dict["mmb"]:
                self.is_mmb_pressed = True
                self.is_mmb_just_pressed = True
            if event.button == self.local_settings_dict["rmb"]:
                self.is_rmb_pressed = True
                self.is_rmb_just_pressed = True

        # REMOVE IN BUILD
        # MOUSEBUTTONUP.
        # Pressed False.
        # Just released True.
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == self.local_settings_dict["lmb"]:
                self.is_lmb_pressed = False
                self.is_lmb_just_released = True
            if event.button == self.local_settings_dict["mmb"]:
                self.is_mmb_pressed = False
                self.is_mmb_just_released = True
            if event.button == self.local_settings_dict["rmb"]:
                self.is_rmb_pressed = False
                self.is_rmb_just_released = True

    def reset_just_events(self) -> None:
        """
        Resets the flags for just-pressed and just-released events.
        Called by main.py.
        """

        self.is_any_key_just_pressed = False
        self.this_frame_event = None

        # Directions.
        # just pressed False.
        # just released False.
        self.is_up_just_pressed = False
        self.is_down_just_pressed = False
        self.is_left_just_pressed = False
        self.is_right_just_pressed = False
        self.is_up_just_released = False
        self.is_down_just_released = False
        self.is_left_just_released = False
        self.is_right_just_released = False

        # Actions.
        # just pressed False.
        # just released False.
        self.is_enter_just_pressed = False
        self.is_pause_just_pressed = False
        self.is_jump_just_pressed = False
        self.is_attack_just_pressed = False
        self.is_enter_just_released = False
        self.is_pause_just_released = False
        self.is_jump_just_released = False
        self.is_attack_just_released = False

        # REMOVE IN BUILD
        # Mouse.
        # just pressed False.
        # just released False.
        self.is_lmb_just_pressed = False
        self.is_rmb_just_pressed = False
        self.is_mmb_just_pressed = False
        self.is_lmb_just_released = False
        self.is_rmb_just_released = False
        self.is_mmb_just_released = False
