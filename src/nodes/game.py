from typing import Any
from typing import Dict
from typing import Type

from constants import NATIVE_HEIGHT
from constants import NATIVE_WIDTH
from constants import pg
from constants import WINDOW_HEIGHT
from constants import WINDOW_WIDTH
from nodes.debug_draw import DebugDraw
from nodes.sound_manager import SoundManager
from scenes.created_by_splash_screen import CreatedBySplashScreen
from scenes.made_with_splash_screen import MadeWithSplashScreen
from scenes.main_menu import MainMenu
from scenes.title_screen import TitleScreen
from typeguard import typechecked


@typechecked
class Game:
    """
    Requires initial scene name.
    The scene names are the keys to my scenes list.

    Properties:
    - Options menu state:
        - Updates option, not current scene.
    - Debug states:
        - Debug draw instance.
        - Frame per frame mode.
    - Window size (resolution scale).
    - All inputs flags.
    - All inputs dict, name to int (keybinding).
    - All actors dict, name to memory.
    - All scenes dict, name to memory.
    - Sound manager instance.
    - Current scene.
    """

    def __init__(self, initial_scene: str):
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
        self.resolution_scale: int = 3
        self.window_width: int = WINDOW_WIDTH * self.resolution_scale
        self.window_height: int = WINDOW_HEIGHT * self.resolution_scale
        self.window_surf: pg.Surface = pg.display.set_mode(
            (self.window_width, self.window_height)
        )
        self.native_y_offset: int = (
            (WINDOW_HEIGHT - NATIVE_HEIGHT) // 2
        ) * self.resolution_scale

        # All game input flags.

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

        # All keys dict, name to int.
        self.key_bindings: Dict[str, int] = {
            "up": pg.K_UP,
            "down": pg.K_DOWN,
            "left": pg.K_LEFT,
            "right": pg.K_RIGHT,
            "enter": pg.K_RETURN,
            "pause": pg.K_ESCAPE,
            "jump": pg.K_c,
            "attack": pg.K_x,
            # REMOVE IN BUILD
            "lmb": 1,
            "mmb": 2,
            "rmb": 3,
        }

        # All actors dict, name to memory
        self.actors: Dict[str, Type[Any]] = {
            # "fire": Fire,
        }

        # All scenes dict, name to memory
        self.scenes: Dict[str, Type[Any]] = {
            "CreatedBySplashScreen": CreatedBySplashScreen,
            "MadeWithSplashScreen": MadeWithSplashScreen,
            "TitleScreen": TitleScreen,
            "MainMenu": MainMenu,
        }

        # The thing that handles sounds.
        self.sound_manager: SoundManager = SoundManager()

        # Keep track of current scene.
        self.current_scene: Any = self.scenes[initial_scene](self)

    def set_is_options_menu_active(self, value: bool) -> None:
        """
        Toggle options screen.
        If options screen is active, current scene is not updated.

        Takes bool parameter.
        """

        self.is_options_menu_active = value

    def set_resolution(self, value: int) -> None:
        """
        Sets the resolution scale of the window.
        Called by options screen.

        Takes int parameter, 1 - 7 only.
        """

        # Not fullscreen. Value updates self.resolution_scale.
        if value != 7:
            # Update self.resolution_scale
            self.resolution_scale = value

            # Update window size, surf and y offset
            self.window_width = WINDOW_WIDTH * self.resolution_scale
            self.window_height = WINDOW_HEIGHT * self.resolution_scale
            self.window_surf = pg.display.set_mode(
                (self.window_width, self.window_height)
            )
            self.native_y_offset = (
                (WINDOW_HEIGHT - NATIVE_HEIGHT) // 2
            ) * self.resolution_scale

        # Full screen. Values does not update self.resolution_scale.
        # self.resolution_scale is updated by how big fullscreen is.
        elif value == 7:
            # Set window surface to be fullscreen size.
            self.window_surf = pg.display.set_mode(
                (self.window_width, self.window_height), pg.FULLSCREEN
            )

            # Update self.resolution_scale with window fullscreen size.
            self.resolution_scale = (
                self.window_surf.get_width() // NATIVE_WIDTH
            )

            # Update window size, surf and y offset
            self.window_width = WINDOW_WIDTH * self.resolution_scale
            self.window_height = WINDOW_HEIGHT * self.resolution_scale
            self.native_y_offset = (
                (WINDOW_HEIGHT - NATIVE_HEIGHT) // 2
            ) * self.resolution_scale

    def set_scene(self, value: str) -> None:
        """
        Sets the current scene with a new instance.
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
            if event.key == self.key_bindings["up"]:
                self.is_up_pressed = True
                self.is_up_just_pressed = True
            if event.key == self.key_bindings["down"]:
                self.is_down_pressed = True
                self.is_down_just_pressed = True
            if event.key == self.key_bindings["left"]:
                self.is_left_pressed = True
                self.is_left_just_pressed = True
            if event.key == self.key_bindings["right"]:
                self.is_right_pressed = True
                self.is_right_just_pressed = True
            if event.key == self.key_bindings["enter"]:
                self.is_enter_pressed = True
                self.is_enter_just_pressed = True
            if event.key == self.key_bindings["pause"]:
                self.is_pause_pressed = True
                self.is_pause_just_pressed = True
            if event.key == self.key_bindings["jump"]:
                self.is_jump_pressed = True
                self.is_jump_just_pressed = True
            if event.key == self.key_bindings["attack"]:
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
            if event.key == self.key_bindings["up"]:
                self.is_up_pressed = False
                self.is_up_just_released = True
            if event.key == self.key_bindings["down"]:
                self.is_down_pressed = False
                self.is_down_just_released = True
            if event.key == self.key_bindings["left"]:
                self.is_left_pressed = False
                self.is_left_just_released = True
            if event.key == self.key_bindings["right"]:
                self.is_right_pressed = False
                self.is_right_just_released = True
            if event.key == self.key_bindings["enter"]:
                self.is_enter_pressed = False
                self.is_enter_just_released = True
            if event.key == self.key_bindings["pause"]:
                self.is_pause_pressed = False
                self.is_pause_just_released = True
            if event.key == self.key_bindings["jump"]:
                self.is_jump_pressed = False
                self.is_jump_just_released = True
            if event.key == self.key_bindings["attack"]:
                self.is_attack_pressed = False
                self.is_attack_just_released = True

        # REMOVE IN BUILD
        # MOUSEBUTTONDOWN.
        # Pressed True.
        # Just pressed True.
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == self.key_bindings["lmb"]:
                self.is_lmb_pressed = True
                self.is_lmb_just_pressed = True
            if event.button == self.key_bindings["mmb"]:
                self.is_mmb_pressed = True
                self.is_mmb_just_pressed = True
            if event.button == self.key_bindings["rmb"]:
                self.is_rmb_pressed = True
                self.is_rmb_just_pressed = True

        # REMOVE IN BUILD
        # MOUSEBUTTONUP.
        # Pressed False.
        # Just released True.
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == self.key_bindings["lmb"]:
                self.is_lmb_pressed = False
                self.is_lmb_just_released = True
            if event.button == self.key_bindings["mmb"]:
                self.is_mmb_pressed = False
                self.is_mmb_just_released = True
            if event.button == self.key_bindings["rmb"]:
                self.is_rmb_pressed = False
                self.is_rmb_just_released = True

    def reset_just_events(self) -> None:
        """
        Resets the flags for just-pressed and just-released events.
        Called by main.py.
        """

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
