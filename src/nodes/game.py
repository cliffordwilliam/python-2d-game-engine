from typing import Any
from typing import Dict
from typing import Type

from constants import NATIVE_H
from constants import NATIVE_W
from constants import pg
from constants import WINDOW_H
from constants import WINDOW_W
from nodes.debug_draw import DebugDraw
from nodes.sound_manager import SoundManager
from scenes.created_by_splash_screen import CreatedBySplashScreen
from typeguard import typechecked


@typechecked
class Game:
    """
    The `Game` class manages various aspects of the game.
    Including settings, inputs, and scene management.
    """

    def __init__(self, initial_scene: str):
        """
        Initializes a new instance of the `Game` class.
        """
        # REMOVE IN BUILD
        self.is_debug: bool = False

        # REMOVE IN BUILD
        self.debug_draw: DebugDraw = DebugDraw()

        self.resolution: int = 4
        self.window_w: int = WINDOW_W * self.resolution
        self.window_h: int = WINDOW_H * self.resolution
        self.window_surf: pg.Surface = pg.display.set_mode(
            (self.window_w, self.window_h)
        )
        self.y_offset: int = ((WINDOW_H - NATIVE_H) // 2) * self.resolution

        self.is_up_pressed: bool = False
        self.is_down_pressed: bool = False
        self.is_left_pressed: bool = False
        self.is_right_pressed: bool = False

        self.is_up_just_pressed: bool = False
        self.is_down_just_pressed: bool = False
        self.is_left_just_pressed: bool = False
        self.is_right_just_pressed: bool = False

        self.is_up_just_released: bool = False
        self.is_down_just_released: bool = False
        self.is_left_just_released: bool = False
        self.is_right_just_released: bool = False

        self.is_lmb_pressed: bool = False
        self.is_rmb_pressed: bool = False
        self.is_mmb_pressed: bool = False

        self.is_lmb_just_pressed: bool = False
        self.is_rmb_just_pressed: bool = False
        self.is_mmb_just_pressed: bool = False

        self.is_lmb_just_released: bool = False
        self.is_rmb_just_released: bool = False
        self.is_mmb_just_released: bool = False

        self.is_enter_pressed: bool = False
        self.is_pause_pressed: bool = False
        self.is_jump_pressed: bool = False
        self.is_attack_pressed: bool = False

        self.is_enter_just_pressed: bool = False
        self.is_pause_just_pressed: bool = False
        self.is_jump_just_pressed: bool = False
        self.is_attack_just_pressed: bool = False

        self.is_enter_just_released: bool = False
        self.is_pause_just_released: bool = False
        self.is_jump_just_released: bool = False
        self.is_attack_just_released: bool = False

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

        self.actors: Dict[str, Type[Any]] = {
            # "fire": Fire,
        }

        self.scenes: Dict[str, Type[Any]] = {
            "CreatedBySplashScreen": CreatedBySplashScreen,
        }

        self.sound_manager: SoundManager = SoundManager()

        self.current_scene: Any = self.scenes[initial_scene](self)

    def set_resolution(self, value: int):
        """
        Sets the resolution of the game window.
        """
        if value != 7:
            self.resolution = value
            self.window_w = WINDOW_W * self.resolution
            self.window_h = WINDOW_H * self.resolution
            self.window_surf = pg.display.set_mode(
                (self.window_w, self.window_h)
            )
            self.y_offset = ((WINDOW_H - NATIVE_H) // 2) * self.resolution

        elif value == 7:
            self.window_surf = pg.display.set_mode(
                (self.window_w, self.window_h), pg.FULLSCREEN
            )
            self.resolution = self.window_surf.get_width() // NATIVE_W
            self.window_w = WINDOW_W * self.resolution
            self.window_h = WINDOW_H * self.resolution
            self.y_offset = ((WINDOW_H - NATIVE_H) // 2) * self.resolution

    def set_scene(self, value: str):
        """
        Sets the current scene of the game.
        """
        self.current_scene = self.scenes[value](self)

    def quit(self):
        """
        Exit the game.
        """
        pg.quit()
        exit()

    def event(self, event: pg.Event):
        """
        Handles events that occur during the game.
        Updates the flag every frame.
        This is called by the main.py.
        """
        if event.type == pg.QUIT:
            pg.quit()
            exit()

        if event.type == pg.KEYDOWN:
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
            if event.key == pg.K_0:
                self.is_debug = not self.is_debug

        # REMOVE IN BUILD
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

    def reset_just_events(self):
        """
        Resets the flags for just-pressed and just-released events.
        Called by main.py.

        Returns:
            None
        """
        self.is_up_just_pressed = False
        self.is_down_just_pressed = False
        self.is_left_just_pressed = False
        self.is_right_just_pressed = False

        self.is_enter_just_pressed = False
        self.is_pause_just_pressed = False
        self.is_jump_just_pressed = False
        self.is_attack_just_pressed = False

        self.is_up_just_released = False
        self.is_down_just_released = False
        self.is_left_just_released = False
        self.is_right_just_released = False

        self.is_enter_just_released = False
        self.is_pause_just_released = False
        self.is_jump_just_released = False
        self.is_attack_just_released = False

        # REMOVE IN BUILD
        self.is_lmb_just_pressed = False
        self.is_rmb_just_pressed = False
        self.is_mmb_just_pressed = False

        self.is_lmb_just_released = False
        self.is_rmb_just_released = False
        self.is_mmb_just_released = False
